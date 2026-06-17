import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_lottie import st_lottie
import requests
import os
import plotly.express as px
import plotly.graph_objects as go

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Uzbek Sentiment Analysis", page_icon="", layout="wide")

TRANSLATIONS = {
    "O'zbekcha": {
        "title": "Uzbek Sentiment Analysis",
        "subtitle": "Matn, fayl va ijtimoiy tarmoqlar izohlarini sun'iy intellekt yordamida tahlil qilish",
        "tab_text": "📝 Matn tahlili",
        "tab_comments": "💬 Izohlar tahlili",
        "tab_history": "📜 Tarix",
        "yt_key": "YouTube API Key",
        "max_comm": "Max izohlar soni",
        "dark_mode": "🌙 Tun rejimi",
        "dark_mode_light": "☀️ Kun rejimi",
        "clear_hist": "🗑️ Tarixni tozalash",
        "analyze_btn": "Tahlil qilish",
        "comments_btn": "Izohlarni tahlil qilish",
        "text_placeholder": "Masalan: Bu mahsulot juda yaxshi edi!",
        "url_placeholder": "https://youtube.com/watch?v=... yoki https://t.me/...",
        "text_label": "Matn kiriting:",
        "url_label": "Post linkini kiriting:",
        "api_connected": "🟢 API ulangan",
        "api_disconnected": "🔴 API ulanmagan",
        "total_lbl": "Jami",
        "pos_lbl": "Ijobiy",
        "neg_lbl": "Salbiy",
        "neu_lbl": "Neytral",
        "top_comments": "Eng aniq izohlar:",
        "categories_title": "### Kategoriyalar bo'yicha izohlar",
        "download_csv": "CSV yuklab olish",
        "history_empty": "Hali tahlil qilinmagan. Izohlar tabiga o'ting.",
        "no_text_warn": "Matn kiriting!",
        "no_url_warn": "Havola kiriting!",
        "api_error": " API serveriga ulanib bo'lmadi!",
        "yt_detected": "▶ **YouTube** video aniqlandi",
        "yt_key_warn": " Sidebar'dan YouTube API key kiriting!",
        "analyzed": "ta izoh tahlil qilindi",
        "sentiment_dist": "Sentiment taqsimoti",
        "comments_count": "Izohlar soni",
        "yt_info": "Video izohlarini tahlil qiladi",
        "yt_info2": "• Sidebar'dan API key kiriting",
        "yt_info3": "• Max 2000 ta izoh",
        "confidence": "Ishonch",
        "expander_label": "ta izoh",
        "tg_key": "Telegram Bot Token",
        "tab_file": "📂 Fayl yuklash",
        "tg_detected": " **Telegram** kanal aniqlandi",
        "tg_key_warn": " Sidebar'dan Telegram Bot Token kiriting!",
        "tg_info": "Kanal yoki post izohlarini tahlil qiladi",
        "tg_info2": "• Post linkini kiriting",
        "file_upload_label": "CSV, JSON, TXT yoki DOCX fayl yuklang:",
        "file_analyze_btn": "Faylni tahlil qilish",
        "file_no_warn": "Fayl yuklang!",
        "file_success": "ta izoh tahlil qilindi",
        "file_max_comm": "Max izohlar (fayldan)",
        "url_platform_warn": "Faqat YouTube va Telegram havolalari qabul qilinadi!",
    },
    "Русский": {
        "title": "Uzbek Sentiment Analysis",
        "subtitle": "Анализ текстов, файлов и комментариев социальных сетей с помощью искусственного интеллекта",
        "tab_text": "📝 Анализ текста",
        "tab_comments": "💬 Анализ комментариев",
        "tab_history": "📜 История",
        "yt_key": "YouTube API Key",
        "max_comm": "Макс. количество",
        "dark_mode": "🌙 Тёмный режим",
        "dark_mode_light": "☀️ Светлый режим",
        "clear_hist": "🗑️ Очистить историю",
        "analyze_btn": "Анализировать",
        "comments_btn": "Анализировать комментарии",
        "text_placeholder": "Например: Этот продукт очень хороший!",
        "url_placeholder": "https://youtube.com/watch?v=... или https://t.me/...",
        "text_label": "Введите текст:",
        "url_label": "Введите ссылку на пост:",
        "api_connected": "🟢 API подключен",
        "api_disconnected": "🔴 API не подключен",
        "total_lbl": "Всего",
        "pos_lbl": "Позитив",
        "neg_lbl": "Негатив",
        "neu_lbl": "Нейтрал",
        "top_comments": "Самые точные комментарии:",
        "categories_title": "### Комментарии по категориям",
        "download_csv": " Скачать CSV",
        "history_empty": "Анализов ещё не было. Перейдите на вкладку комментариев.",
        "no_text_warn": "Введите текст!",
        "no_url_warn": "Введите ссылку!",
        "api_error": " Не удалось подключиться к API!",
        "yt_detected": "▶ **YouTube** видео обнаружено",
        "yt_key_warn": " Введите YouTube API key в настройках!",
        "analyzed": "комментариев проанализировано",
        "sentiment_dist": "Распределение тональности",
        "comments_count": "Количество комментариев",
        "yt_info": "Анализирует комментарии видео",
        "yt_info2": "• Введите API key в настройках",
        "yt_info3": "• Макс. 2000 комментариев",
        "confidence": "Уверенность",
        "expander_label": "комментариев",
        "tg_key": "Telegram Bot Token",
        "tab_file": "📂 Загрузить файл",
        "tg_detected": "Telegram канал обнаружен",
        "tg_key_warn": " Введите Telegram Bot Token в настройках!",
        "tg_info": "Анализ комментариев канала или поста",
        "tg_info2": "• Вставьте ссылку на пост",
        "file_upload_label": "Загрузите CSV, JSON, TXT или DOCX файл:",
        "file_analyze_btn": "Анализировать файл",
        "file_no_warn": "Загрузите файл!",
        "file_success": "комментариев проанализировано",
        "file_max_comm": "Макс. комментариев (из файла)",
        "url_platform_warn": "Принимаются только ссылки YouTube и Telegram!",
    },
    "English": {
        "title": "Uzbek Sentiment Analysis",
        "subtitle": "Analyzing texts, files and social media comments with artificial intelligence",
        "tab_text": "📝 Text Analysis",
        "tab_comments": "💬 Comments Analysis",
        "tab_history": "📜 History",
        "yt_key": "YouTube API Key",
        "max_comm": "Max comments",
        "dark_mode": "🌙 Dark Mode",
        "dark_mode_light": "☀️ Light Mode",
        "clear_hist": "🗑️ Clear History",
        "analyze_btn": "Analyze",
        "comments_btn": "Analyze Comments",
        "text_placeholder": "E.g.: This product was really great!",
        "url_placeholder": "https://youtube.com/watch?v=... or https://t.me/...",
        "text_label": "Enter text:",
        "url_label": "Enter post link:",
        "api_connected": "🟢 API Connected",
        "api_disconnected": "🔴 API Disconnected",
        "total_lbl": "Total",
        "pos_lbl": "Positive",
        "neg_lbl": "Negative",
        "neu_lbl": "Neutral",
        "top_comments": "Most confident comments:",
        "categories_title": "### Comments by Category",
        "download_csv": "Download CSV",
        "history_empty": "No analysis yet. Go to Comments tab.",
        "no_text_warn": "Please enter text!",
        "no_url_warn": "Please enter a link!",
        "api_error": " Could not connect to API server!",
        "yt_detected": "▶ **YouTube** video detected",
        "yt_key_warn": " Please enter YouTube API key in sidebar!",
        "analyzed": "comments analyzed",
        "sentiment_dist": "Sentiment Distribution",
        "comments_count": "Comment Count",
        "yt_info": "Analyzes video comments",
        "yt_info2": "• Enter API key in sidebar",
        "yt_info3": "• Up to 2000 comments",
        "confidence": "Confidence",
        "expander_label": "comments",
        "tg_key": "Telegram Bot Token",
        "tab_file": "📂 File Upload",
        "tg_detected": " **Telegram** channel detected",
        "tg_key_warn": " Please enter Telegram Bot Token in sidebar!",
        "tg_info": "Analyzes channel or post comments",
        "tg_info2": "• Enter post link",
        "file_upload_label": "Upload CSV, JSON, TXT or DOCX file:",
        "file_analyze_btn": "Analyze File",
        "file_no_warn": "Please upload a file!",
        "file_success": "comments analyzed",
        "file_max_comm": "Max comments (from file)",
        "url_platform_warn": "Only YouTube and Telegram links are accepted!",
    }
}

