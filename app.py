import re
import time
import random
import urllib.parse
from datetime import datetime
import requests
import pandas as pd
import streamlit as st

# =========================================================
# LinkedIn Jobs Hunter — v8
# Azure blue interface: Cormorant Garamond + Outfit
# =========================================================

st.set_page_config(page_title="Jobs Hunter", page_icon="🔎", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,700&family=Outfit:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background: linear-gradient(160deg, #ddeeff 0%, #c8e4fb 50%, #b8d8f2 100%) !important;
    font-family: 'Outfit', sans-serif !important;
    color: #062040 !important;
}

/* atmospheric radial overlays */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 70% 50% at 5% 0%,   rgba(79,168,232,0.22) 0%, transparent 55%),
        radial-gradient(ellipse 55% 45% at 95% 100%, rgba(26,107,181,0.16) 0%, transparent 55%);
    pointer-events: none;
    z-index: 0;
}

.block-container {
    padding: 28px 44px 56px !important;
    max-width: 1240px !important;
    position: relative;
    z-index: 1;
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Hero ── */
.hero {
    background: rgba(255,255,255,0.68);
    border: 1.5px solid rgba(184,212,236,0.9);
    border-radius: 28px;
    padding: 38px 42px;
    margin: 8px 0 28px;
    box-shadow:
        0 4px 6px rgba(26,107,181,0.05),
        0 24px 60px rgba(26,107,181,0.10),
        inset 0 1px 0 rgba(255,255,255,0.95);
    backdrop-filter: blur(20px);
    position: relative;
    overflow: hidden;
}

/* top accent bar */
.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #4fa8e8, #1a6bb5, #6ac4f8);
    border-radius: 28px 28px 0 0;
}

.hero-eyebrow {
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #1a6bb5;
    margin-bottom: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
}

.hero-eyebrow::before {
    content: '';
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #4fa8e8;
    box-shadow: 0 0 7px #4fa8e8;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.35; }
}

.hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(38px, 5vw, 64px);
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.0;
    color: #062040;
    margin-bottom: 16px;
}

.hero-title em {
    font-style: italic;
    color: #1a6bb5;
}

.hero-sub {
    font-size: 15px;
    font-weight: 300;
    color: #6a8caa;
    max-width: 600px;
    line-height: 1.65;
}

/* ── Section labels ── */
.slabel {
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #6a8caa;
    display: block;
    margin: 26px 0 14px;
    font-weight: 600;
}

.sdivider {
    border: none;
    border-top: 1px solid rgba(184,212,236,0.7);
    margin: 24px 0;
}

/* ── Keyword banner ── */
.kw-banner {
    background: rgba(255,255,255,0.65);
    border: 1.5px solid rgba(184,212,236,0.8);
    border-radius: 16px;
    padding: 16px 20px 14px;
    margin: 10px 0 8px;
    box-shadow: 0 8px 24px rgba(26,107,181,0.07);
    backdrop-filter: blur(12px);
}

.kw-banner-label {
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #1a6bb5;
    margin-bottom: 10px;
    font-weight: 600;
}

/* ── Text ── */
p, label, .stMarkdown p {
    color: #2a4a6a !important;
    font-size: 14px !important;
    font-family: 'Outfit', sans-serif !important;
}
h1, h2, h3 { color: #062040 !important; }

/* ── Inputs ── */
.stTextInput input,
.stTextArea textarea {
    background: #ffffff !important;
    border: 1.5px solid #b8d4ec !important;
    border-radius: 12px !important;
    color: #062040 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    caret-color: #1a6bb5 !important;
    box-shadow: none !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #1a6bb5 !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(26,107,181,0.12) !important;
    outline: none !important;
}

/* ensure Streamlit wrapper divs don't add dark bg or extra borders */
.stTextInput > div, .stTextArea > div,
.stTextInput > div > div, .stTextArea > div > div,
.stTextInput > label + div, .stTextArea > label + div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #90aec8 !important;
}

.stTextInput label, .stTextArea label,
.stSelectbox label, .stMultiSelect label,
.stSlider label, .stCheckbox label {
    font-family: 'Outfit', sans-serif !important;
    font-size: 10px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #6a8caa !important;
    font-weight: 600 !important;
}

