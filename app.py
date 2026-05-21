import re
import time
import random
import sqlite3
import hashlib
import html
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    AI_SEMANTIC_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    AI_SEMANTIC_AVAILABLE = False

# LinkedIn Jobs Hunter — v9.2 — Hybrid AI Search
st.set_page_config(page_title="Jobs Hunter", page_icon="🔎", layout="wide")
DB_PATH = Path.home() / ".jobs_hunter.db"
def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()
def esc_text(value):
    return html.escape(str(value or ""), quote=False)
def esc_attr(value):
    return html.escape(str(value or ""), quote=True)
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_id     TEXT PRIMARY KEY,
            title      TEXT,
            company    TEXT,
            url        TEXT,
            first_seen TEXT NOT NULL,
            hidden     INTEGER NOT NULL DEFAULT 0
        )
    """)
    return conn
def db_get_seen_ids():
    with db_conn() as c:
        return {row[0] for row in c.execute("SELECT job_id FROM seen_jobs WHERE hidden=1")}
def db_mark_seen(jobs, hide=True):
    if not jobs:
        return
    now = utc_now_iso()
    with db_conn() as c:
        c.executemany(
            """INSERT INTO seen_jobs(job_id, title, company, url, first_seen, hidden)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(job_id) DO UPDATE SET hidden=excluded.hidden""",
            [(j["Job ID"], j.get("Title", ""), j.get("Company", ""),
              j.get("URL", ""), now, 1 if hide else 0) for j in jobs]
        )
def db_clear_seen():
    with db_conn() as c:
        c.execute("DELETE FROM seen_jobs")
def db_seen_count():
    with db_conn() as c:
        return c.execute("SELECT COUNT(*) FROM seen_jobs WHERE hidden=1").fetchone()[0]
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,700&family=Outfit:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp {
    background: linear-gradient(160deg, #ddeeff 0%, #c8e4fb 50%, #b8d8f2 100%) !important;
    font-family: 'Outfit', sans-serif !important; color: #062040 !important;
}
.stApp::before {
    content: ''; position: fixed; inset: 0;
    background: radial-gradient(ellipse 70% 50% at 5% 0%, rgba(79,168,232,0.22) 0%, transparent 55%),
                radial-gradient(ellipse 55% 45% at 95% 100%, rgba(26,107,181,0.16) 0%, transparent 55%);
    pointer-events: none; z-index: 0;
}
.block-container { padding: 28px 44px 56px !important; max-width: 1240px !important; position: relative; z-index: 1; }
#MainMenu, footer, header { visibility: hidden; }
.hero {
    background: rgba(255,255,255,0.68); border: 1.5px solid rgba(184,212,236,0.9); border-radius: 28px;
    padding: 38px 42px; margin: 8px 0 28px;
    box-shadow: 0 4px 6px rgba(26,107,181,0.05), 0 24px 60px rgba(26,107,181,0.10), inset 0 1px 0 rgba(255,255,255,0.95);
    backdrop-filter: blur(20px); position: relative; overflow: hidden;
}
.hero::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #4fa8e8, #1a6bb5, #6ac4f8); border-radius: 28px 28px 0 0;
}
.hero-eyebrow {
    font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase;
    color: #1a6bb5; margin-bottom: 14px; font-weight: 600;
    display: flex; align-items: center; gap: 8px;
}
.hero-eyebrow::before {
    content: ''; display: inline-block; width: 6px; height: 6px;
    border-radius: 50%; background: #4fa8e8;
    box-shadow: 0 0 7px #4fa8e8; animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100% {opacity:1;} 50% {opacity:0.35;} }
.hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(38px, 5vw, 64px);
    font-weight: 700; letter-spacing: -0.025em; line-height: 1.0;
    color: #062040; margin-bottom: 16px;
}
.hero-title em { font-style: italic; color: #1a6bb5; }
.hero-sub { font-size: 15px; font-weight: 300; color: #6a8caa; max-width: 600px; line-height: 1.65; }
.slabel { font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: #6a8caa; display: block; margin: 26px 0 14px; font-weight: 600; }
.sdivider { border: none; border-top: 1px solid rgba(184,212,236,0.7); margin: 24px 0; }
.kw-banner { background: rgba(255,255,255,0.65); border: 1.5px solid rgba(184,212,236,0.8); border-radius: 16px; padding: 16px 20px 14px; margin: 10px 0 8px; }
.kw-banner-label { font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: #1a6bb5; margin-bottom: 10px; font-weight: 600; }
p, label, .stMarkdown p { color: #2a4a6a !important; font-size: 14px !important; }
h1, h2, h3 { color: #062040 !important; }

.stTextInput input, .stTextArea textarea {
    background: #ffffff !important;
    border: 1.5px solid #b8d4ec !important;
    border-radius: 12px !important;
    color: #062040 !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    caret-color: #1a6bb5 !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #1a6bb5 !important;
    box-shadow: 0 0 0 3px rgba(26,107,181,0.12) !important;
    outline: none !important;
}
.stTextInput > div, .stTextArea > div,
.stTextInput > div > div, .stTextArea > div > div {
    background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #90aec8 !important; }

.stTextInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label,
.stSlider label, .stCheckbox label {
    font-size: 10px !important; letter-spacing: 0.14em !important; text-transform: uppercase !important;
    color: #6a8caa !important; font-weight: 600 !important;
}

.stSelectbox > div, .stSelectbox > div > div, .stSelectbox > div > div > div,
.stMultiSelect > div, .stMultiSelect > div > div, .stMultiSelect > div > div > div {
    background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important;
}
.stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="select"] {
    background: #ffffff !important; border: 1.5px solid #b8d4ec !important; border-radius: 12px !important;
    min-height: 46px !important; font-size: 14px !important; color: #062040 !important;
    transition: border-color 0.18s !important;
}
.stSelectbox [data-baseweb="select"]:focus-within, .stMultiSelect [data-baseweb="select"]:focus-within {
    border-color: #1a6bb5 !important; box-shadow: 0 0 0 3px rgba(26,107,181,0.12) !important;
}
.stSelectbox [data-baseweb="select"] > div, .stMultiSelect [data-baseweb="select"] > div {
    background: transparent !important; border: none !important; color: #062040 !important;
}
.stSelectbox [data-baseweb="select"] svg, .stMultiSelect [data-baseweb="select"] svg {
    fill: #6a8caa !important; color: #6a8caa !important;
}
[data-baseweb="popover"] {
    background: #ffffff !important; border: 1.5px solid #b8d4ec !important;
    border-radius: 12px !important; box-shadow: 0 8px 28px rgba(26,107,181,0.12) !important;
}
[data-baseweb="menu"] { background: #ffffff !important; border-radius: 12px !important; }
[data-baseweb="option"] {
    background: #ffffff !important; color: #062040 !important; font-size: 14px !important; padding: 10px 16px !important;
}
[data-baseweb="option"]:hover, [data-baseweb="option"][aria-selected="true"] {
    background: rgba(26,107,181,0.08) !important; color: #062040 !important;
}
.stMultiSelect [data-baseweb="select"] input { color: #062040 !important; background: transparent !important; font-size: 14px !important; }
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(26,107,181,0.10) !important;
    border: 1.5px solid rgba(26,107,181,0.28) !important;
    color: #0f4f8c !important; font-size: 12px !important; font-weight: 600 !important;
    border-radius: 999px !important; padding: 3px 10px !important;
}
.stMultiSelect [data-baseweb="tag"] span { color: #0f4f8c !important; }
.stMultiSelect [data-baseweb="tag"] svg { fill: #1a6bb5 !important; }

.stRadio > div { display: flex !important; flex-wrap: wrap !important; gap: 10px !important; padding: 2px 0 !important; }
.stRadio label {
    background: rgba(255,255,255,0.62) !important;
    border: 1.5px solid rgba(184,212,236,0.85) !important;
    border-radius: 999px !important; padding: 9px 20px !important;
    color: #2a4a6a !important; cursor: pointer !important;
    transition: all 0.18s ease !important; backdrop-filter: blur(8px) !important;
}
.stRadio label *, .stRadio label p, .stRadio label span, .stRadio label div {
    color: #2a4a6a !important; font-size: 13px !important; font-weight: 500 !important;
}
.stRadio label:has(input:checked) {
    background: #1a6bb5 !important; border-color: #1a6bb5 !important;
    color: #ffffff !important; box-shadow: 0 6px 20px rgba(26,107,181,0.28) !important;
}
.stRadio label:has(input:checked) *, .stRadio label:has(input:checked) p,
.stRadio label:has(input:checked) span, .stRadio label:has(input:checked) div { color: #ffffff !important; }
.stRadio label input[type="radio"] { display: none !important; }

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4fa8e8 0%, #1a6bb5 60%, #0f4f8c 100%) !important;
    color: #ffffff !important; border: none !important; border-radius: 30px !important;
    padding: 16px 32px !important; font-weight: 700 !important; font-size: 15px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 8px 32px rgba(26,107,181,0.32) !important;
    transition: all 0.18s ease !important; width: 100% !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 14px 40px rgba(26,107,181,0.42) !important;
}
.stButton > button:not([kind="primary"]), .stDownloadButton > button {
    background: rgba(255,255,255,0.7) !important; color: #1a6bb5 !important;
    border: 1.5px solid rgba(184,212,236,0.9) !important; border-radius: 14px !important;
    font-weight: 600 !important; padding: 12px 18px !important; width: 100% !important;
    backdrop-filter: blur(8px) !important; transition: all 0.18s !important;
}
.stButton > button:not([kind="primary"]):hover, .stDownloadButton > button:hover {
    background: #1a6bb5 !important; color: #ffffff !important; border-color: #1a6bb5 !important;
}

.stSlider > div > div > div > div { background: #1a6bb5 !important; }
.stCheckbox label { color: #2a4a6a !important; text-transform: none !important; letter-spacing: normal !important; font-size: 13px !important; font-weight: 400 !important; }

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.68) !important;
    border: 1.5px solid rgba(184,212,236,0.8) !important;
    border-radius: 18px !important; padding: 22px !important;
    box-shadow: 0 8px 28px rgba(26,107,181,0.08) !important; backdrop-filter: blur(16px) !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 10px !important; letter-spacing: 0.14em !important; text-transform: uppercase !important;
    color: #6a8caa !important; font-weight: 600 !important;
}
div[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 38px !important; font-weight: 700 !important;
    color: #062040 !important; letter-spacing: -0.03em !important;
}

.streamlit-expanderHeader {
    background: rgba(255,255,255,0.62) !important;
    border: 1.5px solid rgba(184,212,236,0.8) !important;
    border-radius: 14px !important; color: #2a4a6a !important;
    padding: 14px 20px !important; backdrop-filter: blur(10px) !important;
}
.streamlit-expanderContent {
    background: rgba(255,255,255,0.58) !important;
    border: 1.5px solid rgba(184,212,236,0.7) !important;
    border-top: none !important; border-radius: 0 0 14px 14px !important;
    padding: 22px !important; backdrop-filter: blur(10px) !important;
}

div[data-testid="stAlert"] {
    border-radius: 14px !important;
    border: 1.5px solid rgba(184,212,236,0.7) !important;
    backdrop-filter: blur(8px) !important;
}

.stDataFrame {
    border-radius: 16px !important;
    border: 1.5px solid rgba(184,212,236,0.8) !important;
    overflow: hidden !important;
    box-shadow: 0 12px 36px rgba(26,107,181,0.08) !important;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, #4fa8e8, #1a6bb5) !important;
    border-radius: 999px !important;
}

.job-card {
    background: rgba(255,255,255,0.68);
    border: 1.5px solid rgba(184,212,236,0.85);
    border-radius: 20px; padding: 22px 26px; margin-bottom: 12px;
    box-shadow: 0 8px 28px rgba(26,107,181,0.07);
    backdrop-filter: blur(14px);
    transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
    position: relative; overflow: hidden;
}
.job-card::before {
    content: ''; position: absolute; top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #4fa8e8, #1a6bb5);
    border-radius: 20px 0 0 20px; opacity: 0; transition: opacity 0.18s;
}
.job-card:hover {
    border-color: rgba(26,107,181,0.45); transform: translateY(-2px);
    box-shadow: 0 16px 44px rgba(26,107,181,0.14);
}
.job-card:hover::before { opacity: 1; }

.job-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 20px; font-weight: 700; color: #062040;
    margin-bottom: 6px; letter-spacing: -0.01em; line-height: 1.2;
}
.job-meta { font-size: 13px; font-weight: 300; color: #6a8caa; margin-bottom: 14px; }
.job-tag {
    display: inline-block; background: rgba(26,107,181,0.09);
    border: 1px solid rgba(26,107,181,0.18); border-radius: 999px;
    padding: 4px 11px; font-size: 10px; font-weight: 500;
    letter-spacing: 0.06em; color: #1a6bb5; margin-right: 5px; margin-bottom: 6px;
}
.job-link { font-size: 13px; color: #1a6bb5; text-decoration: none; font-weight: 600; letter-spacing: 0.02em; }
.job-link:hover { color: #0f4f8c; }
.score-num {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 700; font-size: 42px; line-height: 1; letter-spacing: -0.04em;
}

@media (max-width: 768px) {
    .block-container { padding: 18px 16px 40px !important; }
    .hero { padding: 28px 24px; border-radius: 22px; }
}
</style>
""", unsafe_allow_html=True)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
]
def make_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=(500, 502, 503, 504),
                  allowed_methods=("GET",), raise_on_status=False)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s
