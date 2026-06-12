# -*- coding: utf-8 -*-
"""たびログ / TabiLog — 「期待と現実」を記録する旅アプリ"""
import hashlib
import hmac
import io
import math
import uuid
from datetime import date

import folium
import requests
import streamlit as st
from PIL import Image
from streamlit_cookies_controller import CookieController
from streamlit_folium import st_folium
from supabase import create_client

st.set_page_config(page_title="たびログ | TabiLog", page_icon="🧭",
                   layout="centered", initial_sidebar_state="collapsed")


@st.cache_resource(show_spinner=False)
def get_sb():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


sb = get_sb()
cookies = CookieController(key="tabilog_cookies")
COOKIE_NAME = "tabilog_token"


def make_token(uid):
    sig = hmac.new(st.secrets["SUPABASE_KEY"].encode(), uid.encode(), hashlib.sha256).hexdigest()
    return f"{uid}|{sig}"


def parse_token(token):
    if not token or "|" not in token:
        return None
    uid, sig = token.split("|", 1)
    good = hmac.new(st.secrets["SUPABASE_KEY"].encode(), uid.encode(), hashlib.sha256).hexdigest()
    return uid if hmac.compare_digest(sig, good) else None


def remember_login(uid):
    cookies.set(COOKIE_NAME, make_token(uid), max_age=60 * 60 * 24 * 30)


# クッキー操作は st.rerun() と同一サイクルだと反映されないため、次サイクルで実行する
_skip_cookie_login = False
_cookie_action = st.session_state.pop("cookie_action", None)
if _cookie_action == "__remove__":
    cookies.remove(COOKIE_NAME)
    _skip_cookie_login = True
elif _cookie_action:
    remember_login(_cookie_action)

