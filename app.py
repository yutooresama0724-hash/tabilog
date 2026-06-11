# -*- coding: utf-8 -*-
"""たびログ / TabiLog — 「期待と現実」を記録する旅アプリ"""
import base64
import hashlib
import json
import os
import uuid
from datetime import date

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="たびログ | TabiLog", page_icon="🧭",
                   layout="centered", initial_sidebar_state="collapsed")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# ---------------------------------------------------------------- 多言語
I18N = {
    "ja": {
        "tagline": "「期待と現実」を記録する旅アプリ",
        "tab_login": "ログイン", "tab_register": "新規登録",
        "user_id": "ユーザーID", "password": "パスワード",
        "login_btn": "ログイン", "login_err": "ユーザーIDまたはパスワードが違います",
        "display_name": "表示名", "display_name_ph": "例：ゆうと",
        "uid_label": "ユーザーID（半角英数字）", "uid_ph": "例：yuto_trip",
        "pw_label": "パスワード（6文字以上）", "create_btn": "アカウントを作成",
        "err_fill_all": "すべての項目を入力してください",
        "err_uid_format": "ユーザーIDは半角英数字とアンダースコアのみ使えます",
        "err_pw_len": "パスワードは6文字以上にしてください",
        "err_uid_taken": "このユーザーIDは既に使われています",
        "language": "言語 / Language",
        "nav_map": "マップ", "nav_feed": "フィード", "nav_add": "投稿",
        "nav_update": "追記", "nav_profile": "プロフィール",
        "hero_title": "たびログ", "hero_sub": "キラキラだけじゃない、リアルな旅の記録。<br>🟠 訪問済みの足跡　🔵 これからの旅 — ピンをタップすると「期待と現実」。",
        "flt_my_visited": "🟠 行った", "flt_my_planned": "🔵 これから",
        "flt_fr_visited": "💜 友達が行った", "flt_fr_planned": "🩷 友達のこれから",
        "stat_countries": "訪問した国", "stat_cities": "訪問した都市",
        "stat_spots": "行った場所", "stat_planned": "計画中の旅",
        "unit_countries": " か国", "unit_cities": " 都市", "unit_spots": " スポット", "unit_plans": " 件",
        "feed_title": "フィード", "feed_sub": "期待 🌈 → 現実 📷 をならべて振り返る",
        "scope_friends": "🏠 フレンド", "scope_discover": "🌐 みんなの公開投稿",
        "flt_all": "すべて", "flt_visited": "訪問済み", "flt_planned": "計画中",
        "feed_empty": "まだ表示できる投稿がありません。➕ から最初の旅を登録しましょう！",
        "expectation": "🌈 期待", "reality": "📷 現実",
        "no_reality": "まだ記録がありません（帰国後に 🛬 から追記）",
        "chip_visited": "✅ 訪問済み", "chip_planned": "🗓️ 計画中",
        "vis_public_chip": "🌐 全体公開", "vis_friends_chip": "👥 友達のみ",
        "add_title": "新しい旅を登録", "add_sub": "出発前に「期待していること」を書き残しましょう。",
        "pick_map": "📍 地図をクリックして場所を選択",
        "picked": "選択中の座標", "pick_info": "地図をクリックするとピンの位置が決まります",
        "place": "場所名 *", "place_ph": "例：サグラダ・ファミリア",
        "country": "国 *", "country_ph": "国を選択", "city": "都市 *", "city_ph": "例：バルセロナ",
        "visit_date": "訪問予定日", "expect_label": "🌈 期待していること *",
        "expect_ph": "どんな体験を期待していますか？正直に書いておくと後で面白いです。",
        "visibility": "公開範囲", "vis_default": "アカウント設定に従う",
        "vis_public": "🌐 全体公開", "vis_friends": "👥 友達のみ",
        "vis_post_public": "🌐 この投稿のみ全体公開",
        "submit_trip": "この旅を登録する",
        "err_missing": "未入力の項目があります（地図上の場所選択も必要です）",
        "added": "を登録しました！良い旅を 🛫",
        "upd_title": "帰国後の「現実」を追記", "upd_sub": "良かったことも、ガッカリしたことも、正直に。",
        "upd_none": "追記できる「計画中の旅」がありません。まずは ➕ から旅を登録してください。",
        "upd_which": "どの旅に追記しますか？", "upd_past": "あの時の期待",
        "upd_reality": "📷 実際どうだった？ *", "upd_reality_ph": "良かったことも、ガッカリしたことも、正直に。",
        "rating": "総合評価", "photos": "写真をアップロード",
        "save_reality": "現実を記録する", "err_reality": "「実際どうだったか」を入力してください",
        "updated": "の現実を記録しました。おかえりなさい 🏠",
        "tab_posts": "📊 記録", "tab_friends": "👥 フレンド", "tab_settings": "⚙️ 設定",
        "stat_posts": "投稿", "stat_c": "国", "stat_ci": "都市", "stat_p": "計画中",
        "memories": "🖼️ 思い出グリッド",
        "no_photos": "写真はまだありません。🛬 追記から写真をアップロードすると、ここに並びます。",
        "logout": "ログアウト",
        "req_in": "📨 受信したフレンド申請", "accept": "承認", "decline": "拒否",
        "add_friend": "フレンドを追加", "friend_id_ph": "相手のユーザーID",
        "send_req": "申請を送る", "req_sent": "フレンド申請を送りました",
        "err_self": "自分自身には送れません", "err_already": "すでにフレンドです",
        "err_pending": "申請済みです。相手の承認を待ちましょう", "err_nouser": "そのユーザーIDは見つかりません",
        "friends_list": "フレンド一覧", "remove": "解除", "no_friends": "まだフレンドがいません。ユーザーIDで検索して申請しましょう。",
        "avatar": "プロフィールアイコン", "avatar_upload": "画像をアップロード（正方形がおすすめ）",
        "default_vis": "投稿のデフォルト公開範囲", "save_settings": "設定を保存", "saved": "設定を保存しました",
        "by": "さん",
    },
    "en": {
        "tagline": "A travel journal for expectations & reality",
        "tab_login": "Log in", "tab_register": "Sign up",
        "user_id": "User ID", "password": "Password",
        "login_btn": "Log in", "login_err": "Wrong user ID or password",
        "display_name": "Display name", "display_name_ph": "e.g. Yuto",
        "uid_label": "User ID (alphanumeric)", "uid_ph": "e.g. yuto_trip",
        "pw_label": "Password (6+ characters)", "create_btn": "Create account",
        "err_fill_all": "Please fill in all fields",
        "err_uid_format": "User ID may contain only letters, numbers and underscores",
        "err_pw_len": "Password must be at least 6 characters",
        "err_uid_taken": "This user ID is already taken",
        "language": "言語 / Language",
        "nav_map": "Map", "nav_feed": "Feed", "nav_add": "Post",
        "nav_update": "Reality", "nav_profile": "Profile",
        "hero_title": "TabiLog", "hero_sub": "Real travel memories, not just the highlight reel.<br>🟠 Footprints of visited places 🔵 Upcoming trips — tap a pin to see expectation vs reality.",
        "flt_my_visited": "🟠 My visited", "flt_my_planned": "🔵 My upcoming",
        "flt_fr_visited": "💜 Friends visited", "flt_fr_planned": "🩷 Friends upcoming",
        "stat_countries": "Countries visited", "stat_cities": "Cities visited",
        "stat_spots": "Places visited", "stat_planned": "Planned trips",
        "unit_countries": "", "unit_cities": "", "unit_spots": "", "unit_plans": "",
        "feed_title": "Feed", "feed_sub": "Expectation 🌈 → Reality 📷 side by side",
        "scope_friends": "🏠 Friends", "scope_discover": "🌐 Discover (public)",
        "flt_all": "All", "flt_visited": "Visited", "flt_planned": "Planned",
        "feed_empty": "Nothing to show yet. Add your first trip from ➕!",
        "expectation": "🌈 Expectation", "reality": "📷 Reality",
        "no_reality": "No record yet (add it from 🛬 after the trip)",
        "chip_visited": "✅ Visited", "chip_planned": "🗓️ Planned",
        "vis_public_chip": "🌐 Public", "vis_friends_chip": "👥 Friends only",
        "add_title": "Add a new trip", "add_sub": "Write down your expectations before you go.",
        "pick_map": "📍 Click the map to choose a location",
        "picked": "Selected coordinates", "pick_info": "Click the map to place the pin",
        "place": "Place *", "place_ph": "e.g. Sagrada Família",
        "country": "Country *", "country_ph": "Select a country", "city": "City *", "city_ph": "e.g. Barcelona",
        "visit_date": "Planned date", "expect_label": "🌈 What do you expect? *",
        "expect_ph": "What experience are you hoping for? Be honest — it's fun to look back on.",
        "visibility": "Visibility", "vis_default": "Use account default",
        "vis_public": "🌐 Public", "vis_friends": "👥 Friends only",
        "vis_post_public": "🌐 Make only this post public",
        "submit_trip": "Save this trip",
        "err_missing": "Some fields are missing (including the map location)",
        "added": " saved! Have a great trip 🛫",
        "upd_title": "Add the reality afterwards", "upd_sub": "The good and the disappointing — be honest.",
        "upd_none": "No planned trips to update. Add one from ➕ first.",
        "upd_which": "Which trip do you want to update?", "upd_past": "Your expectation back then",
        "upd_reality": "📷 How was it really? *", "upd_reality_ph": "The good and the disappointing — be honest.",
        "rating": "Overall rating", "photos": "Upload photos",
        "save_reality": "Save the reality", "err_reality": "Please write how it actually was",
        "updated": " updated. Welcome home 🏠",
        "tab_posts": "📊 Posts", "tab_friends": "👥 Friends", "tab_settings": "⚙️ Settings",
        "stat_posts": "Posts", "stat_c": "Countries", "stat_ci": "Cities", "stat_p": "Planned",
        "memories": "🖼️ Memory grid",
        "no_photos": "No photos yet. Upload some from 🛬 and they'll appear here.",
        "logout": "Log out",
        "req_in": "📨 Friend requests", "accept": "Accept", "decline": "Decline",
        "add_friend": "Add a friend", "friend_id_ph": "Their user ID",
        "send_req": "Send request", "req_sent": "Friend request sent",
        "err_self": "You can't add yourself", "err_already": "Already friends",
        "err_pending": "Request already sent. Waiting for approval", "err_nouser": "No user with that ID",
        "friends_list": "Friends", "remove": "Remove", "no_friends": "No friends yet. Search by user ID and send a request.",
        "avatar": "Profile icon", "avatar_upload": "Upload an image (square works best)",
        "default_vis": "Default post visibility", "save_settings": "Save settings", "saved": "Settings saved",
        "by": "",
    },
}