def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.linkedin.com/jobs/search/",
        "Cache-Control": "no-cache",
    }
INDUSTRY_MAP = {
    "Any industry": "",
    "Information Technology & Services": "96",
    "Computer Software": "4",
    "Internet": "6",
    "Financial Services": "43",
    "Banking": "41",
    "Insurance": "42",
    "Management Consulting": "11",
    "Retail": "27",
    "Consumer Goods": "24",
    "Aviation & Aerospace": "94",
    "Airlines / Aviation": "52",
    "Hospital & Health Care": "14",
    "Pharmaceuticals": "15",
    "Real Estate": "44",
    "Construction": "48",
    "Oil & Energy": "57",
    "Telecommunications": "8",
    "Government Administration": "75",
    "Education Management": "69",
    "Hospitality": "31",
    "Logistics & Supply Chain": "116",
    "Marketing & Advertising": "80",
    "Human Resources": "137",
    "Legal Services": "10",
}
JOB_COLLECTIONS = {
    "👥 HR": {
        "keywords": ["HR Manager", "Talent Acquisition Specialist", "Recruitment Manager",
                     "HR Business Partner", "People Operations Manager", "HR Generalist"],
        "industries": ["Human Resources"],
    },
    "🎧 IT": {
        "keywords": ["Business Analyst", "Product Manager", "Product Owner",
                     "Project Manager",
                     "Digital Transformation",
                     "Business Partner", "Delivery Manager", "IT Director",
                     "Enterprise Applications", "AI Consultant"],
        "industries": ["Information Technology & Services", "Computer Software", "Internet"],
    },
    "💰 Finance": {
        "keywords": ["Finance Manager", "Financial Analyst", "Accountant", "CFO",
                     "Financial Controller", "Investment Analyst"],
        "industries": ["Financial Services", "Banking"],
    },
    "📣 Marketing": {
        "keywords": ["Marketing Manager", "Digital Marketing Manager", "Brand Manager",
                     "Content Manager", "Social Media Manager", "Marketing Director"],
        "industries": ["Marketing & Advertising"],
    },
    "🔧 Operations": {
        "keywords": ["Operations Manager", "Supply Chain Manager", "Procurement Manager",
                     "Logistics Manager", "Project Manager", "General Manager"],
        "industries": ["Logistics & Supply Chain"],
    },
    "🏋️ Fitness": {
        "keywords": ["Personal Trainer", "Fitness Trainer", "Fitness Coach",
                     "Fitness Manager", "Gym Instructor", "Group Fitness Instructor"],
        "industries": ["Any industry"],
    },
}
LOCATION_OPTIONS = [
    "United Arab Emirates", "Dubai", "Abu Dhabi", "Sharjah",
    "Saudi Arabia", "Qatar", "Oman", "Kuwait", "Bahrain",
    "Middle East", "Remote", "Worldwide",
]
FRESHNESS_MAP = {
    "Past hour": 3600,
    "Past 24 hours": 86400,
    "Past week": 604800,
    "Past month": 2592000,
    "Any time": None,
}
DELAY_RANGES = {
    "Fast (higher block risk)": (0.5, 1.5),
    "Normal": (1.5, 3.5),
    "Slow (fewer blocks)": (3.0, 6.0),
}
def clean_text(value):
    if not value:
        return ""
    return " ".join(value.replace("\n", " ").split())