/* ── Selects & Multiselect ── */

/* 1. Strip ALL wrappers of border/bg — only the baseweb control gets styled */
.stSelectbox > div,
.stSelectbox > div > div,
.stSelectbox > div > div > div,
.stMultiSelect > div,
.stMultiSelect > div > div,
.stMultiSelect > div > div > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* 2. Style only the real control element */
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] {
    background: #ffffff !important;
    border: 1.5px solid #b8d4ec !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    min-height: 46px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    color: #062040 !important;
    transition: border-color 0.18s !important;
}

.stSelectbox [data-baseweb="select"]:focus-within,
.stMultiSelect [data-baseweb="select"]:focus-within {
    border-color: #1a6bb5 !important;
    box-shadow: 0 0 0 3px rgba(26,107,181,0.12) !important;
}

/* 3. Inner content divs — transparent, no extra border */
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #062040 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* selected value text */
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div[class*="placeholder"],
.stSelectbox [data-baseweb="select"] div[class*="value"] {
    color: #062040 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
}

/* chevron icon */
.stSelectbox [data-baseweb="select"] svg,
.stMultiSelect [data-baseweb="select"] svg {
    fill: #6a8caa !important;
    color: #6a8caa !important;
}

/* 4. Dropdown popup menu */
[data-baseweb="popover"] {
    background: #ffffff !important;
    border: 1.5px solid #b8d4ec !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 28px rgba(26,107,181,0.12) !important;
}

[data-baseweb="menu"] {
    background: #ffffff !important;
    border-radius: 12px !important;
}

[data-baseweb="option"] {
    background: #ffffff !important;
    color: #062040 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 16px !important;
}

[data-baseweb="option"]:hover,
[data-baseweb="option"][aria-selected="true"] {
    background: rgba(26,107,181,0.08) !important;
    color: #062040 !important;
}

/* 5. Multiselect input text */
.stMultiSelect [data-baseweb="select"] input {
    color: #062040 !important;
    background: transparent !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
}

/* 6. Selected tag chips */
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(26,107,181,0.10) !important;
    border: 1.5px solid rgba(26,107,181,0.28) !important;
    color: #0f4f8c !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    border-radius: 999px !important;
    padding: 3px 10px !important;
    box-shadow: none !important;
}

.stMultiSelect [data-baseweb="tag"] span {
    color: #0f4f8c !important;
}

/* tag × button */
.stMultiSelect [data-baseweb="tag"] [data-baseweb="icon"],
.stMultiSelect [data-baseweb="tag"] svg {
    fill: #1a6bb5 !important;
    color: #1a6bb5 !important;
}

/* ── Radio pills ── */
.stRadio > div {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
    padding: 2px 0 !important;
}

.stRadio label {
    background: rgba(255,255,255,0.62) !important;
    border: 1.5px solid rgba(184,212,236,0.85) !important;
    border-radius: 999px !important;
    padding: 9px 20px !important;
    color: #2a4a6a !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
    backdrop-filter: blur(8px) !important;
}

.stRadio label *, .stRadio label p, .stRadio label span, .stRadio label div {
    color: #2a4a6a !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

.stRadio label:has(input:checked) {
    background: #1a6bb5 !important;
    border-color: #1a6bb5 !important;
    color: #ffffff !important;
    box-shadow: 0 6px 20px rgba(26,107,181,0.28) !important;
}

.stRadio label:has(input:checked) *,
.stRadio label:has(input:checked) p,
.stRadio label:has(input:checked) span,
.stRadio label:has(input:checked) div {
    color: #ffffff !important;
}

.stRadio label input[type="radio"] { display: none !important; }

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4fa8e8 0%, #1a6bb5 60%, #0f4f8c 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 30px !important;
    padding: 16px 32px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 8px 32px rgba(26,107,181,0.32) !important;
    transition: all 0.18s ease !important;
    width: 100% !important;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 14px 40px rgba(26,107,181,0.42) !important;
}

