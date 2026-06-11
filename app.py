# -*- coding: utf-8 -*-
"""たびログ — 「期待と現実」を記録する旅アプリ（プロトタイプ）"""
import uuid
from datetime import date

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="たびログ | 期待と現実", page_icon="🧭", layout="wide")

# ---------------------------------------------------------------- デザインCSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&family=Noto+Sans+JP:wght@400;500;700&display=swap');

html, body, [class*="st-"] { font-family: 'Noto Sans JP', sans-serif; }
/* Streamlitのマテリアルアイコンはリガチャで描画されるためフォントを戻す */
[data-testid="stIconMaterial"] {
  font-family: 'Material Symbols Rounded' !important;
}

/* ---- ヒーローバナー ---- */
.hero {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #ff9a5a 0%, #ff5e7e 45%, #8f5eff 100%);
  border-radius: 24px; padding: 2.2rem 2rem 2rem;
  margin-bottom: 1.4rem; color: #fff;
  box-shadow: 0 12px 36px rgba(255, 94, 126, .25);
}
.hero::after {
  content: "✈️"; position: absolute; right: 1.2rem; top: 1rem;
  font-size: 4.5rem; opacity: .25; transform: rotate(-12deg);
}
.hero-eyebrow {
  font-size: .78rem; font-weight: 700; letter-spacing: .35em;
  text-transform: uppercase; opacity: .85; margin-bottom: .3rem;
}
.hero-title {
  font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900;
  font-size: 2.6rem; line-height: 1.15; letter-spacing: .06em;
  text-shadow: 0 2px 10px rgba(0,0,0,.15);
}
.hero-sub { margin-top: .5rem; font-size: .95rem; opacity: .92; font-weight: 500; }