def parse_posted_datetime(value):
    if not value:
        return pd.NaT
    try:
        return pd.to_datetime(value, utc=True, errors="raise")
    except Exception:
        pass
    v = str(value).lower()
    now = pd.Timestamp.now(tz="UTC")
    m = re.search(r"(\d+)", v)
    n = int(m.group(1)) if m else 1
    if "minute" in v:
        return now - pd.Timedelta(minutes=n)
    if "hour" in v:
        return now - pd.Timedelta(hours=n)
    if "day" in v:
        return now - pd.Timedelta(days=n)
    if "week" in v:
        return now - pd.Timedelta(weeks=n)
    if "month" in v:
        return now - pd.Timedelta(days=n * 30)
    if "year" in v:
        return now - pd.Timedelta(days=n * 365)
    return pd.NaT
def build_url(keyword, location, freshness_seconds, start, industry_ids):
    k = urllib.parse.quote_plus(keyword)
    loc = urllib.parse.quote_plus(location)
    url = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        f"?keywords={k}&location={loc}&start={start}&sortBy=DD"
    )
    if freshness_seconds:
        url += f"&f_TPR=r{freshness_seconds}"
    if industry_ids:
        url += f"&f_I={urllib.parse.quote_plus(','.join(industry_ids))}"
    return url