.stButton > button:not([kind="primary"]),
.stDownloadButton > button {
    background: rgba(255,255,255,0.7) !important;
    color: #1a6bb5 !important;
    border: 1.5px solid rgba(184,212,236,0.9) !important;
    border-radius: 14px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    padding: 12px 18px !important;
    width: 100% !important;
    backdrop-filter: blur(8px) !important;
    transition: all 0.18s !important;
}

.stButton > button:not([kind="primary"]):hover,
.stDownloadButton > button:hover {
    background: #1a6bb5 !important;
    color: #ffffff !important;
    border-color: #1a6bb5 !important;
}

/* ── Sliders & checkboxes ── */
.stSlider > div > div > div > div {
    background: #1a6bb5 !important;
}

.stCheckbox label {
    color: #2a4a6a !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    font-size: 13px !important;
    font-weight: 400 !important;
}

/* ── Metrics ── */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.68) !important;
    border: 1.5px solid rgba(184,212,236,0.8) !important;
    border-radius: 18px !important;
    padding: 22px !important;
    box-shadow: 0 8px 28px rgba(26,107,181,0.08) !important;
    backdrop-filter: blur(16px) !important;
}

div[data-testid="stMetricLabel"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 10px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #6a8caa !important;
    font-weight: 600 !important;
}

div[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 38px !important;
    font-weight: 700 !important;
    color: #062040 !important;
    letter-spacing: -0.03em !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.62) !important;
    border: 1.5px solid rgba(184,212,236,0.8) !important;
    border-radius: 14px !important;
    color: #2a4a6a !important;
    padding: 14px 20px !important;
    box-shadow: 0 4px 14px rgba(26,107,181,0.06) !important;
    backdrop-filter: blur(10px) !important;
    font-family: 'Outfit', sans-serif !important;
}

.streamlit-expanderContent {
    background: rgba(255,255,255,0.58) !important;
    border: 1.5px solid rgba(184,212,236,0.7) !important;
    border-top: none !important;
    border-radius: 0 0 14px 14px !important;
    padding: 22px !important;
    backdrop-filter: blur(10px) !important;
}

/* ── Alerts ── */
div[data-testid="stAlert"] {
    border-radius: 14px !important;
    border: 1.5px solid rgba(184,212,236,0.7) !important;
    box-shadow: 0 6px 18px rgba(26,107,181,0.06) !important;
    backdrop-filter: blur(8px) !important;
    font-family: 'Outfit', sans-serif !important;
}

/* ── Dataframe ── */
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

/* ── Job cards ── */
.job-card {
    background: rgba(255,255,255,0.68);
    border: 1.5px solid rgba(184,212,236,0.85);
    border-radius: 20px;
    padding: 22px 26px;
    margin-bottom: 12px;
    box-shadow: 0 8px 28px rgba(26,107,181,0.07);
    backdrop-filter: blur(14px);
    transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
    position: relative;
    overflow: hidden;
}

.job-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #4fa8e8, #1a6bb5);
    border-radius: 20px 0 0 20px;
    opacity: 0;
    transition: opacity 0.18s;
}

.job-card:hover {
    border-color: rgba(26,107,181,0.45);
    transform: translateY(-2px);
    box-shadow: 0 16px 44px rgba(26,107,181,0.14);
}

.job-card:hover::before { opacity: 1; }

.job-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 20px;
    font-weight: 700;
    color: #062040;
    margin-bottom: 6px;
    letter-spacing: -0.01em;
    line-height: 1.2;
}

.job-meta {
    font-size: 13px;
    font-weight: 300;
    color: #6a8caa;
    margin-bottom: 14px;
}

.job-tag {
    display: inline-block;
    background: rgba(26,107,181,0.09);
    border: 1px solid rgba(26,107,181,0.18);
    border-radius: 999px;
    padding: 4px 11px;
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.06em;
    color: #1a6bb5;
    margin-right: 5px;
    margin-bottom: 6px;
}

