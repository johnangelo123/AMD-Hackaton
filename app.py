import streamlit as st
import PyPDF2
import os
import csv
import io
import json
import re
from dotenv import load_dotenv
import base64

client = OpenAI(
    base_url="http://134.199.196.135:8000/v1", 
    api_key="sk-no-key-required"
)
load_dotenv()

MODEL_NAME = 'meta-llama/Meta-Llama-3-8B-Instruct'

def normalize_anki_text(raw_text):
    normalized_lines = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if '\t' in line:
            normalized_lines.append(line)
            continue
        if line.startswith('"') and line.endswith('"') and '","' in line:
            parts = line.split('","', 1)
            term = parts[0].strip('" ')
            definition = parts[1].rstrip('" ').strip()
            normalized_lines.append(f"{term}\t{definition}")
            continue
        if '","' in line:
            parts = line.split('","', 1)
            term = parts[0].strip('" ')
            definition = parts[1].rstrip('" ').strip()
            normalized_lines.append(f"{term}\t{definition}")
            continue
        if line.count(',') >= 1:
            first_comma = line.find(',')
            term = line[:first_comma].strip('" ')
            definition = line[first_comma + 1 :].strip('" ')
            normalized_lines.append(f"{term}\t{definition}")
            continue
        normalized_lines.append(line)
    return "\n".join(normalized_lines)


def parse_flashcard_text(raw_text):
    rows = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('```') or line.lower().startswith('csv:'):
            continue
        if line.startswith('>'):
            line = line.lstrip('> ').strip()
        if line.lower().startswith('term') and 'definition' in line.lower():
            continue
        if '||' in line:
            parts = line.split('||', 1)
        elif '::' in line:
            parts = line.split('::', 1)
        else:
            continue
        term = parts[0].strip().strip('"')
        definition = parts[1].strip().strip('"')
        if term and definition:
            rows.append([term, definition])
    if not rows:
        return ""

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL, lineterminator='\n')
    for term, definition in rows:
        writer.writerow([term, definition])
    return output.getvalue().strip()

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

bg_image_path = "backgroundsample.png"
if os.path.exists(bg_image_path):
    bg_image_base64 = get_base64_image(bg_image_path)
    bg_image_url = f"data:image/png;base64,{bg_image_base64}"
else:
    bg_image_url = ""


st.set_page_config(page_title="Syllabus-to-Calendar Agent | AMD.AI", page_icon="📅", layout="wide")

if "current_page" not in st.session_state:
    st.session_state.current_page = "calendar"