def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

lottie_ai = None

if 'history' not in st.session_state:
    st.session_state.history = []
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

COLORS = {"Positive": "#22c55e", "Negative": "#ef4444", "Neutral": "#94a3b8"}
EMOJI  = {"Positive": "", "Negative": "", "Neutral": ""}

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    lang_choice = st.selectbox("🌐 Til / Language", list(TRANSLATIONS.keys()))
    t = TRANSLATIONS[lang_choice]
    if lottie_ai:
        st_lottie(lottie_ai, height=130)
    else:
        st.title("")

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    yt_api_key = os.getenv('YOUTUBE_API_KEY', '')
    max_comments = st.slider(t['max_comm'], 20, 2000, 100, step=20)

    st.markdown("---")
    is_dark = st.session_state.get('theme', 'dark') == 'dark'
    theme_toggle = st.toggle(t['dark_mode_light'] if is_dark else t['dark_mode'], value=is_dark)
    if theme_toggle != is_dark:
        st.session_state.theme = 'dark' if theme_toggle else 'light'
        st.rerun()
    st.session_state.theme = 'dark' if theme_toggle else 'light'

    try:
        requests.get(f"{API_BASE}/health", timeout=2)
        st.success(t['api_connected'])
    except:
        st.error(t['api_disconnected'])

    if st.button(t['clear_hist']):
        st.session_state.history = []
        st.rerun()