.job-link {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: #1a6bb5;
    text-decoration: none;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.job-link:hover { color: #0f4f8c; }

.score-num {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 700;
    font-size: 42px;
    line-height: 1;
    letter-spacing: -0.04em;
}

@media (max-width: 768px) {
    .block-container { padding: 18px 16px 40px !important; }
    .hero { padding: 28px 24px; border-radius: 22px; }
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# User-Agent rotation
# =========================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
]

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


# =========================================================
# Constants
# =========================================================

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
        "keywords": [
            "HR Manager", "Talent Acquisition Specialist",
            "Recruitment Manager", "HR Business Partner",
            "People Operations Manager", "HR Generalist",
        ],
        "industries": ["Human Resources"],
        "include": "",
        "remote": False
    },
    "🎧 IT": {
        "keywords": [
            "Product Manager", "Senior Product Manager", "Product Owner",
            "Digital Product Manager", "AI Product Manager",
            "IT Project Manager", "Senior Project Manager",
            "Digital Transformation Manager", "Technology Consultant",
            "IT Strategy Consultant", "Business Analyst", "Functional Consultant",
            "Enterprise Applications Manager",
            "AI Consultant",
        ],
        "industries": ["Information Technology & Services", "Computer Software", "Internet"],
        "include": "",
        "remote": False
    },
    "💰 Finance": {
        "keywords": [
            "Finance Manager", "Financial Analyst",
            "Accountant", "CFO",
            "Financial Controller", "Investment Analyst",
        ],
        "industries": ["Financial Services", "Banking"],
        "include": "",
        "remote": False
    },
    "📣 Marketing": {
        "keywords": [
            "Marketing Manager", "Digital Marketing Manager",
            "Brand Manager", "Content Manager",
            "Social Media Manager", "Marketing Director",
        ],
        "industries": ["Marketing & Advertising"],
        "include": "",
        "remote": False
    },
    "🔧 Operations": {
        "keywords": [
            "Operations Manager", "Supply Chain Manager",
            "Procurement Manager", "Logistics Manager",
            "Project Manager", "General Manager",
        ],
        "industries": ["Logistics & Supply Chain"],
        "include": "",
        "remote": False
    },
    "🏋️ Fitness": {
        "keywords": [
            "Personal Trainer", "Fitness Trainer",
            "Fitness Coach", "Fitness Manager",
            "Gym Instructor", "Group Fitness Instructor",
        ],
        "industries": ["Any industry"],
        "include": "",
        "remote": False
    },
}

LOCATION_OPTIONS = [
    "United Arab Emirates", "Dubai", "Abu Dhabi", "Sharjah",
    "Saudi Arabia", "Qatar", "Oman", "Kuwait", "Bahrain",
    "Middle East", "Remote", "Worldwide"
]

FRESHNESS_MAP = {
    "Past hour": 3600,
    "Past 24 hours": 86400,
    "Past week": 604800,
    "Past month": 2592000,
    "Any time": None
}

DELAY_RANGES = {
    "Fast (higher block risk)": (0.5, 1.5),
    "Normal": (1.5, 3.5),
    "Slow (fewer blocks)": (3.0, 6.0),
}


# =========================================================
# Helpers
# =========================================================

def clean_text(value):
    if not value: return ""
    return " ".join(value.replace("\n", " ").split())

def parse_posted_datetime(value):
    if not value: return pd.NaT
    try:
        return pd.to_datetime(value, utc=True, errors="raise")
    except Exception:
        pass
    v = str(value).lower()
    now = pd.Timestamp.utcnow()
    try:
        n = int(re.search(r"(\d+)", v).group(1)) if re.search(r"(\d+)", v) else 1
        if "minute" in v:  return now - pd.Timedelta(minutes=n)
        if "hour"   in v:  return now - pd.Timedelta(hours=n)
        if "day"    in v:  return now - pd.Timedelta(days=n)
        if "week"   in v:  return now - pd.Timedelta(weeks=n)
        if "month"  in v:  return now - pd.Timedelta(days=n * 30)
    except Exception:
        pass
    return pd.NaT

def build_url(keyword, location, freshness_seconds, start, industry_ids):
    k = urllib.parse.quote_plus(keyword)
    l = urllib.parse.quote_plus(location)
    url = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        f"?keywords={k}&location={l}&start={start}&sortBy=DD"
    )
    if freshness_seconds: url += f"&f_TPR=r{freshness_seconds}"
    if industry_ids:      url += f"&f_I={urllib.parse.quote_plus(','.join(industry_ids))}"
    return url