def is_blocked_response(status_code, html):
    if status_code == 999:
        return True, "Status 999 (bot detected)"
    if status_code == 429:
        return True, "Rate limited (429)"
    if status_code not in (200, 201):
        return True, f"Status {status_code}"
    if len(html) < 500:
        return True, f"Too short ({len(html)} chars)"
    for sig in ["challenge?", "authwall", "checkpoint", "captcha", "please verify", "too many requests"]:
        if sig in html.lower():
            return True, f"Block page ('{sig}')"
    return False, ""
def parse_jobs(html, keyword, industry_label, collection):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for li in soup.find_all("li"):
        title_el = li.select_one("h3.base-search-card__title") or li.find("h3")
        title = clean_text(title_el.get_text(" ", strip=True)) if title_el else ""
        company_el = li.select_one("h4.base-search-card__subtitle") or li.find("h4")
        company = clean_text(company_el.get_text(" ", strip=True)) if company_el else ""
        loc_el = li.select_one(".job-search-card__location, .base-search-card__metadata span")
        loc = clean_text(loc_el.get_text(" ", strip=True)) if loc_el else ""
        link_el = li.select_one("a.base-card__full-link") or li.find("a", href=re.compile(r"linkedin\.com/jobs/view/"))
        url = link_el["href"].split("?")[0] if link_el and link_el.get("href") else ""
        time_el = li.find("time")
        if time_el:
            posted_text = clean_text(time_el.get_text(" ", strip=True))
            posted_raw = time_el.get("datetime") or posted_text
        else:
            posted_text, posted_raw = "", ""
        if not title or not url:
            continue
        job_id_match = re.search(r"/jobs/view/(\d+)", url)
        job_id = job_id_match.group(1) if job_id_match else hashlib.md5(url.encode()).hexdigest()[:12]
        jobs.append({
            "Job ID": job_id, "Title": title, "Company": company, "Location": loc,
            "Posted": posted_text, "Posted Date": posted_raw, "Job Title": keyword,
            "Collection": collection, "Industry Filter": industry_label, "URL": url,
        })
    return jobs
def fetch_page(session, url, delay_range):
    try:
        r = session.get(url, headers=get_headers(), timeout=25)
        html = r.text
        blocked, reason = is_blocked_response(r.status_code, html)
    except Exception as e:
        return None, True, str(e), 0
    sleep_range = (3.0, 6.0) if blocked else delay_range
    time.sleep(random.uniform(*sleep_range))
    return (None if blocked else html), blocked, reason, r.status_code
def fetch_jobs(keyword, location, freshness_seconds, pages, industry_ids,
               industry_label, collection, delay_range, session, cache):
    results, diagnostics, block_count = [], [], 0
    for page in range(pages):
        url = build_url(keyword, location, freshness_seconds, page * 25, industry_ids)
        cache_key = (keyword, location, freshness_seconds, tuple(industry_ids), page)
        if cache_key in cache:
            html, status = cache[cache_key]
            jobs = parse_jobs(html, keyword, industry_label, collection) if html else []
            diagnostics.append({
                "keyword": keyword, "collection": collection, "industry": industry_label,
                "page": page + 1, "status": f"{status} (cached)",
                "html_length": len(html) if html else 0,
                "jobs_parsed": len(jobs), "blocked": False, "block_reason": "", "url": url,
            })
            results.extend(jobs)
            continue
        html, blocked, reason, status = fetch_page(session, url, delay_range)
        jobs = parse_jobs(html, keyword, industry_label, collection) if html and not blocked else []
        if not blocked and html:
            cache[cache_key] = (html, status)
        diagnostics.append({
            "keyword": keyword, "collection": collection, "industry": industry_label,
            "page": page + 1, "status": status,
            "html_length": len(html) if html else 0,
            "jobs_parsed": len(jobs), "blocked": blocked,
            "block_reason": reason, "url": url,
        })
        results.extend(jobs)
        if blocked:
            block_count += 1
    return results, diagnostics, block_count