# ── Tema ──────────────────────────────────────────────────────
bg = "#0f172a" if st.session_state.theme == 'dark' else "#f8fafc"
fg = "#f1f5f9" if st.session_state.theme == 'dark' else "#1e293b"
card_bg = "#1e293b" if st.session_state.theme == 'dark' else "#ffffff"

sidebar_bg = "#1e293b" if st.session_state.theme == 'dark' else "#f1f5f9"
sidebar_fg = "#f1f5f9" if st.session_state.theme == 'dark' else "#1e293b"
expander_fg = "#f1f5f9" if st.session_state.theme == 'dark' else "#1e293b"
img_filter = "invert(1)" if st.session_state.theme == 'dark' else "none"
blend_mode = "screen" if st.session_state.theme == 'dark' else "normal"

st.markdown(f"""
<style>
  /* ── Main app ── */
  .stApp {{ background:{bg} !important; color:{fg} !important; }}
  h1, h2, h3 {{ color:#3b82f6 !important; }}

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
    background:transparent !important;
  }}
  .stTabs [data-baseweb="tab"] {{
    color:{fg} !important;
    background:transparent !important;
  }}
  .stTabs [data-baseweb="tab"]:hover {{
    color:{fg} !important;
  }}
  .stTabs [aria-selected="true"] {{
    color:#3b82f6 !important;
  }}

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] > div:first-child {{
    background:{sidebar_bg} !important;
  }}
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] p,
  section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] div,
  section[data-testid="stSidebar"] small,
  section[data-testid="stSidebar"] .stMarkdown {{
    color:{sidebar_fg} !important;
  }}

  /* Sidebar input placeholder */
  section[data-testid="stSidebar"] input {{
    background:{card_bg} !important;
    color:{sidebar_fg} !important;
    border-color:#475569 !important;
  }}
  section[data-testid="stSidebar"] input::placeholder {{
    color:#94a3b8 !important;
    opacity:1 !important;
  }}
  section[data-testid="stSidebar"] input:focus {{
    border-color:#3b82f6 !important;
    box-shadow: 0 0 0 1px #3b82f6 !important;
  }}

  /* Sidebar selectbox */
  section[data-testid="stSidebar"] .stSelectbox > div > div {{
    background:{card_bg} !important;
    color:{sidebar_fg} !important;
    border-color:#475569 !important;
    cursor: pointer !important;
  }}
  section[data-testid="stSidebar"] .stSelectbox input {{
    pointer-events: none !important;
    caret-color: transparent !important;
    user-select: none !important;
    outline: none !important;
    box-shadow: none !important;
    border: none !important;
  }}
  section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] *:focus,
  section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] *:focus-visible,
  section[data-testid="stSidebar"] .stSelectbox [data-baseweb="input"] {{
    outline: none !important;
    box-shadow: none !important;
  }}
  section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div:last-child,
  section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div:last-child:hover {{
    background: transparent !important;
    border-radius: 0 !important;
    width: auto !important;
    cursor: pointer !important;
  }}

  /* ── Clear History button spacing ── */
  section[data-testid="stSidebar"] .stButton {{
    margin-top: 16px !important;
  }}
  section[data-testid="stSidebar"] .stButton > button {{
    background:{card_bg} !important;
    color:{sidebar_fg} !important;
    border: 1px solid #475569 !important;
    width: 100% !important;
  }}
  section[data-testid="stSidebar"] .stButton > button:hover {{
    background:#ef4444 !important;
    color:#ffffff !important;
    border-color:#ef4444 !important;
  }}

  /* ── Header background ── */
  header[data-testid="stHeader"] {{
    background:{bg} !important;
  }}

  /* ── Deploy tugmasi yonidagi Streamlit stikerni yashirish ── */
  [data-testid="stDeployButton"] img,
  [data-testid="stDeployButton"] svg image,
  [data-testid="stDeployButton"] > button > div:last-child,
  [data-testid="stDeployButton"] > button img,
  [data-testid="stDeployButton"] picture,
  .stDeployButton img,
  .stDeployButton picture {{
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    display: none !important;
  }}

  .viewerBadge_container__r5tak,
  .viewerBadge_link__qRIco,
  #stDecoration,
  [data-testid="stDecoration"],
  a[href*="streamlit.io"] img,
  a[href*="share.streamlit"] img {{
    display: none !important;
    visibility: hidden !important;
  }}

  /* ── Download / regular buttons ── */
  .stDownloadButton > button {{
    background:{card_bg} !important;
    color:{fg} !important;
    border: 1px solid #475569 !important;
  }}
  .stDownloadButton > button:hover {{
    background:#2563eb !important;
    color:#ffffff !important;
    border-color:#2563eb !important;
  }}
  .stDownloadButton > button:hover * {{
    color:#ffffff !important;
  }}
  .stButton > button:hover {{
    color:#ffffff !important;
  }}

  /* ── Expander ── */
  details summary {{
    color:{fg} !important;
    background:{card_bg} !important;
    border-radius:8px !important;
    padding: 8px 12px !important;
  }}
  details summary:hover,
  details summary:hover * {{
    color:{fg} !important;
    background:{card_bg} !important;
  }}
  details summary * {{
    color:{fg} !important;
  }}
  .streamlit-expanderHeader,
  .streamlit-expanderHeader * {{
    color:{fg} !important;
    background:{card_bg} !important;
  }}
  .streamlit-expanderHeader:hover,
  .streamlit-expanderHeader:hover * {{
    color:{fg} !important;
    background:{card_bg} !important;
  }}
  .streamlit-expanderContent {{
    background:{card_bg} !important;
    color:{fg} !important;
  }}

  /* ── Comment cards ── */
  .comment-card {{
    background:{card_bg} !important;
    border-radius:10px; padding:12px 16px; margin:6px 0;
    border-left:4px solid #3b82f6;
    color:{fg} !important;
  }}
  .comment-card * {{ color:{fg} !important; }}
  .pos {{ border-left-color:#22c55e !important }}
  .neg {{ border-left-color:#ef4444 !important }}
  .neu {{ border-left-color:#94a3b8 !important }}

  /* ── Badges ── */
  .badge {{ display:inline-block; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }}
  .badge-pos {{ background:#166534 !important; color:#86efac !important; }}
  .badge-neg {{ background:#7f1d1d !important; color:#fca5a5 !important; }}
  .badge-neu {{ background:#1e3a5f !important; color:#93c5fd !important; }}

  /* ── Main input fields ── */
  .stTextInput input, .stTextArea textarea {{
    background:{card_bg} !important;
    color:{fg} !important;
    border-color:#475569 !important;
    caret-color:#ffffff !important;
  }}
  .stTextInput input::placeholder, .stTextArea textarea::placeholder {{
    color:#94a3b8 !important;
  }}

  /* ── Dataframe ── */
  .stDataFrame {{ color:{fg} !important; }}

  /* ── Selectbox main + dropdown arrow ── */
  div[data-baseweb="select"] > div {{
    background:{card_bg} !important;
    color:{fg} !important;
    border-color:#475569 !important;
  }}
  div[data-baseweb="select"] svg {{
    fill:{fg} !important;
    color:{fg} !important;
  }}
  div[data-baseweb="select"] * {{
    color:{fg} !important;
  }}

  /* ── Sidebar selectbox arrow ── */
  section[data-testid="stSidebar"] div[data-baseweb="select"] svg {{
    fill:{sidebar_fg} !important;
  }}

  /* ── Metrics ── */
  [data-testid="stMetric"] {{
    color:{fg} !important;
  }}
  [data-testid="stMetric"] label,
  [data-testid="stMetricLabel"] p,
  [data-testid="stMetricLabel"] span,
  [data-testid="stMetricLabel"] div {{
    color:{fg} !important;
    opacity: 1 !important;
  }}
  [data-testid="stMetricValue"],
  [data-testid="stMetricValue"] div,
  [data-testid="stMetricValue"] span {{
    color:{fg} !important;
  }}
  [data-testid="stMetricDelta"] {{
    color:#22c55e !important;
  }}

  /* ── Chart titles ── */
  .js-plotly-plot .gtitle {{
    fill:{fg} !important;
  }}

  /* ── Input/textarea labels ── */
  .stTextArea label, .stTextArea label p,
  .stTextInput label, .stTextInput label p,
  label, label p {{
    color:{fg} !important;
    opacity:1 !important;
  }}

  /* ── Streamlit running indicator ── */
  [data-testid="stStatusWidget"] svg,
  [data-testid="stStatusWidget"] *,
  header [data-testid="stStatusWidget"] {{
    color:{fg} !important;
    fill:{fg} !important;
    stroke:{fg} !important;
  }}
  header {{
    background:{bg} !important;
  }}
  header * {{
    color:{fg} !important;
    fill:{fg} !important;
    stroke:{fg} !important;
  }}
  header svg path {{
    fill:{fg} !important;
    stroke:{fg} !important;
  }}
  header svg path[fill="none"] {{
    fill:none !important;
    stroke:{fg} !important;
  }}
  header svg {{
    stroke:none !important;
    outline:none !important;
    border:none !important;
  }}
  header svg > path:first-child {{
    stroke:none !important;
    fill:none !important;
  }}

  /* ── All remaining dark text ── */
  .stMarkdown p, .stMarkdown span, .stMarkdown div {{
    color:{fg} !important;
  }}
  p, span.css-10trblm {{
    color:{fg} !important;
  }}

  /* ── File Uploader dark mode ── */
  [data-testid="stFileUploader"] {{
    background:transparent !important;
  }}
  [data-testid="stFileUploaderDropzone"],
  [data-testid="stFileUploader"] section {{
    background:{bg} !important;
    border: 1px solid #475569 !important;
    border-radius: 8px !important;
  }}
  [data-testid="stFileUploaderDropzone"]:hover,
  [data-testid="stFileUploader"] section:hover {{
    border-color: #3b82f6 !important;
    background:{bg} !important;
  }}
  [data-testid="stFileUploaderDropzone"] *,
  [data-testid="stFileUploader"] section * {{
    background:transparent !important;
    color:{fg} !important;
  }}
  [data-testid="stFileUploaderDropzone"] button,
  [data-testid="stFileUploader"] section button {{
    background:#1e40af !important;
    color:#ffffff !important;
    border: none !important;
    border-radius: 6px !important;
  }}
  [data-testid="stFileUploaderDropzone"] button:hover,
  [data-testid="stFileUploader"] section button:hover {{
    background:#2563eb !important;
  }}
  [data-testid="stFileUploaderDropzone"] button *,
  [data-testid="stFileUploader"] section button * {{
    background:transparent !important;
    color:#ffffff !important;
  }}
  [data-testid="stFileUploader"] label,
  [data-testid="stFileUploader"] label p {{
    color:{fg} !important;
  }}
  [data-testid="stFileUploaderFile"] {{
    background:{bg} !important;
    color:{fg} !important;
  }}
  [data-testid="stFileUploaderFile"] * {{
    color:{fg} !important;
  }}
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1 style='font-size:3rem;text-align:center;margin-bottom:0'>{t['title']}</h1>", unsafe_allow_html=True)

# Force file uploader dark mode via JS
st.markdown(f"""
<script>
function fixFileUploader() {{
  var zones = document.querySelectorAll(
    '[data-testid="stFileUploaderDropzone"], ' +
    '[data-testid="stFileUploader"] section, ' +
    '[data-testid="stFileUploader"] > div'
  );
  zones.forEach(function(el) {{
    el.style.setProperty('background', '{bg}', 'important');
    el.style.setProperty('border', '1px solid #475569', 'important');
    el.style.setProperty('border-radius', '8px', 'important');
  }});

  var allInner = document.querySelectorAll(
    '[data-testid="stFileUploaderDropzone"] *, ' +
    '[data-testid="stFileUploader"] section *'
  );
  allInner.forEach(function(child) {{
    var tag = child.tagName ? child.tagName.toLowerCase() : '';
    if (tag === 'button') {{
      child.style.setProperty('background', '#1e40af', 'important');
      child.style.setProperty('color', '#ffffff', 'important');
      child.style.setProperty('border', 'none', 'important');
      child.style.setProperty('border-radius', '6px', 'important');
    }} else if (tag === 'span' || tag === 'p' || tag === 'small' || tag === 'div') {{
      child.style.setProperty('background', 'transparent', 'important');
      child.style.setProperty('color', '{fg}', 'important');
    }} else {{
      child.style.setProperty('background', 'transparent', 'important');
    }}
  }});

  var btnSpans = document.querySelectorAll(
    '[data-testid="stFileUploaderDropzone"] button span, ' +
    '[data-testid="stFileUploader"] section button span, ' +
    '[data-testid="stFileUploader"] section button *'
  );
  btnSpans.forEach(function(s) {{
    s.style.setProperty('color', '#ffffff', 'important');
    s.style.setProperty('background', 'transparent', 'important');
  }});
}}
setTimeout(fixFileUploader, 300);
setTimeout(fixFileUploader, 800);
setTimeout(fixFileUploader, 2000);
var observer = new MutationObserver(function() {{ fixFileUploader(); }});
observer.observe(document.body, {{ childList: true, subtree: true }});
</script>
""", unsafe_allow_html=True)
st.markdown(t['subtitle'])

tab1, tab2, tab3, tab4 = st.tabs([t['tab_text'], t['tab_comments'], t['tab_file'], t['tab_history']])

# ── TAB 1: MATN ───────────────────────────────────────────────
with tab1:
    user_input = st.text_area(t['text_label'], height=130, placeholder=t['text_placeholder'])
    if st.button(t['analyze_btn'], key="txt", type="primary"):
        if user_input.strip():
            with st.spinner("" + t['analyze_btn'] + "..."):
                try:
                    res = requests.post(f"{API_BASE}/analyze-text",
                                        json={"text": user_input}, timeout=30)
                    res.raise_for_status()
                    d = res.json()["result"]
                    lbl = d["label"]
                    badge_cls = {"Positive":"badge-pos","Negative":"badge-neg","Neutral":"badge-neu"}[lbl]
                    css_cls = {"Positive":"pos","Negative":"neg","Neutral":"neu"}[lbl]
                    st.markdown(f"""
                    <div class="comment-card {css_cls}">
                      <span class="badge {badge_cls}">{lbl}</span>
                      <b style="margin-left:10px">{t['confidence']}: {d['confidence']*100:.1f}%</b>
                      <p style="margin-top:8px;opacity:.8">{user_input[:200]}</p>
                    </div>""", unsafe_allow_html=True)
                    st.session_state.history.append({
                        "Vaqt": datetime.now().strftime("%H:%M"),
                        "Tur": t['tab_text'], "Manba": user_input[:50],
                        "Natija": lbl, "Ishonch": f"{d['confidence']*100:.1f}%"
                    })
                except requests.exceptions.ConnectionError:
                    st.error(t['api_error'])
                except Exception as e:
                    st.error(f"Xatolik: {e}")
        else:
            st.warning(t['no_text_warn'])

# ── TAB 2: IZOHLAR ────────────────────────────────────────────
with tab2:
    col_yt, col_tg = st.columns(2)
    with col_yt:
        st.markdown(f"""<div class="comment-card">
          <b>YouTube</b><br>
          <small>{t['yt_info']}</small><br>
          <small>{t['yt_info3']}</small>
        </div>""", unsafe_allow_html=True)
    with col_tg:
        st.markdown(f"""<div class="comment-card">
          <b>Telegram</b><br>
          <small>{t['tg_info']}</small><br>
          <small>{t['tg_info2']}</small>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    url_input = st.text_input(t['url_label'], placeholder=t['url_placeholder'])

    if url_input:
        u = url_input.lower()
        if "youtube" in u or "youtu.be" in u:
            st.info(t['yt_detected'])
        elif "t.me" in u or "telegram.me" in u:
            st.info(t['tg_detected'])

    if st.button(t['comments_btn'], key="comments", type="primary"):
        if not url_input.strip():
            st.warning(t['no_url_warn'])
        elif not any(x in url_input.lower() for x in ["youtube", "youtu.be", "t.me", "telegram.me"]):
            st.warning(t['url_platform_warn'])
        else:
            with st.spinner("" + t['comments_btn'] + "..."):
                try:
                    payload = {
                        "url": url_input,
                        "youtube_api_key": yt_api_key or None,
                        "max_comments": max_comments
                    }
                    res = requests.post(f"{API_BASE}/analyze-comments", json=payload, timeout=180)
                    if res.status_code in (400, 422):
                        st.error(f" {res.json().get('detail', 'Xatolik')}")
                    else:
                        res.raise_for_status()
                        d = res.json()["result"]
                        platform = d["platform"]
                        counts = d["counts"]
                        pcts = d["percentages"]
                        total = d["total"]
                        icon = {"YouTube": "▶", "Telegram": ""}.get(platform, "")
                        st.success(f"{icon} **{d.get('title', platform)}** — {total} {t['analyzed']}")

                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric(t['total_lbl'], total)
                        c2.metric(t['pos_lbl'], counts.get("Positive", 0), f"{pcts.get('Positive', 0)}%")
                        c3.metric(t['neg_lbl'], counts.get("Negative", 0), f"{pcts.get('Negative', 0)}%")
                        c4.metric(t['neu_lbl'], counts.get("Neutral", 0), f"{pcts.get('Neutral', 0)}%")

                        col_chart1, col_chart2 = st.columns(2)
                        with col_chart1:
                            fig_pie = go.Figure(go.Pie(
                                labels=list(counts.keys()), values=list(counts.values()),
                                hole=0.45, marker_colors=[COLORS[k] for k in counts.keys()],
                                textinfo="label+percent"))
                            fig_pie.update_layout(title=t['sentiment_dist'],
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#f1f5f9", height=300, margin=dict(t=40,b=0), legend=dict(font=dict(color="#f1f5f9")))
                            st.plotly_chart(fig_pie, use_container_width=True)

                        with col_chart2:
                            fig_bar = go.Figure(go.Bar(
                                x=list(counts.keys()), y=list(counts.values()),
                                marker_color=[COLORS[k] for k in counts.keys()],
                                text=[f"{pcts[k]}%" for k in counts.keys()], textposition="outside"))
                            fig_bar.update_layout(title=t['comments_count'],
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#f1f5f9", height=300, margin=dict(t=40,b=0),
                                yaxis=dict(gridcolor="#334155"))
                            st.plotly_chart(fig_bar, use_container_width=True)

                        st.markdown("---")
                        st.markdown(t['categories_title'])

                        for sentiment, css_cls, badge_cls in [
                            ("Positive", "pos", "badge-pos"),
                            ("Negative", "neg", "badge-neg"),
                            ("Neutral",  "neu", "badge-neu"),
                        ]:
                            items = d["categories"][sentiment]
                            if not items: continue
                            with st.expander(f"{sentiment} — {len(items)} {t['expander_label']}", expanded=(sentiment=="Positive")):
                                df_cat = pd.DataFrame(items)
                                st.dataframe(df_cat, use_container_width=True, hide_index=True)
                                st.markdown(f"**{t['top_comments']}**")
                                for item in sorted(items, key=lambda x: -x["confidence"])[:5]:
                                    st.markdown(f"""<div class="comment-card {css_cls}">
                                      <span class="badge {badge_cls}">{sentiment}</span>
                                      <span style="opacity:.6;font-size:12px;margin-left:8px">{item['confidence']*100:.1f}%</span>
                                      <p style="margin:6px 0 0;font-size:14px">{item['text']}</p>
                                    </div>""", unsafe_allow_html=True)
                                csv = df_cat.to_csv(index=False).encode()
                                st.download_button(f" {sentiment} {t['download_csv']}",
                                    csv, f"{sentiment.lower()}_comments.csv", "text/csv", key=f"dl_{sentiment}")

                        st.session_state.history.append({
                            "Vaqt": datetime.now().strftime("%H:%M"),
                            "Tur": platform, "Manba": url_input[:60],
                            "Jami": total, "Ijobiy": counts.get("Positive", 0),
                            "Salbiy": counts.get("Negative", 0), "Neytral": counts.get("Neutral", 0),
                        })
                except requests.exceptions.ConnectionError:
                    st.error(t['api_error'])
                except Exception as e:
                    st.error(f"Xatolik: {e}")

# ── TAB 3: FAYL YUKLASH ───────────────────────────────────────
with tab3:

    uploaded_file = st.file_uploader(
        t['file_upload_label'],
        type=["csv", "json", "txt", "docx", "doc"],
        help="Max 10MB"
    )
    file_max = st.slider(t['file_max_comm'], 20, 2000, 500, step=20)

    if st.button(t['file_analyze_btn'], key="file_btn", type="primary"):
        if uploaded_file is None:
            st.warning(t['file_no_warn'])
        else:
            with st.spinner("" + t['file_analyze_btn'] + "..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data_form = {"max_comments": file_max}
                    res = requests.post(f"{API_BASE}/analyze-file", files=files, data=data_form, timeout=300)
                    if res.status_code in (400, 422):
                        st.error(f" {res.json().get('detail', 'Xatolik')}")
                    else:
                        res.raise_for_status()
                        d = res.json()["result"]
                        counts = d["counts"]
                        pcts = d["percentages"]
                        total = d["total"]
                        st.success(f" **{d.get('title', uploaded_file.name)}** — {total} {t['file_success']}")

                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric(t['total_lbl'], total)
                        c2.metric(t['pos_lbl'], counts.get("Positive", 0), f"{pcts.get('Positive', 0)}%")
                        c3.metric(t['neg_lbl'], counts.get("Negative", 0), f"{pcts.get('Negative', 0)}%")
                        c4.metric(t['neu_lbl'], counts.get("Neutral", 0), f"{pcts.get('Neutral', 0)}%")

                        col_chart1, col_chart2 = st.columns(2)
                        with col_chart1:
                            fig_pie = go.Figure(go.Pie(
                                labels=list(counts.keys()), values=list(counts.values()),
                                hole=0.45, marker_colors=[COLORS[k] for k in counts.keys()],
                                textinfo="label+percent"))
                            fig_pie.update_layout(title=t['sentiment_dist'],
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#f1f5f9", height=300, margin=dict(t=40,b=0), legend=dict(font=dict(color="#f1f5f9")))
                            st.plotly_chart(fig_pie, use_container_width=True)

                        with col_chart2:
                            fig_bar = go.Figure(go.Bar(
                                x=list(counts.keys()), y=list(counts.values()),
                                marker_color=[COLORS[k] for k in counts.keys()],
                                text=[f"{pcts[k]}%" for k in counts.keys()], textposition="outside"))
                            fig_bar.update_layout(title=t['comments_count'],
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#f1f5f9", height=300, margin=dict(t=40,b=0),
                                yaxis=dict(gridcolor="#334155"))
                            st.plotly_chart(fig_bar, use_container_width=True)

                        st.markdown("---")
                        st.markdown(t['categories_title'])

                        for sentiment, css_cls, badge_cls in [
                            ("Positive", "pos", "badge-pos"),
                            ("Negative", "neg", "badge-neg"),
                            ("Neutral",  "neu", "badge-neu"),
                        ]:
                            items = d["categories"][sentiment]
                            if not items: continue
                            with st.expander(f"{sentiment} — {len(items)} {t['expander_label']}", expanded=(sentiment=="Positive")):
                                df_cat = pd.DataFrame(items)
                                st.dataframe(df_cat, use_container_width=True, hide_index=True)
                                st.markdown(f"**{t['top_comments']}**")
                                for item in sorted(items, key=lambda x: -x["confidence"])[:5]:
                                    st.markdown(f"""<div class="comment-card {css_cls}">
                                      <span class="badge {badge_cls}">{sentiment}</span>
                                      <span style="opacity:.6;font-size:12px;margin-left:8px">{item['confidence']*100:.1f}%</span>
                                      <p style="margin:6px 0 0;font-size:14px">{item['text']}</p>
                                    </div>""", unsafe_allow_html=True)
                                csv_dl = df_cat.to_csv(index=False).encode()
                                st.download_button(f" {sentiment} {t['download_csv']}",
                                    csv_dl, f"{sentiment.lower()}_file_comments.csv", "text/csv", key=f"fdl_{sentiment}")

                        st.session_state.history.append({
                            "Vaqt": datetime.now().strftime("%H:%M"),
                            "Tur": "File", "Manba": uploaded_file.name,
                            "Jami": total, "Ijobiy": counts.get("Positive", 0),
                            "Salbiy": counts.get("Negative", 0), "Neytral": counts.get("Neutral", 0),
                        })
                except requests.exceptions.ConnectionError:
                    st.error(t['api_error'])
                except Exception as e:
                    st.error(f"Xatolik: {e}")

# ── TAB 4: TARIX ──────────────────────────────────────────────
with tab4:
    if st.session_state.history:
        df_hist = pd.DataFrame(st.session_state.history)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
        csv = df_hist.to_csv(index=False).encode()
        st.download_button(t['download_csv'], csv, "history.csv", "text/csv")
    else:
        st.info(t['history_empty'])