def is_blocked_response(status_code, html):
    if status_code == 999:              return True, "Status 999 (bot detected)"
    if status_code == 429:              return True, "Rate limited (429)"
    if status_code not in (200, 201):   return True, f"Status {status_code}"
    if len(html) < 500:                 return True, f"Too short ({len(html)} chars)"
    for sig in ["challenge?", "authwall", "checkpoint", "captcha", "please verify", "too many requests"]:
        if sig in html.lower():         return True, f"Block page ('{sig}')"
    return False, ""

def _tag_text(html_fragment):
    """Strip all HTML tags and decode common entities."""
    text = re.sub(r"<[^>]+>", " ", html_fragment or "")
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">") \
               .replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    return clean_text(text)

def _attr(tag_html, attr):
    """Extract an attribute value from a tag string."""
    m = re.search(rf'{attr}=["\']([^"\']*)["\']', tag_html or "")
    return m.group(1) if m else ""

def parse_jobs(html, keyword, industry_label, collection):
    jobs = []
    # Split into <li> blocks
    li_blocks = re.split(r"<li[\s>]", html)
    for block in li_blocks[1:]:  # skip content before first <li>
        # Title — h3 with base-search-card__title or just h3
        title = ""
        m = re.search(r'<h3[^>]*class="[^"]*base-search-card__title[^"]*"[^>]*>(.*?)</h3>', block, re.S)
        if not m:
            m = re.search(r'<h3[^>]*>(.*?)</h3>', block, re.S)
        if m:
            title = _tag_text(m.group(1))

        # Company — h4
        company = ""
        m = re.search(r'<h4[^>]*class="[^"]*base-search-card__subtitle[^"]*"[^>]*>(.*?)</h4>', block, re.S)
        if not m:
            m = re.search(r'<h4[^>]*>(.*?)</h4>', block, re.S)
        if m:
            company = _tag_text(m.group(1))

        # Location
        loc = ""
        m = re.search(r'<span[^>]*class="[^"]*(?:job-search-card__location|base-search-card__metadata)[^"]*"[^>]*>(.*?)</span>', block, re.S)
        if m:
            loc = _tag_text(m.group(1))

        # Link — base-card__full-link or first <a href>
        url = ""
        m = re.search(r'<a[^>]*class="[^"]*base-card__full-link[^"]*"[^>]*href="([^"]+)"', block)
        if not m:
            m = re.search(r'<a[^>]*href="(https://[^"]*linkedin\.com/jobs/view/[^"]+)"', block)
        if m:
            url = m.group(1).split("?")[0]

        # Posted time
        posted_text = ""
        posted_raw  = ""
        m = re.search(r'<time[^>]*>(.*?)</time>', block, re.S)
        if m:
            posted_text = _tag_text(m.group(1))
            dt = re.search(r'datetime="([^"]+)"', block)
            posted_raw = dt.group(1) if dt else posted_text

        if not title or not url:
            continue

        job_id_m = re.search(r"/jobs/view/(\d+)", url)
        jobs.append({
            "Job ID":          job_id_m.group(1) if job_id_m else url,
            "Title":           title,
            "Company":         company,
            "Location":        loc,
            "Posted":          posted_text,
            "Posted Date":     posted_raw,
            "Search Keyword":  keyword,
            "Collection":      collection,
            "Industry Filter": industry_label,
            "URL":             url,
        })
    return jobs

def fetch_jobs(keyword, location, freshness_seconds, pages, industry_ids, industry_label, collection, delay_range=(1.5, 3.5)):
    results, diagnostics, block_count = [], [], 0
    for page in range(pages):
        url = build_url(keyword, location, freshness_seconds, page * 25, industry_ids)
        try:
            r = requests.get(url, headers=get_headers(), timeout=25)
            html = r.text
            blocked, reason = is_blocked_response(r.status_code, html)
            jobs = [] if blocked else parse_jobs(html, keyword, industry_label, collection)
            diagnostics.append({
                "keyword": keyword, "collection": collection, "industry": industry_label,
                "page": page + 1, "status": r.status_code, "html_length": len(html),
                "jobs_parsed": len(jobs), "blocked": blocked, "block_reason": reason, "url": url
            })
            results.extend(jobs)
            time.sleep(random.uniform(*(3.0, 6.0) if blocked else delay_range))
            if blocked: block_count += 1
        except Exception as e:
            diagnostics.append({
                "keyword": keyword, "collection": collection, "industry": industry_label,
                "page": page + 1, "status": "error", "html_length": 0,
                "jobs_parsed": 0, "blocked": True, "block_reason": str(e), "url": url
            })
            block_count += 1
            time.sleep(random.uniform(2.0, 4.0))
    return results, diagnostics, block_count