def make_keywords(main_query, extra_queries_text, selected_collection, active_keywords=None):
    raw = []
    if main_query.strip():
        raw.append(main_query.strip())
    raw.extend(x.strip() for x in extra_queries_text.splitlines() if x.strip())
    if selected_collection != "Custom search":
        raw.extend(active_keywords or JOB_COLLECTIONS[selected_collection]["keywords"])
    seen, out = set(), []
    for k in raw:
        key = k.lower()
        if key not in seen:
            seen.add(key)
            out.append(k)
    return out
def score_job_keyword(row, search_terms, include_words, collection_is_set):
    text = f"{row.get('Title','')} {row.get('Company','')} {row.get('Location','')} {row.get('Industry Filter','')}".lower()
    score = 50
    for t in search_terms:
        t = t.lower().strip()
        if t and t in text:
            score += 12
    for w in include_words:
        w = w.lower().strip()
        if w and w in text:
            score += 8
    for t in ["senior", "lead", "manager", "head", "director", "principal",
              "specialist", "consultant", "architect", "owner"]:
        if t in text:
            score += 3
    if collection_is_set:
        score += 5
    for t in ["intern", "internship", "graduate", "trainee"]:
        if t in text:
            score -= 20
    return max(0, min(score, 100))
def build_ai_search_query(query_terms, include_words):
    # Stronger profile-style query gives the AI matcher more context than a single keyword.
    parts = query_terms + include_words
    query = " ".join([p.strip() for p in parts if str(p).strip()])
    return query.strip()

def build_job_text_series(df):
    # Keep this lightweight because LinkedIn guest search does not return full job descriptions.
    return (
        df["Title"].fillna("") + " | " +
        df["Company"].fillna("") + " | " +
        df["Location"].fillna("") + " | " +
        df["Industry Filter"].fillna("") + " | searched as: " +
        df["Job Title"].fillna("")
    )

def score_jobs_semantic(df, query_terms, include_words):
    if df.empty or not SEMANTIC_AVAILABLE:
        return [50] * len(df)
    query = build_ai_search_query(query_terms, include_words)
    if not query:
        return [50] * len(df)
    corpus = build_job_text_series(df).tolist()
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1)
        matrix = vec.fit_transform(corpus + [query])
        sims = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        return [int(round(max(0.0, min(1.0, s)) * 100)) for s in sims]
    except Exception:
        return [50] * len(df)

@st.cache_resource(show_spinner=False)
def load_ai_semantic_model():
    if not AI_SEMANTIC_AVAILABLE:
        return None
    return SentenceTransformer("all-MiniLM-L6-v2")

def score_jobs_ai_semantic(df, query_terms, include_words):
    if df.empty or not AI_SEMANTIC_AVAILABLE:
        return score_jobs_semantic(df, query_terms, include_words)
    query = build_ai_search_query(query_terms, include_words)
    if not query:
        return [50] * len(df)
    corpus = build_job_text_series(df).tolist()
    try:
        model = load_ai_semantic_model()
        if model is None:
            return score_jobs_semantic(df, query_terms, include_words)
        query_emb = model.encode([query], normalize_embeddings=True)
        job_emb = model.encode(corpus, normalize_embeddings=True)
        sims = cosine_similarity(query_emb, job_emb).flatten()
        return [int(round(max(0.0, min(1.0, float(s))) * 100)) for s in sims]
    except Exception:
        return score_jobs_semantic(df, query_terms, include_words)

def score_jobs_hybrid_ai(df, query_terms, include_words, collection_is_set):
    # Full sentence-transformers mode. Can be slow on first run because the model downloads/loads.
    keyword_scores = df.apply(
        lambda r: score_job_keyword(r, query_terms, include_words, collection_is_set), axis=1,
    ).tolist()
    ai_scores = score_jobs_ai_semantic(df, query_terms, include_words)
    hybrid_scores = []
    for kw, ai in zip(keyword_scores, ai_scores):
        score = int(round((0.35 * kw) + (0.65 * ai)))
        hybrid_scores.append(max(0, min(score, 100)))
    return hybrid_scores

def score_jobs_hybrid_fast(df, query_terms, include_words, collection_is_set):
    # Fast hybrid mode: keyword signal + TF-IDF semantic similarity.
    # This avoids the Streamlit freeze caused by loading sentence-transformers/torch.
    keyword_scores = df.apply(
        lambda r: score_job_keyword(r, query_terms, include_words, collection_is_set), axis=1,
    ).tolist()
    semantic_scores = score_jobs_semantic(df, query_terms, include_words)
    hybrid_scores = []
    for kw, sem in zip(keyword_scores, semantic_scores):
        score = int(round((0.55 * kw) + (0.45 * sem)))
        hybrid_scores.append(max(0, min(score, 100)))
    return hybrid_scores
def contains_any(text, words):
    return any(w.lower() in text.lower() for w in words if w) if words else True
def contains_all(text, words):
    return all(w.lower() in text.lower() for w in words if w) if words else True