/* ---- ページヘッダー（サブ画面用） ---- */
.page-head { display: flex; align-items: center; gap: .9rem; margin: .2rem 0 .3rem; }
.page-head .ico {
  width: 56px; height: 56px; flex: none; display: flex; align-items: center; justify-content: center;
  font-size: 1.7rem; border-radius: 18px;
  background: linear-gradient(135deg, #ff9a5a, #ff5e7e 60%, #8f5eff);
  box-shadow: 0 8px 20px rgba(255, 94, 126, .3);
}
.page-head .t {
  font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900;
  font-size: 1.7rem; letter-spacing: .04em; line-height: 1.2;
}
.page-head .s { font-size: .85rem; opacity: .65; margin-top: .15rem; }

/* ---- 統計カード ---- */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin-bottom: 1.2rem; }
.stat {
  background: rgba(150, 160, 200, .08);
  border: 1px solid rgba(150, 160, 200, .18);
  border-radius: 18px; padding: 1rem 1.1rem;
}
.stat .ico { font-size: 1.3rem; }
.stat .val {
  font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.9rem; line-height: 1.2;
  background: linear-gradient(135deg, #ffb46a, #ff5e7e, #a07bff);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.stat .lab { font-size: .78rem; opacity: .65; font-weight: 500; }

/* ---- バッジ・カード見出し ---- */
.chip {
  display: inline-block; font-size: .72rem; font-weight: 700;
  padding: .22em .85em; border-radius: 999px; vertical-align: middle;
}
.chip-done { background: rgba(72, 187, 120, .18); color: #68d391; border: 1px solid rgba(72,187,120,.35); }
.chip-plan { background: rgba(99, 179, 237, .15); color: #63b3ed; border: 1px solid rgba(99,179,237,.35); }
.trip-title {
  font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900;
  font-size: 1.45rem; letter-spacing: .03em; line-height: 1.3; margin: 0;
}
.trip-meta { font-size: .82rem; opacity: .6; margin-top: .1rem; }
.trip-stars { text-align: right; font-size: 1.5rem; color: #f6ad55; letter-spacing: .1em; white-space: nowrap; }

/* ---- サイドバー ---- */
.side-logo {
  font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.5rem;
  letter-spacing: .08em;
  background: linear-gradient(135deg, #ffb46a, #ff5e7e, #a07bff);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.side-cap { font-size: .75rem; opacity: .6; margin-bottom: .6rem; }

/* ---- モバイル ---- */
@media (max-width: 640px) {
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    flex: 1 1 100%; width: 100%; min-width: 100%;
  }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .hero { padding: 1.6rem 1.3rem; border-radius: 20px; }
  .hero-title { font-size: 1.9rem; }
  .hero::after { font-size: 3rem; }
  [data-testid="stMainBlockContainer"] { padding: 2.5rem 1rem 3rem; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- 国データ
# 日本語名 → world.geo.json の英語名（足跡の色付けに使用）
COUNTRIES = {
    "日本": "Japan", "韓国": "South Korea", "中国": "China", "台湾": "Taiwan",
    "タイ": "Thailand", "ベトナム": "Vietnam", "インドネシア": "Indonesia",
    "シンガポール": "Singapore", "マレーシア": "Malaysia", "インド": "India",
    "フランス": "France", "イタリア": "Italy", "スペイン": "Spain",
    "ドイツ": "Germany", "イギリス": "United Kingdom", "ポルトガル": "Portugal",
    "ギリシャ": "Greece", "オランダ": "Netherlands", "スイス": "Switzerland",
    "チェコ": "Czech Republic", "オーストリア": "Austria", "トルコ": "Turkey",
    "アメリカ": "United States of America", "カナダ": "Canada", "メキシコ": "Mexico",
    "ブラジル": "Brazil", "ペルー": "Peru", "アルゼンチン": "Argentina",
    "オーストラリア": "Australia", "ニュージーランド": "New Zealand",
    "エジプト": "Egypt", "モロッコ": "Morocco", "ケニア": "Kenya",
    "アイスランド": "Iceland", "フィンランド": "Finland", "ノルウェー": "Norway",
}

GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"


@st.cache_data(show_spinner=False)
def load_world_geojson():
    try:
        return requests.get(GEOJSON_URL, timeout=10).json()
    except Exception:
        return None


# ---------------------------------------------------------------- 初期データ
def _sample_trips():
    return [
        {
            "id": str(uuid.uuid4()),
            "place": "エッフェル塔",
            "country": "フランス",
            "city": "パリ",
            "lat": 48.8584, "lon": 2.2945,
            "visit_date": "2025-10-12",
            "expectation": "映画みたいなロマンチックな夜景。シャンパン片手に最高の写真が撮れるはず！",
            "reality": "夜景は本当に綺麗だった。ただし行列は90分、スリ注意の放送が常に流れていて気が抜けない。芝生は立入禁止だった。それでも点灯の瞬間は鳥肌もの。",
            "rating": 4,
            "photos": [],
            "status": "visited",
        },
        {
            "id": str(uuid.uuid4()),
            "place": "カオサン通り",
            "country": "タイ",
            "city": "バンコク",
            "lat": 13.7590, "lon": 100.4977,
            "visit_date": "2026-01-05",
            "expectation": "バックパッカーの聖地で安くて美味い屋台メシ三昧。世界中の旅人と仲良くなる。",
            "reality": "想像の3倍うるさくて3倍楽しい。パッタイは60バーツで絶品。ただし観光地化が進んでいて『聖地』感は薄め。虫の素揚げは話のネタに一口で十分。",
            "rating": 5,
            "photos": [],
            "status": "visited",
        },
        {
            "id": str(uuid.uuid4()),
            "place": "マチュピチュ",
            "country": "ペルー",
            "city": "クスコ",
            "lat": -13.1631, "lon": -72.5450,
            "visit_date": "2026-09-20",
            "expectation": "雲海に浮かぶ天空都市を朝イチで独り占めしたい。高山病が少し心配。",
            "reality": "",
            "rating": 0,
            "photos": [],
            "status": "planned",
        },
    ]


if "trips" not in st.session_state:
    st.session_state.trips = _sample_trips()

# ---------------------------------------------------------------- 共通部品
STAR = lambda r: "★" * r + "☆" * (5 - r) if r else "—"


def page_header(icon, title, sub=""):
    st.markdown(f"""
    <div class="page-head">
      <div class="ico">{icon}</div>
      <div><div class="t">{title}</div><div class="s">{sub}</div></div>
    </div>""", unsafe_allow_html=True)


def popup_html(t):
    reality = t["reality"] or "（まだ記録なし）"
    rating = STAR(t["rating"])
    return f"""
    <div style="font-family:sans-serif; width:260px;">
      <h4 style="margin:0 0 4px;">{'✅' if t['status']=='visited' else '🗓️'} {t['place']}</h4>
      <p style="margin:0 0 6px; color:#888; font-size:12px;">{t['country']}・{t['city']}｜{t['visit_date']}</p>
      <p style="margin:0; font-size:12px;"><b style="color:#2b6cb0;">🌈 期待</b><br>{t['expectation']}</p>
      <p style="margin:6px 0 0; font-size:12px;"><b style="color:#c05621;">📷 現実</b><br>{reality}</p>
      <p style="margin:6px 0 0; font-size:13px;">総合評価: <span style="color:#d69e2e;">{rating}</span></p>
    </div>"""


def build_map(trips, height=520):
    m = folium.Map(location=[25, 20], zoom_start=2, tiles="CartoDB positron")

    # 足跡：訪問済みの国を塗る
    visited_countries = {COUNTRIES.get(t["country"]) for t in trips if t["status"] == "visited"}
    visited_countries.discard(None)
    geo = load_world_geojson()
    if geo and visited_countries:
        feats = [f for f in geo["features"] if f["properties"]["name"] in visited_countries]
        folium.GeoJson(
            {"type": "FeatureCollection", "features": feats},
            style_function=lambda f: {
                "fillColor": "#f6ad55", "color": "#dd6b20",
                "weight": 1, "fillOpacity": 0.35,
            },
        ).add_to(m)

    for t in trips:
        visited = t["status"] == "visited"
        folium.Marker(
            [t["lat"], t["lon"]],
            tooltip=f"{t['place']}（{'訪問済み' if visited else '訪問予定'}）",
            popup=folium.Popup(popup_html(t), max_width=300),
            icon=folium.Icon(color="orange" if visited else "blue",
                             icon="camera" if visited else "calendar", prefix="fa"),
        ).add_to(m)
    return st_folium(m, height=height, use_container_width=True,
                     returned_objects=[], key="home_map")


# ---------------------------------------------------------------- 画面
st.sidebar.markdown('<div class="side-logo">🧭 たびログ</div>'
                    '<div class="side-cap">「期待と現実」を記録する旅アプリ</div>',
                    unsafe_allow_html=True)
page = st.sidebar.radio("メニュー", ["🏠 ホーム", "➕ 旅を登録（事前）", "✍️ 現実を追記（事後）", "📚 旅の一覧"],
                        label_visibility="collapsed")
trips = st.session_state.trips

# ---------- ホーム ----------
if page == "🏠 ホーム":
    st.markdown("""
    <div class="hero">
      <div class="hero-eyebrow">Expectation &amp; Reality</div>
      <div class="hero-title">たびログ</div>
      <div class="hero-sub">キラキラだけじゃない、リアルな旅の記録。<br>
      🟠 訪問済みの足跡　🔵 これからの旅　— ピンをタップすると「期待と現実」が見られます。</div>
    </div>""", unsafe_allow_html=True)

    visited = [t for t in trips if t["status"] == "visited"]
    planned = [t for t in trips if t["status"] == "planned"]
    stats = [
        ("🌍", f"{len({t['country'] for t in visited})}<small> か国</small>", "訪問した国"),
        ("🏙️", f"{len({(t['country'], t['city']) for t in visited})}<small> 都市</small>", "訪問した都市"),
        ("📸", f"{len(visited)}<small> スポット</small>", "行った場所"),
        ("🗓️", f"{len(planned)}<small> 件</small>", "計画中の旅"),
    ]
    st.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><div class="ico">{i}</div><div class="val">{v}</div><div class="lab">{l}</div></div>'
        for i, v, l in stats) + '</div>', unsafe_allow_html=True)

    build_map(trips)

# ---------- 追加 ----------
elif page == "➕ 旅を登録（事前）":
    page_header("🛫", "新しい旅を登録", "出発前に「期待していること」を書き残しましょう。帰ってきたら現実と見比べられます。")

    map_col, form_col = st.columns([1.2, 1])
    with map_col:
        st.markdown("**📍 地図をクリックして場所を選択**")
        pick = folium.Map(location=[25, 20], zoom_start=2, tiles="CartoDB positron")
        if "pick_latlon" in st.session_state:
            folium.Marker(st.session_state.pick_latlon, icon=folium.Icon(color="blue")).add_to(pick)
        out = st_folium(pick, height=420, use_container_width=True, key="pick_map")
        if out and out.get("last_clicked"):
            ll = (out["last_clicked"]["lat"], out["last_clicked"]["lng"])
            if st.session_state.get("pick_latlon") != ll:
                st.session_state.pick_latlon = ll
                st.rerun()

    with form_col:
        latlon = st.session_state.get("pick_latlon")
        if latlon:
            st.success(f"選択中の座標: {latlon[0]:.4f}, {latlon[1]:.4f}")
        else:
            st.info("地図をクリックするとピンの位置が決まります")
        with st.form("add_trip"):
            place = st.text_input("場所名 *", placeholder="例：サグラダ・ファミリア")
            country = st.selectbox("国 *", list(COUNTRIES.keys()), index=None, placeholder="国を選択")
            city = st.text_input("都市 *", placeholder="例：バルセロナ")
            visit_date = st.date_input("訪問予定日", value=date.today())
            expectation = st.text_area("🌈 期待していること *", height=120,
                                       placeholder="どんな体験を期待していますか？正直に書いておくと後で面白いです。")
            if st.form_submit_button("この旅を登録する", type="primary", use_container_width=True):
                if not (place and country and city and expectation and latlon):
                    st.error("未入力の項目があります（地図上の場所選択も必要です）")
                else:
                    st.session_state.trips.append({
                        "id": str(uuid.uuid4()), "place": place, "country": country,
                        "city": city, "lat": latlon[0], "lon": latlon[1],
                        "visit_date": str(visit_date), "expectation": expectation,
                        "reality": "", "rating": 0, "photos": [], "status": "planned",
                    })
                    del st.session_state.pick_latlon
                    st.success(f"「{place}」を登録しました！良い旅を 🛫")

# ---------- 更新 ----------
elif page == "✍️ 現実を追記（事後）":
    page_header("🛬", "帰国後の「現実」を追記", "良かったことも、ガッカリしたことも、正直に。")
    planned = [t for t in trips if t["status"] == "planned"]
    if not planned:
        st.info("追記できる「計画中の旅」がありません。まずは ➕ から旅を登録してください。")
    else:
        target = st.selectbox("どの旅に追記しますか？", planned,
                              format_func=lambda t: f"{t['place']}（{t['country']}・{t['city']}｜{t['visit_date']}）")
        st.markdown(f"> 🌈 **あの時の期待**：{target['expectation']}")
        with st.form("update_trip"):
            reality = st.text_area("📷 実際どうだった？ *", height=140,
                                   placeholder="良かったことも、ガッカリしたことも、正直に。")
            rating = st.slider("総合評価", 1, 5, 3, format="%d ★")
            photos = st.file_uploader("写真をアップロード", type=["png", "jpg", "jpeg", "webp"],
                                      accept_multiple_files=True)
            if st.form_submit_button("現実を記録する", type="primary", use_container_width=True):
                if not reality:
                    st.error("「実際どうだったか」を入力してください")
                else:
                    target["reality"] = reality
                    target["rating"] = rating
                    target["photos"] = [p.getvalue() for p in photos] if photos else []
                    target["status"] = "visited"
                    st.success(f"「{target['place']}」の現実を記録しました。おかえりなさい 🏠")
                    st.balloons()

# ---------- 一覧 ----------
elif page == "📚 旅の一覧":
    page_header("📚", "旅の一覧", "期待 🌈 → 現実 📷 をならべて振り返る")
    flt = st.radio("表示", ["すべて", "訪問済み", "計画中"], horizontal=True)
    shown = [t for t in trips
             if flt == "すべて"
             or (flt == "訪問済み" and t["status"] == "visited")
             or (flt == "計画中" and t["status"] == "planned")]
    if not shown:
        st.info("該当する旅がありません。")
    for t in sorted(shown, key=lambda x: x["visit_date"], reverse=True):
        with st.container(border=True):
            head, stars = st.columns([3, 1])
            chip = ('<span class="chip chip-done">✅ 訪問済み</span>' if t["status"] == "visited"
                    else '<span class="chip chip-plan">🗓️ 計画中</span>')
            head.markdown(
                f'<p class="trip-title">{t["place"]}</p>'
                f'<div class="trip-meta">📍 {t["country"]}・{t["city"]}　🗓 {t["visit_date"]}　{chip}</div>',
                unsafe_allow_html=True)
            stars.markdown(f'<div class="trip-stars">{STAR(t["rating"])}</div>', unsafe_allow_html=True)
            exp_col, real_col = st.columns(2)
            with exp_col:
                st.markdown("**🌈 期待**")
                st.info(t["expectation"])
            with real_col:
                st.markdown("**📷 現実**")
                if t["reality"]:
                    st.warning(t["reality"])
                else:
                    st.caption("まだ記録がありません（帰国後に ✍️ から追記）")
            if t["photos"]:
                pcols = st.columns(min(4, len(t["photos"])))
                for i, ph in enumerate(t["photos"]):
                    pcols[i % len(pcols)].image(ph, use_container_width=True)