def make_keywords(main_query, extra_queries_text, selected_collection, active_keywords=None):
    kw = []
    if main_query.strip(): kw.append(main_query.strip())
    kw.extend([x.strip() for x in extra_queries_text.splitlines() if x.strip()])
    if selected_collection != "Custom search":
        kw.extend(active_keywords or JOB_COLLECTIONS[selected_collection]["keywords"])
    return list(dict.fromkeys(kw))

def score_job(row, search_terms, include_words, selected_collection):
    text = f"{row.get('Title','')} {row.get('Company','')} {row.get('Location','')} {row.get('Industry Filter','')}".lower()
    score = 50
    for t in search_terms:
        if t.lower().strip() and t.lower().strip() in text: score += 12
    for w in include_words:
        if w.lower().strip() and w.lower().strip() in text: score += 8
    for t in ["senior","lead","manager","head","director","principal","specialist","consultant","architect","owner"]:
        if t in text: score += 3
    if selected_collection != "Custom search": score += 5
    for t in ["intern","internship","graduate","trainee"]:
        if t in text: score -= 20
    return max(0, min(score, 100))

def contains_any(text, words):
    return any(w.lower() in text.lower() for w in words if w) if words else True

def contains_all(text, words):
    return all(w.lower() in text.lower() for w in words if w) if words else True

def apply_filters(df, include_words, require_all, exclude_words, company_text, result_location_text, min_score):
    if df.empty: return df
    df = df.copy()
    combined = df["Title"].fillna("") + " " + df["Company"].fillna("") + " " + df["Location"].fillna("") + " " + df["Industry Filter"].fillna("")
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
    return df[df["AI Match Score"] >= min_score]


# =========================================================
# ── UI ──
# =========================================================

# Hero
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">LinkedIn Jobs Hunter · UAE & Middle East</div>
  <div class="hero-title">Find fresh roles.<br><em>Before everyone else.</em></div>
  <div class="hero-sub">A clean LinkedIn job scanner with collections, filters, scoring and CSV export.</div>