if "lang" not in st.session_state:
    st.session_state.lang = "ja"


def tr(key):
    return I18N[st.session_state.lang].get(key, key)


# ---------------------------------------------------------------- デザインCSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&family=Noto+Sans+JP:wght@400;500;700&display=swap');

html, body, [class*="st-"] { font-family: 'Noto Sans JP', sans-serif; }
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 640px; padding: 2.2rem 1rem 7rem; }

.logo-grad {
  font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900;
  background: linear-gradient(135deg, #ffb46a, #ff5e7e, #a07bff);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.hero {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #ff9a5a 0%, #ff5e7e 45%, #8f5eff 100%);
  border-radius: 24px; padding: 1.7rem 1.5rem 1.5rem; margin-bottom: 1.2rem; color: #fff;
  box-shadow: 0 12px 36px rgba(255, 94, 126, .25);
}
.hero::after { content: "✈️"; position: absolute; right: 1rem; top: .8rem; font-size: 3.4rem; opacity: .25; transform: rotate(-12deg); }
.hero-eyebrow { font-size: .72rem; font-weight: 700; letter-spacing: .35em; text-transform: uppercase; opacity: .85; }
.hero-title { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 2rem; line-height: 1.15; letter-spacing: .06em; text-shadow: 0 2px 10px rgba(0,0,0,.15); }
.hero-sub { margin-top: .4rem; font-size: .85rem; opacity: .92; font-weight: 500; }

.page-head { display: flex; align-items: center; gap: .9rem; margin: .2rem 0 .5rem; }
.page-head .ico { width: 52px; height: 52px; flex: none; display: flex; align-items: center; justify-content: center; font-size: 1.55rem; border-radius: 17px; background: linear-gradient(135deg, #ff9a5a, #ff5e7e 60%, #8f5eff); box-shadow: 0 8px 20px rgba(255, 94, 126, .3); }
.page-head .t { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.5rem; letter-spacing: .04em; line-height: 1.2; }
.page-head .s { font-size: .82rem; opacity: .65; margin-top: .15rem; }

.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .7rem; margin-bottom: 1.1rem; }
.stat { background: rgba(150, 160, 200, .08); border: 1px solid rgba(150, 160, 200, .18); border-radius: 18px; padding: .85rem .9rem; }
.stat .ico { font-size: 1.15rem; }
.stat .val { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.55rem; line-height: 1.25; background: linear-gradient(135deg, #ffb46a, #ff5e7e, #a07bff); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.stat .lab { font-size: .72rem; opacity: .65; font-weight: 500; }

.chip { display: inline-block; font-size: .72rem; font-weight: 700; padding: .22em .85em; border-radius: 999px; vertical-align: middle; margin-right: .25em; }
.chip-done { background: rgba(72, 187, 120, .18); color: #68d391; border: 1px solid rgba(72,187,120,.35); }
.chip-plan { background: rgba(99, 179, 237, .15); color: #63b3ed; border: 1px solid rgba(99,179,237,.35); }
.chip-pub  { background: rgba(246, 173, 85, .15); color: #f6ad55; border: 1px solid rgba(246,173,85,.35); }
.chip-frd  { background: rgba(160, 123, 255, .15); color: #b794f4; border: 1px solid rgba(160,123,255,.35); }
.trip-title { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.35rem; letter-spacing: .03em; line-height: 1.3; margin: 0; }
.trip-meta { font-size: .8rem; opacity: .75; margin-top: .15rem; }
.trip-stars { text-align: right; font-size: 1.35rem; color: #f6ad55; letter-spacing: .1em; white-space: nowrap; }

.av { border-radius: 50%; flex: none; display: flex; align-items: center; justify-content: center; font-weight: 900; color: #fff; background: linear-gradient(135deg, #ff9a5a, #ff5e7e, #8f5eff); overflow: hidden; }
.av img { width: 100%; height: 100%; object-fit: cover; }
.feed-user { display: flex; align-items: center; gap: .55rem; margin-bottom: .4rem; }
.feed-user .av { width: 34px; height: 34px; font-size: .95rem; }
.feed-user .un { font-weight: 700; font-size: .88rem; }
.feed-user .loc { font-size: .72rem; opacity: .6; }

.prof { display: flex; align-items: center; gap: 1.2rem; margin: .5rem 0 1rem; }
.prof .av { width: 84px; height: 84px; font-family: 'Zen Maru Gothic', sans-serif; font-size: 2.1rem; box-shadow: 0 10px 26px rgba(255, 94, 126, .35); }
.prof .nm { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.5rem; }
.prof .id { font-size: .82rem; opacity: .6; }
.friend-row { display: flex; align-items: center; gap: .6rem; }
.friend-row .av { width: 40px; height: 40px; font-size: 1.05rem; }

.st-key-bottomnav { position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: min(100vw, 640px); z-index: 999; background: rgba(14, 17, 23, .94); backdrop-filter: blur(14px); border: 1px solid rgba(150, 160, 200, .18); border-bottom: none; border-radius: 20px 20px 0 0; padding: .3rem .5rem calc(.4rem + env(safe-area-inset-bottom)); }
.st-key-bottomnav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .3rem; }
.st-key-bottomnav [data-testid="stColumn"] { flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }
.st-key-bottomnav button { background: transparent !important; border: none !important; padding: .25rem 0 !important; min-height: 2.6rem; }
.st-key-bottomnav button p { font-size: 1.45rem !important; line-height: 1; }
.st-key-bottomnav button[kind="primary"] { background: linear-gradient(135deg, rgba(255,154,90,.22), rgba(143,94,255,.22)) !important; border-radius: 14px !important; }

.login-logo { text-align: center; margin: 1.2rem 0 .2rem; }
.login-logo .big { font-size: 2.8rem; letter-spacing: .1em; }
.login-logo .cap { font-size: .85rem; opacity: .65; margin-top: .2rem; }

@media (max-width: 640px) {
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100%; width: 100%; min-width: 100%; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .hero-title { font-size: 1.7rem; }
  [data-testid="stMainBlockContainer"] { padding: 1.5rem .9rem 7rem; }
  /* フレンド行・フィルタなど小さい行は横並びを維持 */
  .st-key-bottomnav [data-testid="stColumn"],
  [class*="st-key-frow_"] [data-testid="stColumn"] { flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- 国データ
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


def country_label(c):
    return c if st.session_state.lang == "ja" else COUNTRIES.get(c, c)


@st.cache_data(show_spinner=False)
def load_world_geojson():
    try:
        return requests.get(GEOJSON_URL, timeout=10).json()
    except Exception:
        return None


# ---------------------------------------------------------------- ユーザー管理
USER_DEFAULTS = {"avatar": None, "friends": [], "requests_in": [],
                 "default_visibility": "friends", "lang": "ja"}


def load_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, encoding="utf-8") as f:
            users = json.load(f)
    for u in users.values():
        for k, v in USER_DEFAULTS.items():
            u.setdefault(k, list(v) if isinstance(v, list) else v)
    return users


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def hash_pw(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def avatar_html(user, name):
    if user and user.get("avatar"):
        return f'<img src="data:image/png;base64,{user["avatar"]}">'
    return (name or "?")[0]


# ---------------------------------------------------------------- 旅データ
def trips_file(username):
    return os.path.join(DATA_DIR, f"trips_{username}.json")


def load_trips(username):
    path = trips_file(username)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        trips = json.load(f)
    for t in trips:
        t["photos"] = [base64.b64decode(p) for p in t.get("photos", [])]
        t.setdefault("visibility", "default")
    return trips


def save_trips(username, trips):
    out = []
    for t in trips:
        c = dict(t)
        c["photos"] = [base64.b64encode(p).decode() for p in t.get("photos", [])]
        out.append(c)
    with open(trips_file(username), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)


def effective_visibility(trip, owner):
    v = trip.get("visibility", "default")
    return owner.get("default_visibility", "friends") if v == "default" else v


def _sample_trips():
    return [
        {
            "id": str(uuid.uuid4()), "place": "エッフェル塔", "country": "フランス", "city": "パリ",
            "lat": 48.8584, "lon": 2.2945, "visit_date": "2025-10-12",
            "expectation": "映画みたいなロマンチックな夜景。シャンパン片手に最高の写真が撮れるはず！",
            "reality": "夜景は本当に綺麗だった。ただし行列は90分、スリ注意の放送が常に流れていて気が抜けない。芝生は立入禁止だった。それでも点灯の瞬間は鳥肌もの。",
            "rating": 4, "photos": [], "status": "visited", "visibility": "default",
        },
        {
            "id": str(uuid.uuid4()), "place": "カオサン通り", "country": "タイ", "city": "バンコク",
            "lat": 13.7590, "lon": 100.4977, "visit_date": "2026-01-05",
            "expectation": "バックパッカーの聖地で安くて美味い屋台メシ三昧。世界中の旅人と仲良くなる。",
            "reality": "想像の3倍うるさくて3倍楽しい。パッタイは60バーツで絶品。ただし観光地化が進んでいて『聖地』感は薄め。虫の素揚げは話のネタに一口で十分。",
            "rating": 5, "photos": [], "status": "visited", "visibility": "public",
        },
        {
            "id": str(uuid.uuid4()), "place": "マチュピチュ", "country": "ペルー", "city": "クスコ",
            "lat": -13.1631, "lon": -72.5450, "visit_date": "2026-09-20",
            "expectation": "雲海に浮かぶ天空都市を朝イチで独り占めしたい。高山病が少し心配。",
            "reality": "", "rating": 0, "photos": [], "status": "planned", "visibility": "default",
        },
    ]


# ---------------------------------------------------------------- ログイン画面
def auth_gate():
    lang_label = st.selectbox(tr("language"), ["日本語", "English"],
                              index=0 if st.session_state.lang == "ja" else 1)
    new_lang = "ja" if lang_label == "日本語" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown(f"""
    <div class="login-logo">
      <div class="logo-grad big">🧭 {tr('hero_title')}</div>
      <div class="cap">{tr('tagline')}</div>
    </div>""", unsafe_allow_html=True)

    tab_login, tab_reg = st.tabs([tr("tab_login"), tr("tab_register")])
    users = load_users()

    with tab_login:
        with st.form("login"):
            uid = st.text_input(tr("user_id"))
            pw = st.text_input(tr("password"), type="password")
            if st.form_submit_button(tr("login_btn"), type="primary", use_container_width=True):
                u = users.get(uid)
                if u and hash_pw(pw, u["salt"]) == u["pw"]:
                    st.session_state.user = uid
                    st.session_state.lang = u.get("lang", st.session_state.lang)
                    st.rerun()
                else:
                    st.error(tr("login_err"))

    with tab_reg:
        with st.form("register"):
            name = st.text_input(tr("display_name"), placeholder=tr("display_name_ph"))
            uid = st.text_input(tr("uid_label"), placeholder=tr("uid_ph"))
            pw = st.text_input(tr("pw_label"), type="password")
            if st.form_submit_button(tr("create_btn"), type="primary", use_container_width=True):
                if not (name and uid and pw):
                    st.error(tr("err_fill_all"))
                elif not uid.isascii() or not uid.replace("_", "").isalnum():
                    st.error(tr("err_uid_format"))
                elif len(pw) < 6:
                    st.error(tr("err_pw_len"))
                elif uid in users:
                    st.error(tr("err_uid_taken"))
                else:
                    salt = uuid.uuid4().hex
                    users[uid] = {"name": name, "salt": salt, "pw": hash_pw(pw, salt),
                                  "lang": st.session_state.lang, **{k: (list(v) if isinstance(v, list) else v)
                                                                    for k, v in USER_DEFAULTS.items() if k != "lang"}}
                    save_users(users)
                    save_trips(uid, _sample_trips())  # お試し用サンプルを初期投入
                    st.session_state.user = uid
                    st.rerun()

    st.stop()


if "user" not in st.session_state:
    auth_gate()

USERS = load_users()
USER_ID = st.session_state.user
ME = USERS.get(USER_ID, dict(USER_DEFAULTS, name=USER_ID))
st.session_state.lang = ME.get("lang", st.session_state.lang)

if "trips" not in st.session_state:
    st.session_state.trips = load_trips(USER_ID)
trips = st.session_state.trips


def persist():
    save_trips(USER_ID, st.session_state.trips)


# ---------------------------------------------------------------- 共通部品
STAR = lambda r: "★" * r + "☆" * (5 - r) if r else "—"


def page_header(icon, title, sub=""):
    st.markdown(f"""
    <div class="page-head">
      <div class="ico">{icon}</div>
      <div><div class="t">{title}</div><div class="s">{sub}</div></div>
    </div>""", unsafe_allow_html=True)


def popup_html(t, owner_name=None):
    reality = t["reality"] or "—"
    owner_line = f'<p style="margin:0 0 4px; font-size:12px; font-weight:bold; color:#805ad5;">👤 {owner_name}</p>' if owner_name else ""
    return f"""
    <div style="font-family:sans-serif; width:260px;">
      {owner_line}
      <h4 style="margin:0 0 4px;">{'✅' if t['status']=='visited' else '🗓️'} {t['place']}</h4>
      <p style="margin:0 0 6px; color:#888; font-size:12px;">{country_label(t['country'])}・{t['city']}｜{t['visit_date']}</p>
      <p style="margin:0; font-size:12px;"><b style="color:#2b6cb0;">{tr('expectation')}</b><br>{t['expectation']}</p>
      <p style="margin:6px 0 0; font-size:12px;"><b style="color:#c05621;">{tr('reality')}</b><br>{reality}</p>
      <p style="margin:6px 0 0; font-size:13px;"><span style="color:#d69e2e;">{STAR(t['rating'])}</span></p>
    </div>"""


# カテゴリ → (ピンの色, アイコン)：Flighty風に自分と友達で色を分ける
PIN_STYLE = {
    "my_visited": ("orange", "camera"),
    "my_planned": ("blue", "calendar"),
    "fr_visited": ("purple", "camera"),
    "fr_planned": ("pink", "calendar"),
}


def build_map(entries, height=440):
    """entries: (trip, category, owner_name) のリスト"""
    m = folium.Map(location=[25, 20], zoom_start=1, tiles="CartoDB positron")
    geo = load_world_geojson()

    def paint(countries, fill, line):
        names = {COUNTRIES.get(c) for c in countries}
        names.discard(None)
        if geo and names:
            feats = [f for f in geo["features"] if f["properties"]["name"] in names]
            folium.GeoJson(
                {"type": "FeatureCollection", "features": feats},
                style_function=lambda f, fill=fill, line=line: {
                    "fillColor": fill, "color": line, "weight": 1, "fillOpacity": 0.3},
            ).add_to(m)

    # 足跡：自分はオレンジ、友達はパープルで塗る（自分を上に重ねる）
    paint({t["country"] for t, cat, _ in entries if cat == "fr_visited"}, "#b794f4", "#805ad5")
    paint({t["country"] for t, cat, _ in entries if cat == "my_visited"}, "#f6ad55", "#dd6b20")

    for t, cat, owner_name in entries:
        color, icon = PIN_STYLE[cat]
        mine = cat.startswith("my_")
        folium.Marker(
            [t["lat"], t["lon"]],
            tooltip=t["place"] if mine else f"{t['place']}（{owner_name}）",
            popup=folium.Popup(popup_html(t, None if mine else owner_name), max_width=300),
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
        ).add_to(m)
    return st_folium(m, height=height, use_container_width=True,
                     returned_objects=[], key="home_map")


def feed_card(t, owner_uid, owner, show_visibility=False):
    with st.container(border=True):
        st.markdown(f"""
        <div class="feed-user">
          <div class="av">{avatar_html(owner, owner.get('name', owner_uid))}</div>
          <div><div class="un">{owner.get('name', owner_uid)} <span style="opacity:.5;">@{owner_uid}</span></div>
          <div class="loc">📍 {country_label(t['country'])}・{t['city']}</div></div>
        </div>""", unsafe_allow_html=True)
        if t["photos"]:
            if len(t["photos"]) == 1:
                st.image(t["photos"][0], use_container_width=True)
            else:
                pcols = st.columns(min(3, len(t["photos"])))
                for i, ph in enumerate(t["photos"]):
                    pcols[i % len(pcols)].image(ph, use_container_width=True)
        chips = ('<span class="chip chip-done">' + tr("chip_visited") + '</span>'
                 if t["status"] == "visited"
                 else '<span class="chip chip-plan">' + tr("chip_planned") + '</span>')
        if show_visibility:
            vis = effective_visibility(t, owner)
            chips += ('<span class="chip chip-pub">' + tr("vis_public_chip") + '</span>' if vis == "public"
                      else '<span class="chip chip-frd">' + tr("vis_friends_chip") + '</span>')
        head, stars = st.columns([3, 1])
        head.markdown(f'<p class="trip-title">{t["place"]}</p>'
                      f'<div class="trip-meta">🗓 {t["visit_date"]}　{chips}</div>',
                      unsafe_allow_html=True)
        stars.markdown(f'<div class="trip-stars">{STAR(t["rating"])}</div>', unsafe_allow_html=True)
        exp_col, real_col = st.columns(2)
        with exp_col:
            st.markdown(f"**{tr('expectation')}**")
            st.info(t["expectation"])
        with real_col:
            st.markdown(f"**{tr('reality')}**")
            if t["reality"]:
                st.warning(t["reality"])
            else:
                st.caption(tr("no_reality"))


VIS_OPTIONS = ["default", "post_public", "friends_only"]


def visibility_select(label_key="visibility", current="default"):
    labels = {"default": tr("vis_default"), "post_public": tr("vis_post_public"),
              "friends_only": tr("vis_friends")}
    idx = {"default": 0, "public": 1, "friends": 2}.get(current, 0)
    choice = st.selectbox(tr(label_key), VIS_OPTIONS, index=idx, format_func=lambda v: labels[v])
    return {"default": "default", "post_public": "public", "friends_only": "friends"}[choice]


# ---------------------------------------------------------------- ナビゲーション
NAV = [("map", "🗺️", "nav_map"), ("feed", "📖", "nav_feed"), ("add", "➕", "nav_add"),
       ("update", "🛬", "nav_update"), ("profile", "👤", "nav_profile")]
if "page" not in st.session_state:
    st.session_state.page = "map"
page = st.session_state.page

# ---------- マップ ----------
if page == "map":
    st.markdown(f"""
    <div class="hero">
      <div class="hero-eyebrow">Expectation &amp; Reality</div>
      <div class="hero-title">{tr('hero_title')}</div>
      <div class="hero-sub">{tr('hero_sub')}</div>
    </div>""", unsafe_allow_html=True)

    visited = [t for t in trips if t["status"] == "visited"]
    planned = [t for t in trips if t["status"] == "planned"]
    stats = [
        ("🌍", f"{len({t['country'] for t in visited})}<small>{tr('unit_countries')}</small>", tr("stat_countries")),
        ("🏙️", f"{len({(t['country'], t['city']) for t in visited})}<small>{tr('unit_cities')}</small>", tr("stat_cities")),
        ("📸", f"{len(visited)}<small>{tr('unit_spots')}</small>", tr("stat_spots")),
        ("🗓️", f"{len(planned)}<small>{tr('unit_plans')}</small>", tr("stat_planned")),
    ]
    st.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><div class="ico">{i}</div><div class="val">{v}</div><div class="lab">{l}</div></div>'
        for i, v, l in stats) + '</div>', unsafe_allow_html=True)

    # Flighty風フィルタ：自分/友達 × 行った/これから
    MAP_FILTERS = ["my_visited", "my_planned", "fr_visited", "fr_planned"]
    active = st.pills("map_filter", MAP_FILTERS, selection_mode="multi",
                      default=MAP_FILTERS, format_func=lambda k: tr(f"flt_{k}"),
                      label_visibility="collapsed")

    entries = []
    for t in trips:
        cat = "my_visited" if t["status"] == "visited" else "my_planned"
        if cat in active:
            entries.append((t, cat, ME.get("name", USER_ID)))
    for fid in ME.get("friends", []):
        owner = USERS.get(fid)
        if not owner:
            continue
        for t in load_trips(fid):
            if effective_visibility(t, owner) not in ("friends", "public"):
                continue
            cat = "fr_visited" if t["status"] == "visited" else "fr_planned"
            if cat in active:
                entries.append((t, cat, owner.get("name", fid)))
    build_map(entries)

# ---------- フィード ----------
elif page == "feed":
    page_header("📖", tr("feed_title"), tr("feed_sub"))
    scope = st.radio("scope", [tr("scope_friends"), tr("scope_discover")],
                     horizontal=True, label_visibility="collapsed")

    if scope == tr("scope_friends"):
        # 自分 + フレンドの投稿（友達のみ or 全体公開）
        entries = [(t, USER_ID, ME) for t in trips]
        for fid in ME.get("friends", []):
            owner = USERS.get(fid)
            if not owner:
                continue
            for t in load_trips(fid):
                if effective_visibility(t, owner) in ("friends", "public"):
                    entries.append((t, fid, owner))
        flt = st.radio("filter", [tr("flt_all"), tr("flt_visited"), tr("flt_planned")],
                       horizontal=True, label_visibility="collapsed")
        entries = [(t, uid, o) for t, uid, o in entries
                   if flt == tr("flt_all")
                   or (flt == tr("flt_visited") and t["status"] == "visited")
                   or (flt == tr("flt_planned") and t["status"] == "planned")]
    else:
        # 全ユーザーの「全体公開」投稿
        entries = []
        for uid, owner in USERS.items():
            tl = trips if uid == USER_ID else load_trips(uid)
            for t in tl:
                if effective_visibility(t, owner) == "public":
                    entries.append((t, uid, owner))

    if not entries:
        st.info(tr("feed_empty"))
    for t, uid, owner in sorted(entries, key=lambda e: e[0]["visit_date"], reverse=True):
        feed_card(t, uid, owner, show_visibility=(uid == USER_ID))

# ---------- 投稿（事前登録） ----------
elif page == "add":
    page_header("🛫", tr("add_title"), tr("add_sub"))
    st.markdown(f"**{tr('pick_map')}**")
    pick = folium.Map(location=[25, 20], zoom_start=1, tiles="CartoDB positron")
    if "pick_latlon" in st.session_state:
        folium.Marker(st.session_state.pick_latlon, icon=folium.Icon(color="blue")).add_to(pick)
    out = st_folium(pick, height=320, use_container_width=True, key="pick_map")
    if out and out.get("last_clicked"):
        ll = (out["last_clicked"]["lat"], out["last_clicked"]["lng"])
        if st.session_state.get("pick_latlon") != ll:
            st.session_state.pick_latlon = ll
            st.rerun()

    latlon = st.session_state.get("pick_latlon")
    if latlon:
        st.success(f"{tr('picked')}: {latlon[0]:.4f}, {latlon[1]:.4f}")
    else:
        st.info(tr("pick_info"))
    with st.form("add_trip"):
        place = st.text_input(tr("place"), placeholder=tr("place_ph"))
        country = st.selectbox(tr("country"), list(COUNTRIES.keys()), index=None,
                               placeholder=tr("country_ph"), format_func=country_label)
        city = st.text_input(tr("city"), placeholder=tr("city_ph"))
        visit_date = st.date_input(tr("visit_date"), value=date.today())
        expectation = st.text_area(tr("expect_label"), height=120, placeholder=tr("expect_ph"))
        visibility = visibility_select()
        if st.form_submit_button(tr("submit_trip"), type="primary", use_container_width=True):
            if not (place and country and city and expectation and latlon):
                st.error(tr("err_missing"))
            else:
                st.session_state.trips.append({
                    "id": str(uuid.uuid4()), "place": place, "country": country,
                    "city": city, "lat": latlon[0], "lon": latlon[1],
                    "visit_date": str(visit_date), "expectation": expectation,
                    "reality": "", "rating": 0, "photos": [], "status": "planned",
                    "visibility": visibility,
                })
                persist()
                del st.session_state.pick_latlon
                st.success(f"「{place}」{tr('added')}")

# ---------- 追記（事後） ----------
elif page == "update":
    page_header("🛬", tr("upd_title"), tr("upd_sub"))
    planned = [t for t in trips if t["status"] == "planned"]
    if not planned:
        st.info(tr("upd_none"))
    else:
        target = st.selectbox(tr("upd_which"), planned,
                              format_func=lambda t: f"{t['place']}（{country_label(t['country'])}・{t['city']}｜{t['visit_date']}）")
        st.markdown(f"> 🌈 **{tr('upd_past')}**: {target['expectation']}")
        with st.form("update_trip"):
            reality = st.text_area(tr("upd_reality"), height=140, placeholder=tr("upd_reality_ph"))
            rating = st.slider(tr("rating"), 1, 5, 3, format="%d ★")
            photos = st.file_uploader(tr("photos"), type=["png", "jpg", "jpeg", "webp"],
                                      accept_multiple_files=True)
            visibility = visibility_select(current=target.get("visibility", "default"))
            if st.form_submit_button(tr("save_reality"), type="primary", use_container_width=True):
                if not reality:
                    st.error(tr("err_reality"))
                else:
                    target["reality"] = reality
                    target["rating"] = rating
                    target["photos"] = [p.getvalue() for p in photos] if photos else []
                    target["status"] = "visited"
                    target["visibility"] = visibility
                    persist()
                    st.success(f"「{target['place']}」{tr('updated')}")
                    st.balloons()

# ---------- プロフィール ----------
elif page == "profile":
    visited = [t for t in trips if t["status"] == "visited"]
    st.markdown(f"""
    <div class="prof">
      <div class="av">{avatar_html(ME, ME.get('name', USER_ID))}</div>
      <div><div class="nm">{ME.get('name', USER_ID)}</div><div class="id">@{USER_ID}</div></div>
    </div>""", unsafe_allow_html=True)

    tab_posts, tab_friends, tab_settings = st.tabs([tr("tab_posts"), tr("tab_friends"), tr("tab_settings")])

    with tab_posts:
        stats = [
            ("📸", f"{len(visited)}", tr("stat_posts")),
            ("🌍", f"{len({t['country'] for t in visited})}", tr("stat_c")),
            ("🏙️", f"{len({(t['country'], t['city']) for t in visited})}", tr("stat_ci")),
            ("🗓️", f"{len(trips) - len(visited)}", tr("stat_p")),
        ]
        st.markdown('<div class="stats">' + "".join(
            f'<div class="stat"><div class="ico">{i}</div><div class="val">{v}</div><div class="lab">{l}</div></div>'
            for i, v, l in stats) + '</div>', unsafe_allow_html=True)
        all_photos = [ph for t in visited for ph in t["photos"]]
        st.markdown(f"**{tr('memories')}**")
        if all_photos:
            gcols = st.columns(3)
            for i, ph in enumerate(all_photos):
                gcols[i % 3].image(ph, use_container_width=True)
        else:
            st.caption(tr("no_photos"))

    with tab_friends:
        # 受信した申請
        reqs = ME.get("requests_in", [])
        if reqs:
            st.markdown(f"**{tr('req_in')}**")
            for rid in list(reqs):
                ru = USERS.get(rid, {})
                with st.container(key=f"frow_req_{rid}"):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.markdown(f"""<div class="friend-row"><div class="av">{avatar_html(ru, ru.get('name', rid))}</div>
                        <div><b>{ru.get('name', rid)}</b><br><small style="opacity:.6;">@{rid}</small></div></div>""",
                                unsafe_allow_html=True)
                    if c2.button(tr("accept"), key=f"acc_{rid}", type="primary", use_container_width=True):
                        ME["requests_in"].remove(rid)
                        ME.setdefault("friends", []).append(rid)
                        USERS.setdefault(rid, {}).setdefault("friends", []).append(USER_ID)
                        save_users(USERS)
                        st.rerun()
                    if c3.button(tr("decline"), key=f"dec_{rid}", use_container_width=True):
                        ME["requests_in"].remove(rid)
                        save_users(USERS)
                        st.rerun()
            st.divider()

        # フレンド追加
        st.markdown(f"**{tr('add_friend')}**")
        with st.container(key="frow_add"):
            c1, c2 = st.columns([3, 1])
            target_id = c1.text_input("friend_id", placeholder=tr("friend_id_ph"),
                                      label_visibility="collapsed")
            if c2.button(tr("send_req"), type="primary", use_container_width=True):
                target_id = target_id.strip().lstrip("@")
                if target_id == USER_ID:
                    st.error(tr("err_self"))
                elif target_id in ME.get("friends", []):
                    st.error(tr("err_already"))
                elif target_id not in USERS:
                    st.error(tr("err_nouser"))
                elif USER_ID in USERS[target_id].get("requests_in", []):
                    st.warning(tr("err_pending"))
                else:
                    USERS[target_id].setdefault("requests_in", []).append(USER_ID)
                    save_users(USERS)
                    st.success(tr("req_sent"))

        # フレンド一覧
        st.markdown(f"**{tr('friends_list')}**")
        friends = ME.get("friends", [])
        if not friends:
            st.caption(tr("no_friends"))
        for fid in list(friends):
            fu = USERS.get(fid, {})
            with st.container(key=f"frow_{fid}"):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"""<div class="friend-row"><div class="av">{avatar_html(fu, fu.get('name', fid))}</div>
                    <div><b>{fu.get('name', fid)}</b><br><small style="opacity:.6;">@{fid}</small></div></div>""",
                            unsafe_allow_html=True)
                if c2.button(tr("remove"), key=f"rm_{fid}", use_container_width=True):
                    ME["friends"].remove(fid)
                    if USER_ID in USERS.get(fid, {}).get("friends", []):
                        USERS[fid]["friends"].remove(USER_ID)
                    save_users(USERS)
                    st.rerun()

    with tab_settings:
        # アイコン設定
        st.markdown(f"**{tr('avatar')}**")
        av = st.file_uploader(tr("avatar_upload"), type=["png", "jpg", "jpeg", "webp"], key="avatar_up")
        # デフォルト公開範囲
        vis_labels = {"public": tr("vis_public"), "friends": tr("vis_friends")}
        default_vis = st.radio(tr("default_vis"), ["friends", "public"],
                               index=0 if ME.get("default_visibility", "friends") == "friends" else 1,
                               format_func=lambda v: vis_labels[v], horizontal=True)
        # 言語
        lang_label = st.radio(tr("language"), ["日本語", "English"],
                              index=0 if st.session_state.lang == "ja" else 1, horizontal=True)
        if st.button(tr("save_settings"), type="primary", use_container_width=True):
            if av is not None:
                ME["avatar"] = base64.b64encode(av.getvalue()).decode()
            ME["default_visibility"] = default_vis
            ME["lang"] = "ja" if lang_label == "日本語" else "en"
            st.session_state.lang = ME["lang"]
            save_users(USERS)
            st.success(tr("saved"))
            st.rerun()

        st.divider()
        if st.button(tr("logout"), use_container_width=True):
            for k in ("user", "trips", "page", "pick_latlon"):
                st.session_state.pop(k, None)
            st.rerun()

# ---------------------------------------------------------------- 下部ナビバー
with st.container(key="bottomnav"):
    cols = st.columns(len(NAV))
    for col, (key, icon, label_key) in zip(cols, NAV):
        if col.button(icon, key=f"nav_{key}", help=tr(label_key), use_container_width=True,
                      type="primary" if page == key else "secondary"):
            st.session_state.page = key
            st.rerun()