# ---------------------------------------------------------------- 多言語
I18N = {
    "ja": {
        "tagline": "「期待と現実」を記録する旅アプリ",
        "tab_login": "ログイン", "tab_register": "新規登録",
        "user_id": "ユーザーID", "password": "パスワード",
        "login_btn": "ログイン", "login_err": "ユーザーIDまたはパスワードが違います",
        "display_name": "表示名", "display_name_ph": "例：たろう",
        "uid_label": "ユーザーID（半角英数字）", "uid_ph": "例：taro_trip",
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
        "pick_map": "📍 地図をクリックするか、場所名で検索",
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
        "rating_photo": "📸 写真映え", "rating_again": "🔁 もう一度行きたい度",
        "photos": "写真をアップロード",
        "save_reality": "現実を記録する", "err_reality": "「実際どうだったか」を入力してください",
        "updated": "の現実を記録しました。おかえりなさい 🏠",
        "tab_posts": "📊 記録", "tab_friends": "👥 フレンド", "tab_wrapped": "✨ 振り返り", "tab_settings": "⚙️ 設定",
        "stat_posts": "投稿", "stat_c": "国", "stat_ci": "都市", "stat_p": "計画中",
        "stat_gap": "期待超え率", "stat_dist": "総移動距離",
        "earth_laps": "地球 {laps} 周分",
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
        # --- 新機能 ---
        "gap_label": "🎯 期待と比べてどうだった？",
        "gap_up": "🚀 期待を超えた", "gap_even": "🙂 期待通り", "gap_down": "📉 期待以下",
        "capsule": "⏳ タイムカプセルにする（現実を書くまで期待を自分でもロック）",
        "capsule_locked": "🔒 タイムカプセル封印中 — 現実を記録すると開封されます",
        "capsule_open": "🎉 タイムカプセル開封！あの時の期待：",
        "others_reality": "👀 みんなの現実（同じあたりに行った人）",
        "no_others": "近くの公開された「現実」はまだありません",
        "companions": "👥 一緒に行った友達",
        "with_label": "と一緒",
        "rx_nice": "期待通りで何より", "rx_lol": "現実は厳しい", "rx_helpful": "参考になった",
        "baton_title": "🎁 旅のバトン（おすすめを送る）",
        "baton_to": "送る相手", "baton_place": "おすすめの場所", "baton_note": "おすすめポイント",
        "baton_send": "バトンを送る", "baton_sent": "バトンを送りました！",
        "baton_geo_err": "場所が見つかりませんでした。表記を変えて試してください",
        "baton_in": "🎁 届いた旅のバトン", "baton_accept": "計画に追加", "baton_decline": "見送る",
        "baton_from": "さんからのおすすめ", "baton_added": "計画に追加しました！",
        "search_place": "🔍 場所名で検索（例：Sagrada Familia）", "search_btn": "検索",
        "geocode_err": "見つかりませんでした。表記を変えて試してください", "geocode_ok": "📍 見つけました：",
        "delete": "🗑 削除",
        "confirm_del": "この投稿を完全に削除します（元に戻せません）",
        "confirm_del_btn": "完全に削除する",
        "tut_title": "ようこそ、たびログへ！",
        "tut_sub": "「期待と現実」を記録する、3ステップの旅ノート",
        "tut_1": "<b>➕ 投稿</b>：旅の前に「期待していること」を登録（地図クリックか場所名検索で場所を選択）",
        "tut_2": "<b>🛬 追記</b>：帰ってきたら「実際どうだったか」・写真・評価を記録",
        "tut_3": "<b>👤 フレンド</b>：友達を追加すると、お互いの旅がマップとフィードに表示",
        "tut_example": "📝 記入例（エッフェル塔）",
        "tut_exp": "🌈 期待：映画みたいなロマンチックな夜景。シャンパン片手に最高の写真が撮れるはず！",
        "tut_real": "📷 現実：夜景は本当に綺麗だった。ただし行列は90分、スリ注意の放送が常に流れていて気が抜けない。それでも点灯の瞬間は鳥肌もの。",
        "rem_soon": "🛫 もうすぐ「{place}」（{date}）！出発前に期待を見返そう",
        "rem_overdue": "🛬 「{place}」から帰ってきた？🛬 追記から現実を記録しよう",
        "timelapse": "⏪ 足跡タイムラプス（日付までの足跡を表示）",
        "wrapped_year": "振り返る年", "wrapped_none": "この年の訪問記録はまだありません",
        "w_countries": "か国", "w_cities": "都市", "w_spots": "スポット",
        "w_gap": "期待超え率", "w_dist": "移動距離", "w_best": "今年のベスト",
        "w_title": "{year}年のあなたの旅",
    },
    "en": {
        "tagline": "A travel journal for expectations & reality",
        "tab_login": "Log in", "tab_register": "Sign up",
        "user_id": "User ID", "password": "Password",
        "login_btn": "Log in", "login_err": "Wrong user ID or password",
        "display_name": "Display name", "display_name_ph": "e.g. Alex",
        "uid_label": "User ID (alphanumeric)", "uid_ph": "e.g. alex_trip",
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
        "pick_map": "📍 Click the map or search by name",
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
        "rating_photo": "📸 Photogenic", "rating_again": "🔁 Would go again",
        "photos": "Upload photos",
        "save_reality": "Save the reality", "err_reality": "Please write how it actually was",
        "updated": " updated. Welcome home 🏠",
        "tab_posts": "📊 Posts", "tab_friends": "👥 Friends", "tab_wrapped": "✨ Wrapped", "tab_settings": "⚙️ Settings",
        "stat_posts": "Posts", "stat_c": "Countries", "stat_ci": "Cities", "stat_p": "Planned",
        "stat_gap": "Beat expectations", "stat_dist": "Distance traveled",
        "earth_laps": "{laps} laps around Earth",
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
        # --- new features ---
        "gap_label": "🎯 Compared to your expectations?",
        "gap_up": "🚀 Exceeded them", "gap_even": "🙂 As expected", "gap_down": "📉 Fell short",
        "capsule": "⏳ Time capsule (lock the expectation until you write the reality)",
        "capsule_locked": "🔒 Time capsule sealed — it opens when you record the reality",
        "capsule_open": "🎉 Time capsule opened! Your expectation back then:",
        "others_reality": "👀 Realities from people who went nearby",
        "no_others": "No public realities near here yet",
        "companions": "👥 Friends you went with",
        "with_label": "with",
        "rx_nice": "Glad it went as hoped", "rx_lol": "Reality is brutal", "rx_helpful": "Helpful",
        "baton_title": "🎁 Trip baton (recommend a place)",
        "baton_to": "Send to", "baton_place": "Place to recommend", "baton_note": "Why you recommend it",
        "baton_send": "Send the baton", "baton_sent": "Baton sent!",
        "baton_geo_err": "Couldn't find that place. Try a different spelling",
        "baton_in": "🎁 Trip batons you received", "baton_accept": "Add to my plans", "baton_decline": "Pass",
        "baton_from": "recommends", "baton_added": "Added to your plans!",
        "search_place": "🔍 Search by place name (e.g. Sagrada Familia)", "search_btn": "Search",
        "geocode_err": "Not found. Try a different spelling", "geocode_ok": "📍 Found: ",
        "delete": "🗑 Delete",
        "confirm_del": "This will permanently delete the post (can't be undone)",
        "confirm_del_btn": "Delete permanently",
        "tut_title": "Welcome to TabiLog!",
        "tut_sub": "A 3-step journal for expectations & reality",
        "tut_1": "<b>➕ Post</b>: before a trip, write down what you expect (pick the spot by clicking the map or searching)",
        "tut_2": "<b>🛬 Reality</b>: after the trip, record how it really was, with photos and ratings",
        "tut_3": "<b>👤 Friends</b>: add friends and see each other's trips on the map and feed",
        "tut_example": "📝 Example (Eiffel Tower)",
        "tut_exp": "🌈 Expectation: a movie-like romantic night view. The perfect photo with champagne in hand!",
        "tut_real": "📷 Reality: the night view really was beautiful. But the queue was 90 minutes and pickpocket warnings played non-stop. Still, the moment it lit up gave me goosebumps.",
        "rem_soon": "🛫 \"{place}\" is coming up ({date})! Reread your expectations",
        "rem_overdue": "🛬 Back from \"{place}\"? Record the reality from 🛬",
        "timelapse": "⏪ Footprint timelapse (show footprints up to a date)",
        "wrapped_year": "Year to look back on", "wrapped_none": "No visits recorded for this year yet",
        "w_countries": "countries", "w_cities": "cities", "w_spots": "spots",
        "w_gap": "beat expectations", "w_dist": "traveled", "w_best": "Best of the year",
        "w_title": "Your {year} in travel",
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
/* 固定ヘッダーを透過にしてコンテンツと干渉しないように */
[data-testid="stHeader"] { background: transparent; }
/* 右下のStreamlitバッジ・フッターを非表示（下部ナビと重なってボタンが押せなくなるため） */
/* Streamlit Cloudのバッジ（作者アバター+ロゴ）はCSSモジュールのハッシュ付きクラスなので前方一致で消す */
[class*="viewerBadge"], footer, .stAppDeployButton, [data-testid="stAppDeployButton"],
[class^="_profileContainer"], [class^="_profilePreview"], [class^="_container"],
[class^="_link"], [class^="_viewerBadge"], [class^="_chevronDownIcon"],
[data-testid="appCreatorAvatar"], a[href*="streamlit.io/cloud"] {
  display: none !important;
}
[data-testid="stMainBlockContainer"] { max-width: 640px; padding: 2.2rem 1rem 7rem; }

.logo-grad { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; background: linear-gradient(135deg, #ffb46a, #ff5e7e, #a07bff); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.hero { position: relative; overflow: hidden; background: linear-gradient(135deg, #ff9a5a 0%, #ff5e7e 45%, #8f5eff 100%); border-radius: 24px; padding: 1.7rem 1.5rem 1.5rem; margin-bottom: 1.2rem; color: #fff; box-shadow: 0 12px 36px rgba(255, 94, 126, .25); }
.hero::after { content: "✈️"; position: absolute; right: 1rem; top: .8rem; font-size: 3.4rem; opacity: .25; transform: rotate(-12deg); }
.hero-eyebrow { font-size: .72rem; font-weight: 700; letter-spacing: .35em; text-transform: uppercase; opacity: .85; }
.hero-title { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 2rem; line-height: 1.15; letter-spacing: .06em; text-shadow: 0 2px 10px rgba(0,0,0,.15); }
.hero-sub { margin-top: .4rem; font-size: .85rem; opacity: .92; font-weight: 500; }

.page-head { display: flex; align-items: center; gap: .9rem; margin: .2rem 0 .5rem; }
.page-head .ico { width: 52px; height: 52px; flex: none; display: flex; align-items: center; justify-content: center; font-size: 1.55rem; border-radius: 17px; background: linear-gradient(135deg, #ff9a5a, #ff5e7e 60%, #8f5eff); box-shadow: 0 8px 20px rgba(255, 94, 126, .3); }
.page-head .t { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.5rem; letter-spacing: .04em; line-height: 1.2; }
.page-head .s { font-size: .82rem; opacity: .65; margin-top: .15rem; }

.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .7rem; margin-bottom: 1.1rem; }
.stats.six { grid-template-columns: repeat(3, 1fr); }
.stat { background: rgba(150, 160, 200, .08); border: 1px solid rgba(150, 160, 200, .18); border-radius: 18px; padding: .85rem .9rem; }
.stat .ico { font-size: 1.15rem; }
.stat .val { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.55rem; line-height: 1.25; background: linear-gradient(135deg, #ffb46a, #ff5e7e, #a07bff); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.stat .lab { font-size: .72rem; opacity: .65; font-weight: 500; }

.chip { display: inline-block; font-size: .72rem; font-weight: 700; padding: .22em .85em; border-radius: 999px; vertical-align: middle; margin-right: .25em; }
.chip-done { background: rgba(72, 187, 120, .18); color: #68d391; border: 1px solid rgba(72,187,120,.35); }
.chip-plan { background: rgba(99, 179, 237, .15); color: #63b3ed; border: 1px solid rgba(99,179,237,.35); }
.chip-pub  { background: rgba(246, 173, 85, .15); color: #f6ad55; border: 1px solid rgba(246,173,85,.35); }
.chip-frd  { background: rgba(160, 123, 255, .15); color: #b794f4; border: 1px solid rgba(160,123,255,.35); }
.chip-gap-up   { background: rgba(72, 187, 120, .15); color: #68d391; border: 1px solid rgba(72,187,120,.35); }
.chip-gap-even { background: rgba(160, 174, 192, .15); color: #cbd5e0; border: 1px solid rgba(160,174,192,.35); }
.chip-gap-down { background: rgba(245, 101, 101, .15); color: #fc8181; border: 1px solid rgba(245,101,101,.35); }
.trip-title { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.35rem; letter-spacing: .03em; line-height: 1.3; margin: 0; }
.trip-meta { font-size: .8rem; opacity: .75; margin-top: .15rem; }
.trip-stars { text-align: right; font-size: .95rem; color: #f6ad55; letter-spacing: .08em; white-space: nowrap; line-height: 1.6; }

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

/* ---- Wrapped カード ---- */
.wrapped { background: linear-gradient(160deg, #2d1b4e 0%, #8f5eff 55%, #ff5e7e 100%); border-radius: 26px; padding: 1.8rem 1.6rem; color: #fff; margin: .6rem 0 1rem; box-shadow: 0 14px 40px rgba(143, 94, 255, .35); }
.wrapped .wt { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.4rem; letter-spacing: .05em; margin-bottom: 1rem; }
.wrapped .grid { display: grid; grid-template-columns: 1fr 1fr; gap: .9rem; }
.wrapped .cell .v { font-family: 'Zen Maru Gothic', sans-serif; font-weight: 900; font-size: 1.9rem; line-height: 1.1; }
.wrapped .cell .k { font-size: .75rem; opacity: .8; }
.wrapped .best { margin-top: 1.1rem; padding-top: .9rem; border-top: 1px solid rgba(255,255,255,.25); font-size: .9rem; }
.wrapped .best b { font-family: 'Zen Maru Gothic', sans-serif; font-size: 1.1rem; }
.wrapped .logo { margin-top: 1rem; font-size: .7rem; letter-spacing: .3em; opacity: .7; text-transform: uppercase; }

/* z-indexはStreamlit Cloudのバッジ類より前面にする */
.st-key-bottomnav { position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: min(100vw, 640px); z-index: 2147483000; background: rgba(14, 17, 23, .97); backdrop-filter: blur(14px); border: 1px solid rgba(150, 160, 200, .18); border-bottom: none; border-radius: 20px 20px 0 0; padding: .3rem .5rem calc(.4rem + env(safe-area-inset-bottom)); }
.st-key-bottomnav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .3rem; }
.st-key-bottomnav [data-testid="stColumn"] { flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }
.st-key-bottomnav button { background: transparent !important; border: none !important; padding: .25rem 0 !important; min-height: 2.6rem; }
.st-key-bottomnav button p { font-size: 1.45rem !important; line-height: 1; }
.st-key-bottomnav button[kind="primary"] { background: linear-gradient(135deg, rgba(255,154,90,.22), rgba(143,94,255,.22)) !important; border-radius: 14px !important; }

/* リアクションボタンを小さく */
[class*="st-key-rxrow_"] button { padding: .1rem .4rem !important; min-height: 1.9rem; font-size: .8rem; border-radius: 999px !important; }
[class*="st-key-rxrow_"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .3rem; }
[class*="st-key-rxrow_"] [data-testid="stColumn"] { flex: 0 0 auto !important; min-width: 0 !important; width: auto !important; }

.login-logo { text-align: center; margin: 1.2rem 0 .2rem; }
.login-logo .big { font-size: 2.8rem; letter-spacing: .1em; }
.login-logo .cap { font-size: .85rem; opacity: .65; margin-top: .2rem; }

@media (max-width: 640px) {
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100%; width: 100%; min-width: 100%; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .stats.six { grid-template-columns: repeat(2, 1fr); }
  .hero-title { font-size: 1.7rem; }
  /* 固定ヘッダーの高さぶん上余白を確保（タイトルが隠れないように） */
  [data-testid="stMainBlockContainer"] { padding: 4rem .9rem 7rem; }
  .st-key-bottomnav [data-testid="stColumn"],
  [class*="st-key-rxrow_"] [data-testid="stColumn"],
  [class*="st-key-ctlrow_"] [data-testid="stColumn"],
  [class*="st-key-frow_"] [data-testid="stColumn"] { flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }
  [class*="st-key-rxrow_"] [data-testid="stColumn"] { flex: 0 0 auto !important; }
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


@st.cache_data(show_spinner=False)
def geocode(query):
    """Nominatimで場所名→座標。(lat, lon, 表示名) か None"""
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": query, "format": "json", "limit": 1},
                         headers={"User-Agent": "tabilog-prototype"}, timeout=10)
        d = r.json()
        if d:
            return float(d[0]["lat"]), float(d[0]["lon"]), d[0]["display_name"]
    except Exception:
        pass
    return None


def haversine_km(a_lat, a_lon, b_lat, b_lon):
    rl1, rl2 = math.radians(a_lat), math.radians(b_lat)
    dlat = math.radians(b_lat - a_lat)
    dlon = math.radians(b_lon - a_lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(rl1) * math.cos(rl2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


# ---------------------------------------------------------------- ユーザー管理
USER_DEFAULTS = {"avatar": None, "friends": [], "requests_in": [],
                 "default_visibility": "friends", "lang": "ja", "suggestions": []}


def load_users():
    users = {}
    for r in sb.table("users").select("*").execute().data:
        users[r["id"]] = {
            "name": r["name"], "salt": r["salt"], "pw": r["pw"],
            "avatar": r.get("avatar_url"),
            "default_visibility": r.get("default_visibility", "friends"),
            "lang": r.get("lang", "ja"),
            "friends": [], "requests_in": [], "suggestions": [],
        }
    for r in sb.table("friendships").select("*").execute().data:
        if r["user_a"] in users:
            users[r["user_a"]]["friends"].append(r["user_b"])
    for r in sb.table("friend_requests").select("*").execute().data:
        if r["to_user"] in users:
            users[r["to_user"]]["requests_in"].append(r["from_user"])
    for r in sb.table("suggestions").select("*").execute().data:
        if r["to_user"] in users:
            users[r["to_user"]]["suggestions"].append(r)
    return users


def hash_pw(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def avatar_html(user, name):
    if user and user.get("avatar"):
        return f'<img src="{user["avatar"]}">'
    return (name or "?")[0]


def upload_image(data, path):
    """画像を圧縮（長辺1280px・JPEG）してStorageへ。公開URLを返す"""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82)
    sb.storage.from_("photos").upload(path, buf.getvalue(),
                                      {"content-type": "image/jpeg", "upsert": "true"})
    return sb.storage.from_("photos").get_public_url(path)


# ---------------------------------------------------------------- 旅データ
TRIP_DEFAULTS = {"visibility": "default", "gap": None, "photo_rating": 0,
                 "capsule": False, "companions": [], "reactions": {}}

TRIP_FIELDS = ("id", "place", "country", "city", "lat", "lon", "visit_date",
               "expectation", "reality", "rating", "photo_rating", "gap",
               "status", "visibility", "capsule", "companions", "reactions")


def _row_to_trip(r):
    t = {k: r.get(k) for k in TRIP_FIELDS}
    t["photos"] = r.get("photo_urls") or []
    t["visit_date"] = str(t["visit_date"])
    for k, v in TRIP_DEFAULTS.items():
        if t.get(k) is None and k != "gap":
            t[k] = dict(v) if isinstance(v, dict) else (list(v) if isinstance(v, list) else v)
    return t


def _trip_to_row(t, owner=None):
    row = {k: t.get(k) for k in TRIP_FIELDS}
    row["photo_urls"] = t.get("photos", [])
    if owner:
        row["owner"] = owner
    return row


def load_trips(username):
    rows = sb.table("trips").select("*").eq("owner", username).execute().data
    return [_row_to_trip(r) for r in rows]


def load_all_trips():
    """全ユーザーの投稿を (trip, owner_uid) で返す"""
    return [(_row_to_trip(r), r["owner"])
            for r in sb.table("trips").select("*").execute().data]


def db_insert_trip(t, owner):
    sb.table("trips").insert(_trip_to_row(t, owner)).execute()


def db_update_trip(t):
    sb.table("trips").update(_trip_to_row(t)).eq("id", t["id"]).execute()


def db_delete_trip(trip_id):
    sb.table("trips").delete().eq("id", trip_id).execute()


def effective_visibility(trip, owner):
    v = trip.get("visibility", "default")
    return owner.get("default_visibility", "friends") if v == "default" else v


def can_see(trip, owner_uid, owner, viewer_uid, viewer):
    if owner_uid == viewer_uid:
        return True
    vis = effective_visibility(trip, owner)
    if vis == "public":
        return True
    return owner_uid in viewer.get("friends", [])


def toggle_reaction(owner_uid, trip_id, key, me_uid):
    """投稿へのリアクションをトグルして保存"""
    rows = sb.table("trips").select("reactions").eq("id", trip_id).execute().data
    if not rows:
        return
    rx = rows[0].get("reactions") or {}
    lst = rx.setdefault(key, [])
    if me_uid in lst:
        lst.remove(me_uid)
    else:
        lst.append(me_uid)
    sb.table("trips").update({"reactions": rx}).eq("id", trip_id).execute()
    if owner_uid == st.session_state.user:
        for t in st.session_state.trips:
            if t["id"] == trip_id:
                t["reactions"] = rx


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
                    st.session_state.cookie_action = uid
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
                    sb.table("users").insert({
                        "id": uid, "name": name, "salt": salt,
                        "pw": hash_pw(pw, salt), "lang": st.session_state.lang,
                    }).execute()
                    st.session_state.user = uid
                    st.session_state.cookie_action = uid
                    st.rerun()

    st.stop()


if "user" not in st.session_state:
    # クッキーから自動ログイン（更新してもログアウトされない）
    cookie_uid = None if _skip_cookie_login else parse_token(cookies.get(COOKIE_NAME))
    if cookie_uid and sb.table("users").select("id").eq("id", cookie_uid).execute().data:
        st.session_state.user = cookie_uid
    else:
        auth_gate()

USERS = load_users()
USER_ID = st.session_state.user
ME = USERS.get(USER_ID, dict(USER_DEFAULTS, name=USER_ID))
st.session_state.lang = ME.get("lang", st.session_state.lang)

if "trips" not in st.session_state:
    st.session_state.trips = load_trips(USER_ID)
trips = st.session_state.trips


# ---------------------------------------------------------------- 共通部品
STAR = lambda r: "★" * r + "☆" * (5 - r) if r else "—"
GAP_CHIP = {"up": ("chip-gap-up", "gap_up"), "even": ("chip-gap-even", "gap_even"),
            "down": ("chip-gap-down", "gap_down")}
REACTIONS = [("nice", "🌈"), ("lol", "😂"), ("helpful", "📝")]


def page_header(icon, title, sub=""):
    st.markdown(f"""
    <div class="page-head">
      <div class="ico">{icon}</div>
      <div><div class="t">{title}</div><div class="s">{sub}</div></div>
    </div>""", unsafe_allow_html=True)


def is_locked(t, owner_uid):
    """タイムカプセル封印中か（本人にも見せない）"""
    return t.get("capsule") and t["status"] == "planned"


def popup_html(t, owner_name=None):
    reality = t["reality"] or "—"
    expectation = "🔒" if t.get("capsule") and t["status"] == "planned" else t["expectation"]
    owner_line = f'<p style="margin:0 0 4px; font-size:12px; font-weight:bold; color:#805ad5;">👤 {owner_name}</p>' if owner_name else ""
    return f"""
    <div style="font-family:sans-serif; width:260px;">
      {owner_line}
      <h4 style="margin:0 0 4px;">{'✅' if t['status']=='visited' else '🗓️'} {t['place']}</h4>
      <p style="margin:0 0 6px; color:#888; font-size:12px;">{country_label(t['country'])}・{t['city']}｜{t['visit_date']}</p>
      <p style="margin:0; font-size:12px;"><b style="color:#2b6cb0;">{tr('expectation')}</b><br>{expectation}</p>
      <p style="margin:6px 0 0; font-size:12px;"><b style="color:#c05621;">{tr('reality')}</b><br>{reality}</p>
      <p style="margin:6px 0 0; font-size:13px;"><span style="color:#d69e2e;">{STAR(t['rating'])}</span></p>
    </div>"""


PIN_STYLE = {
    "my_visited": ("orange", "camera"),
    "my_planned": ("blue", "calendar"),
    "fr_visited": ("purple", "camera"),
    "fr_planned": ("pink", "calendar"),
}


def build_map(entries, height=440):
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


def all_visible_visited(exclude_trip_id=None):
    """自分が見られる全ユーザーの訪問済み投稿 (trip, owner_uid, owner)"""
    out = []
    for t, uid in load_all_trips():
        owner = USERS.get(uid)
        if not owner or t["status"] != "visited" or t["id"] == exclude_trip_id:
            continue
        if can_see(t, uid, owner, USER_ID, ME):
            out.append((t, uid, owner))
    return out


def reaction_row(t, owner_uid):
    rx = t.get("reactions", {})
    with st.container(key=f"rxrow_{t['id']}"):
        cols = st.columns(len(REACTIONS))
        for col, (key, emoji) in zip(cols, REACTIONS):
            users_r = rx.get(key, [])
            mine = USER_ID in users_r
            label = f"{emoji} {len(users_r)}" if users_r else emoji
            if col.button(label, key=f"rx_{t['id']}_{key}", help=tr(f"rx_{key}"),
                          type="primary" if mine else "secondary"):
                toggle_reaction(owner_uid, t["id"], key, USER_ID)
                st.rerun()


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
        if t.get("gap") in GAP_CHIP:
            cls, key = GAP_CHIP[t["gap"]]
            chips += f'<span class="chip {cls}">{tr(key)}</span>'
        if show_visibility:
            vis = effective_visibility(t, owner)
            chips += ('<span class="chip chip-pub">' + tr("vis_public_chip") + '</span>' if vis == "public"
                      else '<span class="chip chip-frd">' + tr("vis_friends_chip") + '</span>')

        head, stars = st.columns([3, 1])
        meta = f'🗓 {t["visit_date"]}　{chips}'
        comps = [USERS.get(c, {}).get("name", c) for c in t.get("companions", [])]
        if comps:
            meta += f'<br>👥 {", ".join(comps)} {tr("with_label")}'
        head.markdown(f'<p class="trip-title">{t["place"]}</p>'
                      f'<div class="trip-meta">{meta}</div>', unsafe_allow_html=True)
        if t["status"] == "visited":
            srows = f'🔁 {STAR(t["rating"])}'
            if t.get("photo_rating"):
                srows = f'📸 {STAR(t["photo_rating"])}<br>' + srows
            stars.markdown(f'<div class="trip-stars">{srows}</div>', unsafe_allow_html=True)

        exp_col, real_col = st.columns(2)
        with exp_col:
            st.markdown(f"**{tr('expectation')}**")
            if is_locked(t, owner_uid):
                st.info(tr("capsule_locked"))
            else:
                st.info(t["expectation"])
        with real_col:
            st.markdown(f"**{tr('reality')}**")
            if t["reality"]:
                st.warning(t["reality"])
            else:
                st.caption(tr("no_reality"))

        # 自分の計画中の旅 → 同じあたりに行った人の「現実」を事前チェック
        if owner_uid == USER_ID and t["status"] == "planned":
            with st.expander(tr("others_reality")):
                near = [(o_t, o_uid, o) for o_t, o_uid, o in all_visible_visited(t["id"])
                        if haversine_km(t["lat"], t["lon"], o_t["lat"], o_t["lon"]) <= 75]
                if not near:
                    st.caption(tr("no_others"))
                for o_t, o_uid, o in near:
                    st.markdown(f"**{o.get('name', o_uid)}** — {o_t['place']}　"
                                f"<span style='color:#f6ad55;'>{STAR(o_t['rating'])}</span>",
                                unsafe_allow_html=True)
                    st.caption(o_t["reality"] or "—")

        if owner_uid == USER_ID:
            ctl = st.container(key=f"ctlrow_{t['id']}")
            rx_col, del_col = ctl.columns([4, 1])
            with rx_col:
                reaction_row(t, owner_uid)
            with del_col:
                with st.popover(tr("delete")):
                    st.caption(tr("confirm_del"))
                    if st.button(tr("confirm_del_btn"), key=f"del_{t['id']}", type="primary",
                                 use_container_width=True):
                        db_delete_trip(t["id"])
                        st.session_state.trips = [x for x in st.session_state.trips
                                                  if x["id"] != t["id"]]
                        st.rerun()
        else:
            reaction_row(t, owner_uid)


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

    # 初回チュートリアル（まだ投稿がないとき）
    if not trips:
        st.markdown(f"""
        <div style="background: rgba(150,160,200,.08); border: 1px solid rgba(150,160,200,.18);
                    border-radius: 20px; padding: 1.3rem 1.4rem; margin-bottom: 1.1rem;">
          <div style="font-family:'Zen Maru Gothic',sans-serif; font-weight:900; font-size:1.25rem;">
            👋 {tr('tut_title')}</div>
          <div style="font-size:.82rem; opacity:.65; margin-bottom:.8rem;">{tr('tut_sub')}</div>
          <ol style="font-size:.88rem; line-height:1.9; padding-left:1.2rem; margin:0;">
            <li>{tr('tut_1')}</li><li>{tr('tut_2')}</li><li>{tr('tut_3')}</li>
          </ol>
          <div style="margin-top:.9rem; padding:.8rem 1rem; border-radius:14px;
                      background: rgba(143,94,255,.1); border:1px solid rgba(143,94,255,.25); font-size:.82rem;">
            <b>{tr('tut_example')}</b><br>{tr('tut_exp')}<br>{tr('tut_real')}
          </div>
        </div>""", unsafe_allow_html=True)

    # 旅程リマインド
    today = date.today()
    for t in trips:
        if t["status"] != "planned":
            continue
        try:
            d = date.fromisoformat(t["visit_date"])
        except ValueError:
            continue
        if 0 <= (d - today).days <= 7:
            st.info(tr("rem_soon").format(place=t["place"], date=t["visit_date"]))
        elif d < today:
            st.warning(tr("rem_overdue").format(place=t["place"]))

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

    # 足跡タイムラプス
    vis_dates = sorted({t["visit_date"] for t, cat, _ in entries if cat.endswith("visited")})
    if len(vis_dates) >= 2:
        with st.expander(tr("timelapse")):
            upto = st.select_slider("date", options=vis_dates, value=vis_dates[-1],
                                    label_visibility="collapsed")
            entries = [(t, cat, n) for t, cat, n in entries
                       if not cat.endswith("visited") or t["visit_date"] <= upto]
    build_map(entries)

# ---------- フィード ----------
elif page == "feed":
    page_header("📖", tr("feed_title"), tr("feed_sub"))
    scope = st.radio("scope", [tr("scope_friends"), tr("scope_discover")],
                     horizontal=True, label_visibility="collapsed")

    if scope == tr("scope_friends"):
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
        entries = []
        for t, uid in load_all_trips():
            owner = USERS.get(uid)
            if owner and effective_visibility(t, owner) == "public":
                entries.append((t, uid, owner))

    if not entries:
        st.info(tr("feed_empty"))
    for t, uid, owner in sorted(entries, key=lambda e: e[0]["visit_date"], reverse=True):
        feed_card(t, uid, owner, show_visibility=(uid == USER_ID))

# ---------- 投稿（事前登録） ----------
elif page == "add":
    page_header("🛫", tr("add_title"), tr("add_sub"))
    st.markdown(f"**{tr('pick_map')}**")

    # 場所名検索（ジオコーディング）
    with st.container(key="frow_geo"):
        g1, g2 = st.columns([3, 1])
        gq = g1.text_input("geo_q", placeholder=tr("search_place"), label_visibility="collapsed")
        if g2.button(tr("search_btn"), use_container_width=True):
            hit = geocode(gq) if gq else None
            if hit:
                st.session_state.pick_latlon = (hit[0], hit[1])
                st.session_state.pick_name = hit[2]
                st.rerun()
            else:
                st.error(tr("geocode_err"))
    if st.session_state.get("pick_name"):
        st.success(tr("geocode_ok") + st.session_state.pick_name)

    pick = folium.Map(location=st.session_state.get("pick_latlon", [25, 20]),
                      zoom_start=10 if "pick_latlon" in st.session_state else 1,
                      tiles="CartoDB positron")
    if "pick_latlon" in st.session_state:
        folium.Marker(st.session_state.pick_latlon, icon=folium.Icon(color="blue")).add_to(pick)
    out = st_folium(pick, height=320, use_container_width=True, key="pick_map")
    if out and out.get("last_clicked"):
        ll = (out["last_clicked"]["lat"], out["last_clicked"]["lng"])
        if st.session_state.get("pick_latlon") != ll:
            st.session_state.pick_latlon = ll
            st.session_state.pop("pick_name", None)
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
        capsule = st.checkbox(tr("capsule"))
        visibility = visibility_select()
        if st.form_submit_button(tr("submit_trip"), type="primary", use_container_width=True):
            if not (place and country and city and expectation and latlon):
                st.error(tr("err_missing"))
            else:
                new_trip = {
                    "id": str(uuid.uuid4()), "place": place, "country": country,
                    "city": city, "lat": latlon[0], "lon": latlon[1],
                    "visit_date": str(visit_date), "expectation": expectation,
                    "reality": "", "rating": 0, "photo_rating": 0, "gap": None,
                    "photos": [], "status": "planned", "visibility": visibility,
                    "capsule": capsule, "companions": [], "reactions": {},
                }
                db_insert_trip(new_trip, USER_ID)
                st.session_state.trips.append(new_trip)
                st.session_state.pop("pick_latlon", None)
                st.session_state.pop("pick_name", None)
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
        if is_locked(target, USER_ID):
            st.info(tr("capsule_locked"))
        else:
            st.markdown(f"> 🌈 **{tr('upd_past')}**: {target['expectation']}")
        with st.form("update_trip"):
            reality = st.text_area(tr("upd_reality"), height=140, placeholder=tr("upd_reality_ph"))
            gap = st.radio(tr("gap_label"), ["up", "even", "down"], index=1, horizontal=True,
                           format_func=lambda g: tr(f"gap_{g}"))
            photo_rating = st.slider(tr("rating_photo"), 1, 5, 3, format="%d ★")
            rating = st.slider(tr("rating_again"), 1, 5, 3, format="%d ★")
            friend_opts = ME.get("friends", [])
            companions = st.multiselect(tr("companions"), friend_opts,
                                        format_func=lambda f: USERS.get(f, {}).get("name", f)) if friend_opts else []
            photos = st.file_uploader(tr("photos"), type=["png", "jpg", "jpeg", "webp"],
                                      accept_multiple_files=True)
            visibility = visibility_select(current=target.get("visibility", "default"))
            if st.form_submit_button(tr("save_reality"), type="primary", use_container_width=True):
                if not reality:
                    st.error(tr("err_reality"))
                else:
                    was_capsule = is_locked(target, USER_ID)
                    target.update(reality=reality, rating=rating, photo_rating=photo_rating,
                                  gap=gap, companions=companions, status="visited",
                                  visibility=visibility)
                    target["photos"] = ([upload_image(p.getvalue(), f"{USER_ID}/{target['id']}/{i}.jpg")
                                         for i, p in enumerate(photos)] if photos else [])
                    db_update_trip(target)
                    st.success(f"「{target['place']}」{tr('updated')}")
                    if was_capsule:
                        st.info(f"{tr('capsule_open')}\n\n> {target['expectation']}")
                    st.balloons()

# ---------- プロフィール ----------
elif page == "profile":
    visited = [t for t in trips if t["status"] == "visited"]
    st.markdown(f"""
    <div class="prof">
      <div class="av">{avatar_html(ME, ME.get('name', USER_ID))}</div>
      <div><div class="nm">{ME.get('name', USER_ID)}</div><div class="id">@{USER_ID}</div></div>
    </div>""", unsafe_allow_html=True)

    tab_posts, tab_friends, tab_wrapped, tab_settings = st.tabs(
        [tr("tab_posts"), tr("tab_friends"), tr("tab_wrapped"), tr("tab_settings")])

    # 統計の共通計算
    def total_km(tl):
        v = sorted([t for t in tl if t["status"] == "visited"], key=lambda x: x["visit_date"])
        return sum(haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]) for a, b in zip(v, v[1:]))

    def gap_rate(tl):
        g = [t["gap"] for t in tl if t["status"] == "visited" and t.get("gap")]
        return round(100 * g.count("up") / len(g)) if g else None

    with tab_posts:
        km = total_km(trips)
        rate = gap_rate(trips)
        stats = [
            ("📸", f"{len(visited)}", tr("stat_posts")),
            ("🌍", f"{len({t['country'] for t in visited})}", tr("stat_c")),
            ("🏙️", f"{len({(t['country'], t['city']) for t in visited})}", tr("stat_ci")),
            ("🗓️", f"{len(trips) - len(visited)}", tr("stat_p")),
            ("🚀", f"{rate}<small>%</small>" if rate is not None else "—", tr("stat_gap")),
            ("🌐", f"{km:,.0f}<small> km</small>", tr("stat_dist")),
        ]
        st.markdown('<div class="stats six">' + "".join(
            f'<div class="stat"><div class="ico">{i}</div><div class="val">{v}</div><div class="lab">{l}</div></div>'
            for i, v, l in stats) + '</div>', unsafe_allow_html=True)
        if km > 0:
            st.caption("🌍 " + tr("earth_laps").format(laps=f"{km / 40075:.2f}"))

        all_photos = [ph for t in visited for ph in t["photos"]]
        st.markdown(f"**{tr('memories')}**")
        if all_photos:
            gcols = st.columns(3)
            for i, ph in enumerate(all_photos):
                gcols[i % 3].image(ph, use_container_width=True)
        else:
            st.caption(tr("no_photos"))

    with tab_friends:
        # 届いた旅のバトン
        suggestions = ME.get("suggestions", [])
        if suggestions:
            st.markdown(f"**{tr('baton_in')}**")
            for s in list(suggestions):
                su = USERS.get(s["from_user"], {})
                with st.container(border=True, key=f"frow_sug_{s['id']}"):
                    st.markdown(f"**{su.get('name', s['from_user'])}** {tr('baton_from')}: "
                                f"**{s['place']}**（{country_label(s['country'])}・{s['city']}）")
                    if s.get("note"):
                        st.caption(f"💬 {s['note']}")
                    c1, c2 = st.columns(2)
                    if c1.button(tr("baton_accept"), key=f"sug_ok_{s['id']}", type="primary",
                                 use_container_width=True):
                        new_trip = {
                            "id": str(uuid.uuid4()), "place": s["place"], "country": s["country"],
                            "city": s["city"], "lat": s["lat"], "lon": s["lon"],
                            "visit_date": str(date.today()),
                            "expectation": f"🎁 {su.get('name', s['from_user'])}: {s.get('note', '')}",
                            "reality": "", "rating": 0, "photo_rating": 0, "gap": None,
                            "photos": [], "status": "planned", "visibility": "default",
                            "capsule": False, "companions": [], "reactions": {},
                        }
                        db_insert_trip(new_trip, USER_ID)
                        st.session_state.trips.append(new_trip)
                        sb.table("suggestions").delete().eq("id", s["id"]).execute()
                        st.success(tr("baton_added"))
                        st.rerun()
                    if c2.button(tr("baton_decline"), key=f"sug_ng_{s['id']}", use_container_width=True):
                        sb.table("suggestions").delete().eq("id", s["id"]).execute()
                        st.rerun()
            st.divider()

        # フレンド申請（受信）
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
                        sb.table("friend_requests").delete().eq("from_user", rid).eq("to_user", USER_ID).execute()
                        sb.table("friendships").insert([
                            {"user_a": USER_ID, "user_b": rid},
                            {"user_a": rid, "user_b": USER_ID},
                        ]).execute()
                        st.rerun()
                    if c3.button(tr("decline"), key=f"dec_{rid}", use_container_width=True):
                        sb.table("friend_requests").delete().eq("from_user", rid).eq("to_user", USER_ID).execute()
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
                    sb.table("friend_requests").insert(
                        {"from_user": USER_ID, "to_user": target_id}).execute()
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
                    sb.table("friendships").delete().eq("user_a", USER_ID).eq("user_b", fid).execute()
                    sb.table("friendships").delete().eq("user_a", fid).eq("user_b", USER_ID).execute()
                    st.rerun()

        # 旅のバトンを送る
        if friends:
            st.divider()
            st.markdown(f"**{tr('baton_title')}**")
            with st.form("baton"):
                b_to = st.selectbox(tr("baton_to"), friends,
                                    format_func=lambda f: USERS.get(f, {}).get("name", f))
                b_place = st.text_input(tr("baton_place"), placeholder=tr("place_ph"))
                b_country = st.selectbox(tr("country"), list(COUNTRIES.keys()), index=None,
                                         placeholder=tr("country_ph"), format_func=country_label)
                b_city = st.text_input(tr("city"), placeholder=tr("city_ph"))
                b_note = st.text_area(tr("baton_note"), height=80)
                if st.form_submit_button(tr("baton_send"), type="primary", use_container_width=True):
                    if not (b_to and b_place and b_country and b_city):
                        st.error(tr("err_fill_all"))
                    else:
                        hit = geocode(f"{b_place}, {b_city}, {COUNTRIES.get(b_country, b_country)}") \
                              or geocode(f"{b_city}, {COUNTRIES.get(b_country, b_country)}")
                        if not hit:
                            st.error(tr("baton_geo_err"))
                        else:
                            sb.table("suggestions").insert({
                                "id": str(uuid.uuid4()), "from_user": USER_ID, "to_user": b_to,
                                "place": b_place, "country": b_country, "city": b_city,
                                "lat": hit[0], "lon": hit[1], "note": b_note or "",
                            }).execute()
                            st.success(tr("baton_sent"))

    with tab_wrapped:
        years = sorted({t["visit_date"][:4] for t in visited}, reverse=True)
        if not years:
            st.info(tr("wrapped_none"))
        else:
            year = st.selectbox(tr("wrapped_year"), years)
            yv = [t for t in visited if t["visit_date"].startswith(year)]
            if not yv:
                st.info(tr("wrapped_none"))
            else:
                rate = gap_rate(yv)
                km = total_km(yv)
                best = max(yv, key=lambda t: (t["rating"], t.get("photo_rating", 0)))
                cells = [
                    (len({t["country"] for t in yv}), tr("w_countries")),
                    (len({(t["country"], t["city"]) for t in yv}), tr("w_cities")),
                    (len(yv), tr("w_spots")),
                    (f"{rate}%" if rate is not None else "—", tr("w_gap")),
                ]
                st.markdown(f"""
                <div class="wrapped">
                  <div class="wt">✨ {tr('w_title').format(year=year)}</div>
                  <div class="grid">{"".join(f'<div class="cell"><div class="v">{v}</div><div class="k">{k}</div></div>' for v, k in cells)}</div>
                  <div class="best">🏆 {tr('w_best')}: <b>{best['place']}</b>（{country_label(best['country'])}）<br>
                  <span style="color:#ffd98a;">{STAR(best['rating'])}</span>　🌐 {km:,.0f} km {tr('w_dist')}</div>
                  <div class="logo">🧭 {tr('hero_title')}</div>
                </div>""", unsafe_allow_html=True)

    with tab_settings:
        st.markdown(f"**{tr('avatar')}**")
        av = st.file_uploader(tr("avatar_upload"), type=["png", "jpg", "jpeg", "webp"], key="avatar_up")
        vis_labels = {"public": tr("vis_public"), "friends": tr("vis_friends")}
        default_vis = st.radio(tr("default_vis"), ["friends", "public"],
                               index=0 if ME.get("default_visibility", "friends") == "friends" else 1,
                               format_func=lambda v: vis_labels[v], horizontal=True)
        lang_label = st.radio(tr("language"), ["日本語", "English"],
                              index=0 if st.session_state.lang == "ja" else 1, horizontal=True)
        if st.button(tr("save_settings"), type="primary", use_container_width=True):
            upd = {"default_visibility": default_vis,
                   "lang": "ja" if lang_label == "日本語" else "en"}
            if av is not None:
                upd["avatar_url"] = upload_image(av.getvalue(), f"avatars/{USER_ID}.jpg")
            sb.table("users").update(upd).eq("id", USER_ID).execute()
            st.session_state.lang = upd["lang"]
            st.success(tr("saved"))
            st.rerun()

        st.divider()
        if st.button(tr("logout"), use_container_width=True):
            st.session_state.cookie_action = "__remove__"
            for k in ("user", "trips", "page", "pick_latlon", "pick_name"):
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