def apply_filters(df, include_words, require_all, exclude_words,
                  company_text, result_location_text, min_score, hide_seen, seen_ids):
    if df.empty:
        return df
    df = df.copy()
    combined = (df["Title"].fillna("") + " " + df["Company"].fillna("")
                + " " + df["Location"].fillna("") + " " + df["Industry Filter"].fillna(""))
    if include_words:
        fn = contains_all if require_all else contains_any
        df = df[combined.apply(lambda x: fn(x, include_words))]
    if exclude_words:
        c2 = df["Title"].fillna("") + " " + df["Company"].fillna("") + " " + df["Location"].fillna("")
        df = df[~c2.apply(lambda x: contains_any(x, exclude_words))]
    if company_text.strip():
        df = df[df["Company"].fillna("").str.contains(company_text.strip(), case=False, na=False)]
    if result_location_text.strip():
        df = df[df["Location"].fillna("").str.contains(result_location_text.strip(), case=False, na=False)]
    if hide_seen and seen_ids:
        df = df[~df["Job ID"].isin(seen_ids)]
    return df[df["Match Score"] >= min_score]
if "page_cache" not in st.session_state:
    st.session_state.page_cache = {}
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "last_diagnostics" not in st.session_state:
    st.session_state.last_diagnostics = None
if "last_block_count" not in st.session_state:
    st.session_state.last_block_count = 0
if "request_session" not in st.session_state:
    st.session_state.request_session = make_session()
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">LinkedIn Jobs Hunter · v9.3 · UAE & Middle East</div>
  <div class="hero-title">Find fresh roles.<br><em>Before everyone else.</em></div>
  <div class="hero-sub">Clean LinkedIn scanner with collections, filters, fast hybrid smart search, optional AI scoring, persistent seen-list, in-session caching.</div>