st.markdown(f"""
<style>
    .stApp {{
        background-image: url('{bg_image_url}');
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<style>
    :root {
        --primary: #DC2626;
        --primary-light: #FEE2E2;
        --primary-dark: #991B1B;
        --accent: #7C3AED;
        --surface: rgba(255,255,255,0.95);
        --surface-card: #FFFFFF;
        --border: #E5E7EB;
        --text-primary: #1F2937;
        --text-secondary: #6B7280;
    }

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    .stAppViewContainer {
        padding-top: 0 !important;
    }

    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        z-index: 0;
        background: rgba(255,255,255,0.85);
        pointer-events: none;
    }

    .main {
        padding-top: 0 !important;
    }

    .main .block-container {
        position: relative;
        z-index: 2;
        max-width: 980px;
        padding: 0 2rem 4rem;
        margin-top: -8rem !important;
    }

    .nav-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2.5rem;
        margin-top: 0;
        background: var(--surface-card);
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    .nav-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 700;
        color: var(--primary-dark);
        letter-spacing: 0.02em;
    }

    .nav-logo-dot {
        width: 8px;
        height: 8px;
        background: var(--primary);
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(220,38,38,0.4);
        animation: pulse 2s infinite;
    }

    @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.5} }

    .nav-badge {
        font-family: 'Inter', sans-serif;
        font-size: 11px;
        font-weight: 600;
        color: var(--primary);
        border: 1px solid var(--primary);
        padding: 6px 14px;
        border-radius: 20px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        background: rgba(220,38,38,0.05);
    }

    .header-nav {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .header-nav-button {
        padding: 0.85rem 1rem;
        border-radius: 999px;
        background: #FFFFFF;
        border: 1px solid rgba(220,38,38,0.15);
        color: var(--primary-dark);
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 700;
        text-decoration: none;
        letter-spacing: 0.04em;
        transition: all 0.2s ease;
    }

    .header-nav-button:hover {
        background: rgba(220,38,38,0.08);
        border-color: var(--primary);
        color: var(--primary);
    }

    .header-nav-button.active {
        background: var(--primary);
        color: white;
        border-color: var(--primary);
    }

    .hero-tag {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: var(--primary);
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .hero-tag::before {
        content: '';
        display: block;
        width: 20px;
        height: 2px;
        background: var(--primary);
        border-radius: 1px;
    }

    .hero-title {
        font-size: clamp(2rem, 4vw, 3.5rem);
        font-weight: 700;
        line-height: 1.1;
        letter-spacing: -0.01em;
        margin-bottom: 1rem;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    .hero-title .accent {
        color: var(--primary);
        display: block;
    }

    .hero-sub {
        font-size: 1rem;
        color: var(--text-secondary);
        max-width: 520px;
        line-height: 1.6;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    .hero-visual {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }

    .hero-step-card {
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 120px;
        min-height: 120px;
        padding: 1.25rem;
        border-radius: 24px;
        background: rgba(255,255,255,0.9);
        box-shadow: 0 16px 40px rgba(0,0,0,0.08);
        border: 1px solid rgba(229,231,235,0.9);
        text-align: center;
    }

    .hero-step-card span {
        display: block;
        font-size: 2.25rem;
        margin-bottom: 0.75rem;
    }

    .hero-step-card p {
        margin: 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-weight: 600;
    }

    .hero-arrow {
        font-size: 2.5rem;
        color: var(--primary);
    }

    .instructions-panel {
        margin-top: 2.5rem;
        padding: 2rem;
        border-radius: 20px;
        background: rgba(255,255,255,0.95);
        border: 1px solid rgba(229,231,235,0.9);
        box-shadow: 0 20px 40px rgba(0,0,0,0.06);
    }

    .instructions-title {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: var(--primary-dark);
        margin-bottom: 1rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .instructions-step {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: var(--text-secondary);
        margin-bottom: 0.75rem;
        line-height: 1.6;
    }

    .instructions-step strong {
        color: var(--primary-dark);
    }

    .stats-container {
        display: flex;
        gap: 3rem;
        margin-bottom: 2.5rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid var(--border);
    }

    .stat {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--primary);
    }

    .stat-label {
        font-family: 'Inter', sans-serif;
        font-size: 11px;
        font-weight: 500;
        color: var(--text-secondary);
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .section-label {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 2rem;
    }

    .section-label::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    .stFileUploader {
        position: relative;
        background: var(--surface-card) !important;
        border: 2px dashed var(--primary-light) !important;
        border-radius: 8px !important;
        padding: 0 !important;
        transition: all 0.2s;
    }

    .stFileUploader:hover {
        border-color: var(--primary) !important;
        background: rgba(220,38,38,0.02) !important;
    }

    .stFileUploader > div:first-child {
        padding: 3rem 2rem !important;
        text-align: center;
    }

    .stFileUploader label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }

    .stFileUploader [data-testid="stMarkdownContainer"] p {
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        letter-spacing: 0 !important;
        text-shadow: none !important;
    }

    .stAlert {
        background: rgba(220,38,38,0.08) !important;
        border: 1px solid rgba(220,38,38,0.3) !important;
        border-radius: 8px !important;
        color: var(--primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        letter-spacing: 0;
    }

    .stAlert [data-testid="stMarkdownContainer"] p {
        color: var(--primary) !important;
        text-shadow: none !important;
    }

    .result-panel {
        position: relative;
        border: 1px solid var(--border);
        border-radius: 8px;
        background: var(--surface-card);
        overflow: hidden;
        margin-top: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }

    .result-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.5rem;
        border-bottom: 1px solid var(--border);
        position: relative;
        z-index: 1;
        background: rgba(220,38,38,0.03);
    }

    .result-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 700;
        color: var(--primary);
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .result-title::before {
        content: '';
        width: 8px;
        height: 8px;
        background: var(--primary);
        border-radius: 50%;
    }

    .result-body {
        padding: 1.5rem;
        position: relative;
        z-index: 1;
        max-height: 400px;
        overflow-y: auto;
        background: #FFFFFF;
    }

    .result-body pre {
        color: var(--text-primary) !important;
        background: #FFFFFF !important;
        padding: 1rem;
        border-radius: 4px;
        border: 1px solid var(--border);
        overflow-x: auto;
        font-family: 'Courier New', monospace !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
        margin: 0 !important;
    }

    .result-body::-webkit-scrollbar {
        width: 6px;
    }

    .result-body::-webkit-scrollbar-track {
        background: rgba(0,0,0,0.05);
        border-radius: 3px;
    }

    .result-body::-webkit-scrollbar-thumb {
        background: var(--primary);
        border-radius: 3px;
    }

    .stCodeBlock {
        background: transparent !important;
        border: none !important;
    }

    .stCodeBlock code {
        font-family: 'Inter', monospace !important;
        font-size: 13px !important;
        color: var(--text-primary) !important;
        line-height: 1.6 !important;
        text-shadow: none !important;
    }

    div[data-testid="stDownloadButton"] button,
    div[data-testid="stButton"] button {
        display: inline-flex !important;
        align-items: center;
        gap: 10px;
        background: var(--primary) !important;
        border: none !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 0.75rem 1.75rem !important;
        border-radius: 6px !important;
        transition: all 0.2s;
        position: relative;
        overflow: hidden;
        margin-top: 1.5rem;
        box-shadow: 0 2px 8px rgba(220,38,38,0.2) !important;
    }

    div[data-testid="stDownloadButton"] button:hover,
    div[data-testid="stButton"] button:hover {
        background: var(--primary-dark) !important;
        box-shadow: 0 4px 12px rgba(220,38,38,0.3) !important;
        transform: translateY(-1px);
    }

    .features-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 2.5rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border);
    }

    .chip {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        padding: 8px 14px;
        border: 1px solid var(--border);
        border-radius: 6px;
        color: var(--text-secondary);
        background: var(--surface-card);
        transition: all 0.2s;
    }

    .chip:hover {
        border-color: var(--primary);
        color: var(--primary);
        background: var(--primary-light);
    }

    .page-footer {
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border);
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 500;
        color: var(--text-secondary);
        letter-spacing: 0.03em;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .footer-dot {
        display: inline-block;
        width: 4px;
        height: 4px;
        background: var(--primary);
        border-radius: 50%;
        margin: 0 8px;
        vertical-align: middle;
    }

    .spinner {
        width: 14px;
        height: 14px;
        border: 2px solid rgba(220,38,38,0.2);
        border-top-color: var(--primary);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        flex-shrink: 0;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .file-badge {
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(220,38,38,0.05);
        border: 1px solid var(--primary-light);
        border-radius: 6px;
        padding: 0.75rem 1rem;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 1rem;
    }

    .file-badge-name {
        color: var(--text-primary);
        font-weight: 600;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* New Layout Styles */
    #sticky-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 2rem;
        background: var(--surface-card);
        border-bottom: 1px solid var(--border);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    #main-layout {
        display: grid;
        grid-template-columns: 1fr 300px;
        gap: 2rem;
        margin-top: 80px; /* Height of sticky header */
        padding: 0 2rem;
    }

    #main-content {
        max-width: 980px;
        margin: 0 auto;
    }

    #sidebar {
        position: sticky;
        top: 100px;
        height: fit-content;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .sidebar-btn {
        padding: 1rem 1.5rem;
        background: var(--surface-card);
        border: 2px solid var(--border);
        border-radius: 8px;
        color: var(--text-secondary);
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 600;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .sidebar-btn:hover {
        border-color: var(--primary);
        color: var(--primary);
    }

    .sidebar-btn.active {
        border-color: var(--primary);
        background: var(--primary-light);
        color: var(--primary);
    }

    #calendar-page, #anki-page {
        /* Content containers */
    }
</style>
""", unsafe_allow_html=True)