</div>
""", unsafe_allow_html=True)

# ── 01 Collections ──
st.markdown('<span class="slabel">01 &nbsp;—&nbsp; Collection</span>', unsafe_allow_html=True)

collection_options = ["Custom search"] + list(JOB_COLLECTIONS.keys())
selected_collection = st.radio(
    "collection", collection_options,
    horizontal=True, label_visibility="collapsed"
)

if selected_collection != "Custom search":
    cdata = JOB_COLLECTIONS[selected_collection]
    st.markdown(
        f'<div class="kw-banner"><div class="kw-banner-label">'
        f'{selected_collection} &nbsp;·&nbsp; {len(cdata["keywords"])} roles — click × to remove any</div>',
        unsafe_allow_html=True
    )
    active_keywords = st.multiselect(
        "active_kw", options=cdata["keywords"], default=cdata["keywords"],
        key=f"kw_select_{selected_collection}_v8", label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    active_keywords = []

st.markdown('<hr class="sdivider">', unsafe_allow_html=True)

# ── 02 Search ──
st.markdown('<span class="slabel">02 &nbsp;—&nbsp; Search</span>', unsafe_allow_html=True)

c1, c2 = st.columns([3, 1])
with c1:
    main_query = st.text_input(
        "Role / job title",
        value="",
        placeholder="e.g. Product Manager, ERP Consultant, Digital Transformation Lead",
        key="main_query_input"
    )
with c2:
    location = st.selectbox("Location", LOCATION_OPTIONS, index=0, key="location_select")

c3, c4, c5 = st.columns(3)
with c3:
    freshness = st.selectbox("Posted within", list(FRESHNESS_MAP.keys()), index=1, key="freshness_select")
with c4:
    default_industries = JOB_COLLECTIONS[selected_collection]["industries"] if selected_collection != "Custom search" else ["Any industry"]
    selected_industries = st.multiselect("Industry", list(INDUSTRY_MAP.keys()), default=default_industries, key="industry_select")
with c5:
    sort_mode = st.selectbox("Sort by", ["Newest first", "Match score first"], index=0, key="sort_select")

extra_queries_text = st.text_area(
    "Extra keywords (one per line)",
    value="", placeholder="Senior Product Manager\nAI Product Owner",
    height=80, key="extra_queries_text"
)

st.markdown('<hr class="sdivider">', unsafe_allow_html=True)

# ── 03 Advanced filters ──
with st.expander("⚙  Filters & settings"):
    fa, fb, fc = st.columns(3)
    with fa:
        include_text = st.text_input("Must include", value="", placeholder="e.g. AI, ERP", key="include_text_stable")
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
        min_score = st.slider("Min match score", 0, 100, 35, key="min_score")

    fg, fh = st.columns(2)
    with fg:
        pages = st.slider("Pages per keyword", 1, 5, 2, key="pages")
    with fh:
        delay_mode = st.selectbox("Request delay", list(DELAY_RANGES.keys()), index=1, key="delay_mode")

    show_diagnostics = st.checkbox("Show diagnostics", value=False, key="diagnostics")

delay_range = DELAY_RANGES[delay_mode]

# Derived
keywords      = make_keywords(main_query, extra_queries_text, selected_collection, active_keywords)
include_words = [x.strip() for x in include_text.split(",") if x.strip()]
exclude_words = [x.strip() for x in exclude_text.split(",") if x.strip()]

if not selected_industries: selected_industries = ["Any industry"]
if "Any industry" in selected_industries and len(selected_industries) > 1:
    selected_industries = [x for x in selected_industries if x != "Any industry"]

industry_ids   = [INDUSTRY_MAP[x] for x in selected_industries if INDUSTRY_MAP.get(x)]
industry_label = ", ".join(selected_industries)

if selected_collection == "🎧 IT" and pages > 1:
    st.warning("⚠️ IT collection has many keywords. Consider Slow delay or 1 page to reduce LinkedIn blocks.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Search button ──
if st.button("🔎  Find Opportunities", type="primary", use_container_width=True):
    if not keywords:
        st.error("Enter a job title, add extra searches, or choose a collection.")
        st.stop()

    all_jobs, all_diag, total_blocks = [], [], 0
    seen_ids    = set()
    progress    = st.progress(0)
    status_text = st.empty()

    for idx, keyword in enumerate(keywords):
        status_text.markdown(
            f'<p style="font-family:\'Outfit\',sans-serif;font-size:11px;letter-spacing:0.1em;'
            f'text-transform:uppercase;color:#6a8caa;margin:4px 0;">'
            f'Searching {idx+1}/{len(keywords)}: '
            f'<span style="color:#1a6bb5;font-weight:600;">{keyword}</span></p>',
            unsafe_allow_html=True
        )
        jobs, diag, bc = fetch_jobs(
            keyword=keyword, location=location,
            freshness_seconds=FRESHNESS_MAP[freshness], pages=pages,
            industry_ids=industry_ids, industry_label=industry_label,
            collection=selected_collection, delay_range=delay_range
        )
        for job in jobs:
            if job["Job ID"] not in seen_ids:
                seen_ids.add(job["Job ID"])
                all_jobs.append(job)
        all_diag.extend(diag)
        total_blocks += bc
        progress.progress((idx + 1) / len(keywords))

    status_text.empty()

    total_req = max(len(all_diag), 1)
    if total_blocks > 0:
        bp = round(100 * total_blocks / total_req)
        if   bp >= 50: st.error(f"🚫 LinkedIn blocked {total_blocks}/{total_req} requests ({bp}%). Try Slow delay or wait before retrying.")
        elif bp >= 20: st.warning(f"⚠️ {total_blocks}/{total_req} requests blocked ({bp}%). Some results may be missing.")
        else:          st.info(f"ℹ️ {total_blocks}/{total_req} minor blocks. Results may be slightly incomplete.")

    if show_diagnostics:
        st.dataframe(pd.DataFrame(all_diag), use_container_width=True, hide_index=True)

    if not all_jobs:
        st.error("No jobs found. LinkedIn may have blocked all requests. Try Slow delay mode or simpler keywords.")
        st.stop()

    df = pd.DataFrame(all_jobs)
    df["Posted Parsed"] = df["Posted Date"].apply(parse_posted_datetime)
    df["AI Match Score"] = df.apply(lambda r: score_job(r, keywords, include_words, selected_collection), axis=1)

    before_filter = len(df)
    filtered_df   = apply_filters(df, include_words, require_all, exclude_words, company_text, result_location_text, min_score)
    after_filter  = len(filtered_df)

    if filtered_df.empty:
        st.warning(f"Found {before_filter} jobs but 0 after filters. Try reducing min score or removing include words.")
        st.dataframe(
            df.sort_values("Posted Parsed", ascending=False, na_position="last")
              [["Posted Date","Posted","AI Match Score","Title","Company","Location","URL"]],
            use_container_width=True, hide_index=True
        )
        st.stop()

    if sort_mode == "Newest first":
        filtered_df = filtered_df.sort_values(["Posted Parsed","AI Match Score"], ascending=[False,False], na_position="last")
    else:
        filtered_df = filtered_df.sort_values(["AI Match Score","Posted Parsed"], ascending=[False,False], na_position="last")

    # Results summary
    st.markdown('<hr class="sdivider">', unsafe_allow_html=True)
    st.success(f"✅ {before_filter} jobs found · {after_filter} matched your filters")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matched", after_filter)
    m2.metric("Total found", before_filter)
    m3.metric("Best score", int(filtered_df["AI Match Score"].max()))
    valid_dates = filtered_df["Posted Parsed"].dropna()
    m4.metric("Newest", valid_dates.iloc[0].strftime("%b %d, %H:%M") if not valid_dates.empty else "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    # Results table
    st.markdown(f'<span class="slabel">Results — {sort_mode}</span>', unsafe_allow_html=True)
    display_cols = ["Posted Date","Posted","AI Match Score","Title","Company","Location","Collection","Search Keyword","Industry Filter","URL"]
    st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

    # Job cards
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="slabel">Top 15 cards</span>', unsafe_allow_html=True)

    for _, row in filtered_df.head(15).iterrows():
        score      = int(row["AI Match Score"])
        s_color    = "#1a6bb5" if score >= 70 else "#a8c8e8"
        parsed     = row.get("Posted Parsed")
        date_label = parsed.strftime("%b %d, %Y") if pd.notna(parsed) else (row["Posted Date"] or "—")

        st.markdown(f"""
        <div class="job-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:24px;">
            <div style="flex:1;min-width:0;">
              <div class="job-title">{row['Title']}</div>
              <div class="job-meta">{row['Company'] or '—'} &nbsp;·&nbsp; {row['Location'] or '—'}</div>
              <span class="job-tag">{row['Collection']}</span>
              <span class="job-tag">{row['Search Keyword']}</span>
              <span class="job-tag">{date_label}</span>
              <div style="margin-top:16px;">
                <a class="job-link" href="{row['URL']}" target="_blank">View on LinkedIn →</a>
              </div>
            </div>
            <div style="text-align:right;min-width:52px;flex-shrink:0;">
              <div class="score-num" style="color:{s_color};">{score}</div>
              <div style="font-family:'Outfit',sans-serif;font-size:9px;color:#6a8caa;letter-spacing:0.16em;text-transform:uppercase;margin-top:2px;">score</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Download
    st.markdown("<br>", unsafe_allow_html=True)
    csv = filtered_df.drop(columns=["Posted Parsed"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Download CSV",
        csv,
        file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )

st.markdown('<hr class="sdivider">', unsafe_allow_html=True)
st.markdown(
    '<p style="font-family:\'Outfit\',sans-serif;font-size:10px;color:#a8c8e8;letter-spacing:0.16em;text-transform:uppercase;">'
    'JOBS HUNTER v8 &nbsp;·&nbsp; azure blue interface · saved jobs next</p>',
    unsafe_allow_html=True
)