</div>
""", unsafe_allow_html=True)
seen_count = db_seen_count()
sc1, sc2, sc3 = st.columns([3, 1, 1])
with sc1:
    if seen_count:
        st.caption(f"📑 {seen_count} jobs in your hidden/seen list (persisted at `~/.jobs_hunter.db`)")
    else:
        st.caption("📑 Hidden/seen list is empty — mark jobs as seen below after a search")
with sc2:
    if st.button("Clear cache", key="clear_cache_btn"):
        st.session_state.page_cache = {}
        st.success("Cache cleared.")
with sc3:
    if st.button("Reset seen-list", key="reset_seen_btn"):
        db_clear_seen()
        st.success("Seen-list cleared.")
st.markdown('<span class="slabel">01 &nbsp;—&nbsp; Collection</span>', unsafe_allow_html=True)
collection_options = ["Custom search"] + list(JOB_COLLECTIONS.keys())
selected_collection = st.radio("collection", collection_options, horizontal=True, label_visibility="collapsed")
if selected_collection != "Custom search":
    cdata = JOB_COLLECTIONS[selected_collection]
    st.caption(f"{len(cdata['keywords'])} roles in collection — click × to remove any")
    active_keywords = st.multiselect(
        "active_kw", options=cdata["keywords"], default=cdata["keywords"],
        key=f"kw_select_{selected_collection}_v9", label_visibility="collapsed",
    )
else:
    active_keywords = []
st.markdown('<hr class="sdivider">', unsafe_allow_html=True)
st.markdown('<span class="slabel">02 &nbsp;—&nbsp; Search</span>', unsafe_allow_html=True)
c1, c2 = st.columns([3, 1])
with c1:
    main_query = st.text_input(
        "Role / job title", value="",
        placeholder="e.g. Product Manager, ERP Consultant, Digital Transformation Lead",
        key="main_query_input",
        label_visibility="collapsed",
    )
with c2:
    location = st.selectbox("Location", LOCATION_OPTIONS, index=0, key="location_select")
c3, c4, c5 = st.columns(3)
with c3:
    freshness = st.selectbox("Posted within", list(FRESHNESS_MAP.keys()), index=1, key="freshness_select")
with c4:
    default_industries = (
        JOB_COLLECTIONS[selected_collection]["industries"]
        if selected_collection != "Custom search" else ["Any industry"]
    )
    selected_industries = st.multiselect(
        "Industry", list(INDUSTRY_MAP.keys()), default=default_industries, key="industry_select",
    )
with c5:
    sort_mode = st.selectbox("Sort by", ["Newest first", "Match score first"], index=0, key="sort_select")
extra_queries_text = st.text_area(
    "Extra keywords (one per line)", value="",
    placeholder="Senior Product Manager\nAI Product Owner",
    height=80, key="extra_queries_text",
)
st.markdown('<hr class="sdivider">', unsafe_allow_html=True)
with st.expander("⚙  Filters & settings"):
    fa, fb, fc = st.columns(3)
    with fa:
        include_text = st.text_input("Must include", value="", placeholder="e.g. AI, ERP", key="include_text")
    with fb:
        exclude_text = st.text_input("Exclude words", value="intern, internship, trainee", key="exclude_text")
    with fc:
        require_all = st.checkbox("Require ALL include words", value=False, key="require_all")
    fd, fe, ff = st.columns(3)
    with fd:
        company_text = st.text_input("Company contains", value="", placeholder="e.g. Emirates, G42", key="company_text")
    with fe:
        result_location_text = st.text_input("Location contains", value="", placeholder="e.g. Dubai", key="result_location_text")
    with ff:
        min_score = st.slider("Min match score", 0, 100, 45, key="min_score")
    fg, fh, fi = st.columns(3)
    with fg:
        pages = st.slider("Pages per keyword", 1, 5, 2, key="pages")
    with fh:
        delay_mode = st.selectbox("Request delay", list(DELAY_RANGES.keys()), index=1, key="delay_mode")
    with fi:
        scoring_options = ["Hybrid Smart Search (fast)", "Keyword (fast)"]
        if SEMANTIC_AVAILABLE:
            scoring_options.append("Semantic (TF-IDF)")
        if AI_SEMANTIC_AVAILABLE:
            scoring_options.append("Hybrid AI Search (slow first run)")
        scoring_mode = st.selectbox(
            "Scoring", scoring_options,
            index=0,
            key="scoring_mode",
        )
    fj, fk = st.columns(2)
    with fj:
        hide_seen = st.checkbox("Hide already-seen jobs", value=True, key="hide_seen")
    with fk:
        show_diagnostics = st.checkbox("Show diagnostics", value=False, key="diagnostics")
delay_range = DELAY_RANGES[delay_mode]
keywords = make_keywords(main_query, extra_queries_text, selected_collection, active_keywords)
include_words = [x.strip() for x in include_text.split(",") if x.strip()]
exclude_words = [x.strip() for x in exclude_text.split(",") if x.strip()]
if not selected_industries:
    selected_industries = ["Any industry"]
if "Any industry" in selected_industries and len(selected_industries) > 1:
    selected_industries = [x for x in selected_industries if x != "Any industry"]
industry_ids = [INDUSTRY_MAP[x] for x in selected_industries if INDUSTRY_MAP.get(x)]
industry_label = ", ".join(selected_industries)
if selected_collection == "🎧 IT" and pages > 1:
    st.warning("⚠️ IT collection has many keywords. Consider Slow delay or 1 page to reduce LinkedIn blocks.")
if not SEMANTIC_AVAILABLE:
    st.caption("ℹ️ scikit-learn not installed → only keyword scoring. `pip install scikit-learn` for TF-IDF semantic mode.")
if not AI_SEMANTIC_AVAILABLE:
    st.caption("ℹ️ sentence-transformers not installed → full AI mode is unavailable, but Fast Hybrid Search still works.")
st.markdown("<br>", unsafe_allow_html=True)
def run_search():
    if not keywords:
        st.error("Enter a job title, add extra searches, or choose a collection.")
        return
    all_jobs, all_diag, total_blocks = [], [], 0
    seen_ids_run = set()
    progress = st.progress(0)
    status_text = st.empty()
    for idx, kw in enumerate(keywords):
        status_text.markdown(
            f'<p style="font-size:11px;letter-spacing:0.1em;text-transform:uppercase;color:#6a8caa;">'
            f'Searching {idx+1}/{len(keywords)}: <span style="color:#1a6bb5;font-weight:600;">{esc_text(kw)}</span></p>',
            unsafe_allow_html=True,
        )
        jobs, diag, bc = fetch_jobs(
            keyword=kw, location=location,
            freshness_seconds=FRESHNESS_MAP[freshness], pages=pages,
            industry_ids=industry_ids, industry_label=industry_label,
            collection=selected_collection, delay_range=delay_range,
            session=st.session_state.request_session,
            cache=st.session_state.page_cache,
        )
        for job in jobs:
            if job["Job ID"] not in seen_ids_run:
                seen_ids_run.add(job["Job ID"])
                all_jobs.append(job)
        all_diag.extend(diag)
        total_blocks += bc
        progress.progress((idx + 1) / len(keywords))
    status_text.empty()
    st.session_state.last_results = all_jobs
    st.session_state.last_diagnostics = all_diag
    st.session_state.last_block_count = total_blocks
btn_col1, btn_col2 = st.columns([3, 1])
with btn_col1:
    run_clicked = st.button("🔎  Find Opportunities", type="primary", use_container_width=True)
with btn_col2:
    reapply_clicked = st.button(
        "Re-apply filters", use_container_width=True,
        disabled=st.session_state.last_results is None,
    )
if run_clicked:
    run_search()
all_jobs = st.session_state.last_results
all_diag = st.session_state.last_diagnostics or []
total_blocks = st.session_state.last_block_count
if all_jobs is not None:
    total_req = max(len(all_diag), 1)
    if total_blocks > 0:
        bp = round(100 * total_blocks / total_req)
        if bp >= 50:
            st.error(f"🚫 LinkedIn blocked {total_blocks}/{total_req} requests ({bp}%). Try Slow delay or wait.")
        elif bp >= 20:
            st.warning(f"⚠️ {total_blocks}/{total_req} requests blocked ({bp}%). Some results may be missing.")
        else:
            st.info(f"ℹ️ {total_blocks}/{total_req} minor blocks. Results may be slightly incomplete.")
    if show_diagnostics:
        st.dataframe(pd.DataFrame(all_diag), use_container_width=True, hide_index=True)
    if not all_jobs:
        st.error("No jobs found. LinkedIn may have blocked all requests. Try Slow delay or simpler keywords.")
        st.stop()
    df = pd.DataFrame(all_jobs)
    df["Posted Parsed"] = df["Posted Date"].apply(parse_posted_datetime)
    collection_is_set = selected_collection != "Custom search"
    if scoring_mode.startswith("Hybrid Smart"):
        # Fast default: no model download, no torch loading, no freezing.
        df["Match Score"] = score_jobs_hybrid_fast(df, keywords, include_words, collection_is_set)
    elif scoring_mode.startswith("Hybrid AI") and AI_SEMANTIC_AVAILABLE:
        with st.spinner("Loading AI model and scoring jobs... first run can take several minutes"):
            df["Match Score"] = score_jobs_hybrid_ai(df, keywords, include_words, collection_is_set)
    elif scoring_mode.startswith("Semantic") and SEMANTIC_AVAILABLE:
        df["Match Score"] = score_jobs_semantic(df, keywords, include_words)
    else:
        df["Match Score"] = df.apply(
            lambda r: score_job_keyword(r, keywords, include_words, collection_is_set), axis=1,
        )
    persistent_seen = db_get_seen_ids()
    before_filter = len(df)
    filtered_df = apply_filters(
        df, include_words, require_all, exclude_words,
        company_text, result_location_text, min_score, hide_seen, persistent_seen,
    )
    after_filter = len(filtered_df)
    if filtered_df.empty:
        st.warning(
            f"Found {before_filter} jobs but 0 after filters. "
            "Try lowering min score, removing include words, or unchecking Hide already-seen."
        )
        st.dataframe(
            df.sort_values("Posted Parsed", ascending=False, na_position="last")
            [["Posted Date", "Posted", "Match Score", "Title", "Company", "Location", "URL"]],
            use_container_width=True, hide_index=True,
        )
        st.stop()
    if sort_mode == "Newest first":
        filtered_df = filtered_df.sort_values(
            ["Posted Parsed", "Match Score"], ascending=[False, False], na_position="last",
        )
    else:
        filtered_df = filtered_df.sort_values(
            ["Match Score", "Posted Parsed"], ascending=[False, False], na_position="last",
        )
    st.markdown('<hr class="sdivider">', unsafe_allow_html=True)
    st.success(
        f"✅ {before_filter} jobs found · {after_filter} matched your filters · "
        f"{len(st.session_state.page_cache)} pages cached"
    )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matched", after_filter)
    m2.metric("Total found", before_filter)
    m3.metric("Collections", filtered_df["Collection"].nunique())
    valid_dates = filtered_df["Posted Parsed"].dropna()
    m4.metric("Newest", valid_dates.iloc[0].strftime("%b %d, %H:%M") if not valid_dates.empty else "N/A")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<span class="slabel">Results — {sort_mode}</span>', unsafe_allow_html=True)
    display_cols = [
        "Posted Date", "Posted", "Title", "Company", "Location",
        "Collection", "Industry Filter", "URL",
    ]
    display_df = filtered_df[display_cols].rename(columns={"Title": "Job Title"})
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown("<br>", unsafe_allow_html=True)
    top_n = min(15, len(filtered_df))
    st.markdown(f'<span class="slabel">Top {top_n} cards</span>', unsafe_allow_html=True)
    top_jobs = filtered_df.head(top_n)
    for _, row in top_jobs.iterrows():
        score = int(row["Match Score"])
        s_color = "#1a6bb5" if score >= 70 else "#a8c8e8"
        parsed = row.get("Posted Parsed")
        date_label = parsed.strftime("%b %d, %Y") if pd.notna(parsed) else (row["Posted Date"] or "—")
        title = esc_text(row["Title"])
        company = esc_text(row["Company"] or "—")
        location_s = esc_text(row["Location"] or "—")
        collection_s = esc_text(row["Collection"])
        keyword_s = esc_text(row.get("Job Title", ""))
        date_s = esc_text(date_label)
        url = esc_attr(row["URL"])
        st.markdown(
            f"""
        <div class="job-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:24px;">
            <div style="flex:1;min-width:0;">
              <div class="job-title">{title}</div>
              <div class="job-meta">{company} &nbsp;·&nbsp; {location_s}</div>
              <span class="job-tag">{collection_s}</span>
              <span class="job-tag">{keyword_s}</span>
              <span class="job-tag">{date_s}</span>
              <div style="margin-top:16px;">
                <a class="job-link" href="{url}" target="_blank" rel="noopener noreferrer">View on LinkedIn →</a>
              </div>
            </div>
          </div>
        </div>

        </div>
        """,
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)
    msa, msb, msc = st.columns(3)
    with msa:
        if st.button(f"📌  Mark top {top_n} as seen", use_container_width=True):
            db_mark_seen(top_jobs.to_dict("records"), hide=True)
            st.success(f"Marked {top_n} jobs as seen.")
            st.rerun()
    with msb:
        if st.button(f"📌  Mark ALL {after_filter} as seen", use_container_width=True):
            db_mark_seen(filtered_df.to_dict("records"), hide=True)
            st.success(f"Marked {after_filter} jobs as seen.")
            st.rerun()
    with msc:
        export_df = filtered_df.copy()
        export_df["Posted ISO"] = export_df["Posted Parsed"].apply(
            lambda x: x.isoformat() if pd.notna(x) else "",
        )
        export_df = export_df.drop(columns=["Posted Parsed"], errors="ignore")
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇  Download CSV", csv,
            file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv", use_container_width=True,
        )
elif reapply_clicked:
    st.rerun()
st.markdown('<hr class="sdivider">', unsafe_allow_html=True)
st.markdown(
    '<p style="font-size:10px;color:#a8c8e8;letter-spacing:0.16em;text-transform:uppercase;">'
    'JOBS HUNTER v9.2 &nbsp;·&nbsp; honest scoring · session cache · persistent seen-list</p>',
    unsafe_allow_html=True,
)