params = st.query_params if hasattr(st, "query_params") else {}
if "page" in params:
    page = params["page"][0] if isinstance(params["page"], list) else params["page"]
    if page in ["calendar", "anki"]:
        st.session_state.current_page = page

st.markdown("""
<div id="sticky-header">
    <div class="nav-logo">
        <div class="nav-logo-dot"></div>
        AMD.AI
    </div>
    <div class="header-nav">
        <a href="?page=calendar" target="_self" class="header-nav-button{active_calendar}">📅 Syllabus</a>
        <a href="?page=anki" target="_self" class="header-nav-button{active_anki}">📝 Anki</a>
    </div>
    <div class="nav-badge">Agent Active</div>
</div>
""".format(
    active_calendar=" active" if st.session_state.current_page == "calendar" else "",
    active_anki=" active" if st.session_state.current_page == "anki" else ""
), unsafe_allow_html=True)

if st.session_state.current_page == "calendar":
    st.markdown("""
    <div id="main-layout">
        <div id="main-content">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-tag">AI-Powered Deadline Extractor</div>
    <div class="hero-title">
        Syllabus
        <span class="accent">To Calendar</span>
        Agent
    </div>
    <p class="hero-sub">
        Drop your class syllabus. Our AI neural core extracts every deadline and exports a ready-to-import Google Calendar CSV — in under a minute.
    </p>
    <div class="hero-visual">
        <div class="hero-step-card">
            <span>📄</span>
            <p>Upload your syllabus PDF</p>
        </div>
        <div class="hero-arrow">→</div>
        <div class="hero-step-card">
            <span>📊</span>
            <p>Extract clean CSV data</p>
        </div>
        <div class="hero-arrow">→</div>
        <div class="hero-step-card">
            <span>📅</span>
            <p>Import to Google Calendar</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stats-container">
        <div class="stat"><span class="stat-value">100%</span><span class="stat-label">Deadline Coverage</span></div>
        <div class="stat"><span class="stat-value">&lt; 1m</span><span class="stat-label">Extraction Time</span></div>
        <div class="stat"><span class="stat-value">GCal</span><span class="stat-label">Ready Export</span></div>
        <div class="stat"><span class="stat-value">0</span><span class="stat-label">Missed Deadlines</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">01 — Upload Syllabus</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Drop your syllabus PDF here", type="pdf", label_visibility="collapsed")

    if uploaded_file is not None:
        st.markdown(f"""
        <div class="file-badge">
            📄 <span class="file-badge-name">{uploaded_file.name}</span>
            <span style="margin-left:auto;color:var(--primary);font-size:10px;letter-spacing:0.1em;">LOADED</span>
        </div>
        """, unsafe_allow_html=True)

        status_extract = st.empty()
        status_analyze = st.empty()

        with st.spinner("Reading PDF and extracting text…"):
            status_extract.markdown("""
            <div style="display:flex;align-items:center;gap:10px;margin-top:1rem;color:#DC2626;font-family:'Inter',sans-serif;font-size:12px;">
                <div class="spinner"></div>
                <span>Reading PDF and extracting text…</span>
            </div>
            """, unsafe_allow_html=True)

            reader = PyPDF2.PdfReader(uploaded_file)
            syllabus_text = ""
            for page in reader.pages:
                syllabus_text += page.extract_text()

        status_extract.empty()

        prompt = """CRITICAL: Output ONLY CSV data. Nothing else. No intro text, no explanation, no preamble.

The VERY FIRST LINE of your output must be the header row. The VERY FIRST CHARACTER must be the 'S' in Subject.

Header row (line 1):
Subject,Start Date,Start Time,End Date,End Time,All Day Event,Description,Location,Private

Then data rows, each with exactly 9 comma-separated quoted fields:
"Assignment 1: CPU Scheduling","10/12/2026","","10/12/2026","",TRUE,"Submit C++ code and brief report analyzing efficiency of your Round Robin implementation.","",""

STRICT RULES:
- NO text before the header
- NO blank lines
- NO explanations
- First character = 'S' from Subject
- Every field quoted except TRUE/FALSE
- 8 commas per row (9 fields)
- Dates: MM/DD/YYYY

Extract all deadlines from syllabus:

""" + syllabus_text

        with st.spinner("Neural core analyzing deadlines…"):
            status_analyze.markdown("""
            <div style="display:flex;align-items:center;gap:10px;margin-top:1rem;color:#DC2626;font-family:'Inter',sans-serif;font-size:12px;">
                <div class="spinner"></div>
                <span>Neural core analyzing deadlines…</span>
            </div>
            """, unsafe_allow_html=True)

            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500
                )
                ai_csv_data = response.choices[0].message.content

                status_analyze.empty()
                st.success("✓ Schedule extracted successfully — ready to download")

                st.markdown('<div class="section-label" style="margin-top:2rem;">02 — Extracted Schedule</div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div class="result-panel">
                    <div class="result-header">
                        <div class="result-title">AI Output — CSV Ready</div>
                    </div>
                    <div class="result-body">
                        <pre>{ai_csv_data}</pre>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="↓   Download Google Calendar CSV",
                        data=ai_csv_data,
                        file_name="my_schedule.csv",
                        mime="text/csv"
                    )
            
            except Exception as e:
                status_analyze.empty()
                st.error(f"✗ Error: {str(e)}")

    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.current_page == "anki":
    st.markdown("""
    <div id="main-layout">
        <div id="main-content">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-tag">AI-Powered Flashcard Generator</div>
    <div class="hero-title">
        PDF
        <span class="accent">To Anki</span>
        Flashcards
    </div>
    <p class="hero-sub">
        Drop your syllabus PDF. Our AI extracts key concepts and definitions, creating a ready-to-import Anki deck.
    </p>
    <div class="hero-visual">
        <div class="hero-step-card">
            <span>📄</span>
            <p>Upload your syllabus PDF</p>
        </div>
        <div class="hero-arrow">→</div>
        <div class="hero-step-card">
            <span>🧠</span>
            <p>Extract core concepts</p>
        </div>
        <div class="hero-arrow">→</div>
        <div class="hero-step-card">
            <span>🎓</span>
            <p>Import to Anki</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stats-container">
        <div class="stat"><span class="stat-value">100%</span><span class="stat-label">Concept Coverage</span></div>
        <div class="stat"><span class="stat-value">&lt; 1m</span><span class="stat-label">Extraction Time</span></div>
        <div class="stat"><span class="stat-value">Anki</span><span class="stat-label">Ready Export</span></div>
        <div class="stat"><span class="stat-value">0</span><span class="stat-label">Missed Topics</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">01 — Upload Syllabus</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Drop your syllabus PDF here", type="pdf", label_visibility="collapsed", key="anki_uploader")

    if uploaded_file is not None:
        st.markdown(f"""
        <div class="file-badge">
            📄 <span class="file-badge-name">{uploaded_file.name}</span>
            <span style="margin-left:auto;color:var(--primary);font-size:10px;letter-spacing:0.1em;">LOADED</span>
        </div>
        """, unsafe_allow_html=True)

        status_extract = st.empty()

        with st.spinner("Reading PDF and extracting text…"):
            status_extract.markdown("""
            <div style="display:flex;align-items:center;gap:10px;margin-top:1rem;color:#DC2626;font-family:'Inter',sans-serif;font-size:12px;">
                <div class="spinner"></div>
                <span>Reading PDF and extracting text…</span>
            </div>
            """, unsafe_allow_html=True)

            reader = PyPDF2.PdfReader(uploaded_file)
            syllabus_text = ""
            for page in reader.pages:
                syllabus_text += page.extract_text()

        status_extract.empty()

        if st.button("Generate Anki Flashcards", key="flashcard_btn", use_container_width=True):
            status_flashcard = st.empty()
            with st.spinner("Generating Anki flashcards…"):
                status_flashcard.markdown("""
                <div style="display:flex;align-items:center;gap:10px;margin-top:1rem;color:#DC2626;font-family:'Inter',sans-serif;font-size:12px;">
                    <div class="spinner"></div>
                    <span>AI is generating Anki-friendly terms and definitions…</span>
                </div>
                """, unsafe_allow_html=True)

                flashcard_prompt = """CRITICAL: Output ONLY flashcard data. Nothing else. No intro text, no markdown, no explanations, no code fences.

The output must be line-delimited flashcards with exactly two fields per line: Term and Definition separated by ||.

Example lines:
Round Robin||A CPU scheduling algorithm where processes are given fixed time slices in a circular queue.
Deadlock||A state where two or more processes wait forever because each is holding resources the others need.

STRICT RULES:
- Do NOT include a header row.
- Do NOT include any blank lines.
- Do NOT include any text before or after the flashcard data.
- Use || to separate Term and Definition.
- Terms should be very short and concise (1-4 words).
- Extract ALL key concepts, definitions, and important terms from the entire PDF text.
- Do not skip any important information.

Syllabus Text:
""" + syllabus_text

                try:
                    flashcard_response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[{"role": "user", "content": flashcard_prompt}],
                        max_tokens=4000
                    )
                    flashcard_csv_data = flashcard_response.choices[0].message.content
                    flashcard_text = parse_flashcard_text(flashcard_csv_data)

                    if not flashcard_text:
                        flashcard_text = flashcard_csv_data.strip()

                    status_flashcard.empty()
                    st.success("✓ Anki flashcards created successfully — ready to download")

                    st.markdown('<div class="section-label" style="margin-top:2rem;">02 — Anki Flashcards</div>', unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="result-panel">
                        <div class="result-header">
                            <div class="result-title">Anki CSV — Ready for Import</div>
                        </div>
                        <div class="result-body">
                            <pre>{flashcard_text}</pre>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.download_button(
                        label="↓   Download Anki CSV",
                        data=flashcard_text.encode('utf-8'),
                        file_name="anki_flashcards.csv",
                        mime="text/csv",
                        key="flashcard_download"
                    )
                except Exception as e:
                    status_flashcard.empty()
                    st.error(f"✗ Flashcard Error: {str(e)}")

    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)


if st.session_state.current_page == "calendar":
    st.markdown("""
    <div class="features-container">
        <div class="chip">PDF Extraction</div>
        <div class="chip">AI Parsing</div>
        <div class="chip">Google Calendar CSV</div>
        <div class="chip">MM/DD/YYYY Format</div>
        <div class="chip">Multi-Deadline Detection</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="features-container">
        <div class="chip">PDF Extraction</div>
        <div class="chip">AI Parsing</div>
        <div class="chip">Anki CSV Export</div>
        <div class="chip">Front/Back Fields</div>
        <div class="chip">Ready for Import</div>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.current_page == "calendar":
    st.markdown("""
    <div class="instructions-panel">
        <div class="instructions-title">How to use this web app</div>
        <div class="instructions-step"><strong>1.</strong> Upload your syllabus PDF using the upload box above.</div>
        <div class="instructions-step"><strong>2.</strong> Download the generated Google Calendar CSV file after extraction.</div>
        <div class="instructions-step"><strong>3.</strong> Open Google Calendar, go to <strong>Settings</strong> then <strong>Import & export</strong>, select the CSV file, and import it.</div>
        <div class="instructions-step"><strong>4.</strong> Your deadlines will appear on Google Calendar as all-day events.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="instructions-panel">
        <div class="instructions-title">How to use this web app</div>
        <div class="instructions-step"><strong>1.</strong> Upload your syllabus PDF using the upload box above.</div>
        <div class="instructions-step"><strong>2.</strong> Click <strong>Generate Anki Flashcards</strong> once the file is loaded.</div>
        <div class="instructions-step"><strong>3.</strong> Download the generated CSV file.</div>
        <div class="instructions-step"><strong>4.</strong> Open Anki, go to <strong>File → Import</strong>, select the CSV file, set the field separator to <strong>Comma</strong>, and set the quote character to <strong>"</strong>.</div>
        <div class="instructions-step"><strong>5.</strong> Review the flashcards in Anki and study your extracted terms.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="page-footer">
    <span>AMD.AI<span class="footer-dot"></span>AGENT v2.0</span>
    <span>Created by Angels & Devils Team</span>
    <span>POWERED BY Llama 3</span>            
</div>
""", unsafe_allow_html=True)
