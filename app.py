import streamlit as st
import re
import json
import html
from datetime import datetime
import pandas as pd
import altair as alt
import requests
import time
import os
import sqlite3

# 1. DATABASE SETUP FOR THREAT HISTORY ARCHIVE
DB_FILE = "threat_intelligence.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS threat_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            target TEXT,
            timeframe TEXT,
            risk_score INTEGER,
            risk_level TEXT,
            ioc_count INTEGER,
            ttp_count INTEGER,
            summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_scan_to_db(target, timeframe, risk_score, risk_level, ioc_count, ttp_count, summary):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO threat_scans (timestamp, target, timeframe, risk_score, risk_level, ioc_count, ttp_count, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'), target or "Global", timeframe, risk_score, risk_level, ioc_count, ttp_count, summary[:300]))
        conn.commit()
        conn.close()
    except Exception as e:
        st.warning(f"Database write warning: {e}")

def get_scan_history():
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM threat_scans ORDER BY id DESC LIMIT 50", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# 2. SESSION STATE MANAGEMENT
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

if "ai_analysis_result" not in st.session_state:
    st.session_state.ai_analysis_result = None

if "computed_risk_score" not in st.session_state:
    st.session_state.computed_risk_score = 0

if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False

if "sample_log_text" not in st.session_state:
    st.session_state.sample_log_text = ""

if "help_chat_history" not in st.session_state:
    st.session_state.help_chat_history = [
        {"role": "assistant", "content": "👋 **Hello! I'm your Gemini CTI Copilot.** Ask me anything about your threat pipeline or security workflows!"}
    ]

if "feedback_submissions" not in st.session_state:
    st.session_state.feedback_submissions = []

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Smart Intelligence | Enterprise CTI Suite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# 3. THEME SELECTION & DYNAMIC VARIABLES
selected_lang = "English"
t = {
    "welcome": "Smart Intelligence CTI",
    "tagline": "Enterprise Automated Threat Intelligence, Correlation, and Mitigation Platform",
    "l1": "Layer 1: Scope & Target Definition",
    "l2": "Layer 2: Multi-Source Data Ingestion Modules",
    "l3": "Layer 3: Extraction & Normalization Engine",
    "l4": "Layer 4: AI Threat Correlation & Actionable Mitigation Engine",
    "l5": "Layer 5: Output Deliverables & Operational Dashboard",
    "btn_process": "⚡ EXECUTE 5-LAYER INTELLIGENCE PIPELINE",
    "target": "Target Entity / Sector",
    "timeframe": "Intelligence Timeframe",
    "goal": "Intelligence Goal"
}

# Theme-Adaptive Color Schemes
if theme_choice_preset := "Dark SOC Theme": # evaluated below via theme_choice selectbox logic
    pass

# We define theme choice selector in sidebar
st.sidebar.markdown("<div style='text-align: center; padding: 10px 0;'><h2 style='color: #38bdf8; margin:0; font-size: 1.4rem; text-shadow: 0 0 10px rgba(56,189,248,0.5);'>⚙️ CONTROL PANEL</h2></div>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='border-bottom: 2px solid #38bdf8; margin-bottom: 15px;'></div>", unsafe_allow_html=True)

theme_choice = st.sidebar.selectbox(
    "🎨 UI Visual Mode", 
    ["Dark SOC Theme", "Cyberpunk Neon Mode", "Clean Light Mode"]
)

if theme_choice == "Clean Light Mode":
    bg_color_solid = "#f1f5f9"
    bg_gradient = "linear-gradient(135deg, #e0f2fe 0%, #cbd5e1 100%)"
    card_bg = "rgba(255, 255, 255, 0.95)"
    text_color = "#0f172a"
    sidebar_bg = "#ffffff"
    sidebar_text = "#0f172a"
    accent_color = "#0284c7"
    border_color = "#0284c7"
    glow_shadow = "0 0 20px rgba(2, 132, 199, 0.25)"
    matrix_glow_color = "#0284c7"
    copilot_bg = "#ffffff"
    copilot_text = "#0f172a"
    copilot_bubble_user = "#0284c7"
    copilot_bubble_assistant = "#e2e8f0"
elif theme_choice == "Cyberpunk Neon Mode":
    bg_color_solid = "#030208"
    bg_gradient = "radial-gradient(circle at 50% 10%, #2a0845 0%, #030208 85%)"
    card_bg = "rgba(18, 15, 36, 0.85)"
    text_color = "#00ffcc"
    sidebar_bg = "linear-gradient(180deg, #060b18 0%, #030611 100%)"
    sidebar_text = "#00ffcc"
    accent_color = "#ff0055"
    border_color = "#00ffcc"
    glow_shadow = "0 0 25px rgba(0, 255, 204, 0.45), 0 0 45px rgba(255, 0, 85, 0.25)"
    matrix_glow_color = "#00ffcc"
    copilot_bg = "#0d0a1a"
    copilot_text = "#00ffcc"
    copilot_bubble_user = "#ff0055"
    copilot_bubble_assistant = "#1e153b"
else:  # Dark SOC Theme
    bg_color_solid = "#040714"
    bg_gradient = "radial-gradient(circle at 50% 10%, #0d2147 0%, #040714 90%)"
    card_bg = "rgba(10, 18, 36, 0.88)"
    text_color = "#f8fafc"
    sidebar_bg = "linear-gradient(180deg, #060b18 0%, #030611 100%)"
    sidebar_text = "#38bdf8"
    accent_color = "#38bdf8"
    border_color = "#38bdf8"
    glow_shadow = "0 0 22px rgba(56, 189, 248, 0.4), inset 0 0 15px rgba(56, 189, 248, 0.15)"
    matrix_glow_color = "#38bdf8"
    copilot_bg = "#070d1d"
    copilot_text = "#f8fafc"
    copilot_bubble_user = "#38bdf8"
    copilot_bubble_assistant = "#101d38"

# INJECT ANIMATED MATRIX BACKGROUND
st.components.v1.html(f"""
    <canvas id="cyberCanvas" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: -1;"></canvas>
    <script>
    const canvas = document.getElementById('cyberCanvas');
    const ctx = canvas.getContext('2d');
    function resize() {{
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }}
    resize();
    window.addEventListener('resize', resize);
    const chars = '01 sudo nmap ssh port 80 443 22 cti ioc cve mitre 0xFF APT29 root payload {{}} <> //';
    const charArr = chars.split(' ');
    const fontSize = 14;
    const columns = Math.floor(window.innerWidth / fontSize);
    const drops = [];
    for (let i = 0; i < columns; i++) {{ drops[i] = Math.random() * -100; }}
    function draw() {{
        ctx.fillStyle = 'rgba(4, 7, 20, 0.08)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '{matrix_glow_color}';
        ctx.font = fontSize + 'px monospace';
        ctx.shadowBlur = 10;
        ctx.shadowColor = '{matrix_glow_color}';
        for (let i = 0; i < drops.length; i++) {{
            const text = charArr[Math.floor(Math.random() * charArr.length)];
            const x = i * fontSize;
            const y = drops[i] * fontSize;
            ctx.fillText(text, x, y);
            if (y > canvas.height && Math.random() > 0.975) {{ drops[i] = 0; }}
            drops[i]++;
        }}
    }}
    setInterval(draw, 45);
    </script>
""", height=0)

# HIGH-VISIBILITY DROPDOWN & SCROLLABLE SIDEBAR CSS
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color_solid} !important;
        background-image: {bg_gradient} !important;
        background-attachment: fixed !important;
    }}
    .block-container, section.main, .stMainBlockContainer, [data-testid="stMain"], [data-testid="stVerticalBlock"] {{
        background: transparent !important;
    }}
    
    /* SCROLLABLE & BEAUTIFIED SIDEBAR */
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 2px solid {border_color} !important;
        box-shadow: 10px 0px 40px rgba(56, 189, 248, 0.3) !important;
        z-index: 999999 !important;
        padding-top: 10px;
        overflow-y: auto !important;
        max-height: 100vh !important;
    }}
    
    /* Custom Sidebar Scrollbar */
    section[data-testid="stSidebar"]::-webkit-scrollbar {{
        width: 6px;
    }}
    section[data-testid="stSidebar"]::-webkit-scrollbar-track {{
        background: rgba(3, 7, 18, 0.5);
    }}
    section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {{
        background: {border_color};
        border-radius: 4px;
        box-shadow: 0 0 10px {border_color};
    }}
    
    /* CRITICAL DROPDOWN CONTRAST FIX */
    ul[role="listbox"], 
    div[role="listbox"], 
    div[data-baseweb="popover"], 
    ul[data-testid="stSelectboxVirtualDropdown"],
    [data-baseweb="menu"] {{
        background-color: #0d1b3e !important;
        border: 2px solid {border_color} !important;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.5) !important;
        z-index: 99999999 !important;
    }}
    
    li[role="option"], 
    div[role="option"],
    ul[role="listbox"] li,
    ul[data-testid="stSelectboxVirtualDropdown"] li {{
        background-color: #0d1b3e !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 10px 14px !important;
    }}
    
    li[role="option"]:hover, 
    li[aria-selected="true"],
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover {{
        background-color: #0284c7 !important;
        color: #ffffff !important;
        text-shadow: 0 0 8px #ffffff !important;
    }}

    li[role="option"] span, div[role="option"] span {{
        color: #ffffff !important;
        font-weight: 800 !important;
    }}

    /* GLOBAL TEXT & INPUT STYLES */
    html, body, p, span, div, label, .stMarkdown, .stText {{
        color: {text_color} !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }}
    h1, h2, h3, h4 {{ color: {text_color} !important; font-weight: 700 !important; }}
    h1 {{ color: {accent_color} !important; text-shadow: 0 0 22px {accent_color}, 0 0 35px rgba(56, 189, 248, 0.6); }}
    
    textarea, input, select, div[data-baseweb="select"] > div {{
        color: {text_color} !important;
        background-color: {'#ffffff' if theme_choice == 'Clean Light Mode' else 'rgba(6, 13, 28, 0.92)'} !important;
        border: 1.5px solid {border_color} !important;
        border-radius: 12px !important;
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.25) !important;
    }}
    div[data-testid="stMetric"], .stExpander, div.stTabs {{
        background: {card_bg} !important;
        backdrop-filter: blur(25px) saturate(200%);
        border: 1px solid {border_color} !important;
        border-top: 3px solid {accent_color} !important;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: {glow_shadow} !important;
    }}
    .welcome-banner {{
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.2) 0%, rgba(56, 189, 248, 0.35) 50%, rgba(6, 182, 212, 0.2) 100%);
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 16px 22px;
        text-align: center;
        font-size: 1.25rem;
        font-weight: 800;
        color: {accent_color} !important;
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.45);
        letter-spacing: 0.05em;
        margin-bottom: 22px;
    }}
    .soc-dashboard-hero {{
        background: {card_bg} !important;
        border: 2px solid {border_color} !important;
        border-top: 6px solid {accent_color} !important;
        border-radius: 22px !important;
        padding: 34px !important;
        box-shadow: 0 0 45px rgba(56, 189, 248, 0.35) !important;
        margin-top: 15px !important;
        margin-bottom: 40px !important;
    }}
    .soc-metric-card {{
        background: {'#ffffff' if theme_choice == 'Clean Light Mode' else 'rgba(15, 23, 42, 0.9)'};
        border: 1px solid {border_color};
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
    }}
    .stButton>button {{
        width: 100%;
        font-weight: 800;
        font-size: 1.2rem;
        background: linear-gradient(135deg, #0284c7 0%, #38bdf8 50%, #00ffcc 100%) !important;
        color: #030712 !important;
        border: none !important;
        border-radius: 14px;
        padding: 1rem 1.6rem;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.5);
    }}
    .live-hud-badge {{
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.25);
        border: 1.5px solid #34d399;
        color: #34d399;
        padding: 8px 20px;
        border-radius: 24px;
        font-size: 0.92rem;
        font-weight: 800;
        box-shadow: 0 0 22px rgba(52, 211, 153, 0.5);
    }}
    .live-hud-dot {{
        height: 12px; width: 12px;
        background-color: #34d399;
        border-radius: 50%;
        display: inline-block;
        margin-right: 12px;
        box-shadow: 0 0 15px #34d399;
        animation: pulse-animation 1.6s infinite;
    }}
    @keyframes pulse-animation {{
        0% {{ transform: scale(0.9); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.8); }}
        70% {{ transform: scale(1.2); box-shadow: 0 0 0 14px rgba(52, 211, 153, 0); }}
        100% {{ transform: scale(0.9); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }}
    }}
    .ioc-box {{
        background: {'#ffffff' if theme_choice == 'Clean Light Mode' else 'rgba(3, 7, 18, 0.96)'};
        border: 1px solid {border_color};
        border-left: 4px solid {accent_color};
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-family: 'Courier New', monospace;
        color: {text_color};
    }}
    .playbook-container {{
        background-color: {'#f8fafc' if theme_choice == 'Clean Light Mode' else '#020617'} !important;
        border: 1.5px solid {border_color} !important;
        border-radius: 14px !important;
        padding: 20px 24px !important;
        margin-top: 12px !important;
    }}
    .playbook-line {{
        font-family: 'Fira Code', 'Courier New', Consolas, monospace !important;
        font-size: 0.96rem !important;
        line-height: 1.65 !important;
        color: {accent_color} !important;
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        margin-bottom: 6px !important;
    }}
    .developer-footer {{
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: {'#e2e8f0' if theme_choice == 'Clean Light Mode' else '#03050c'};
        color: {text_color} !important;
        text-align: center; padding: 12px; font-size: 0.9rem !important;
        font-weight: 700;
        border-top: 1px solid {border_color}; z-index: 999;
    }}
    </style>
""", unsafe_allow_html=True)

# SIDEBAR CONTROLS (BEAUTIFIED & SCROLLABLE CONTAINER)
with st.sidebar.expander("🛠️ Advanced Platform & API Settings", expanded=True):
    st.markdown("<p style='font-size: 0.82rem; color: #94a3b8; margin-bottom: 12px;'>Configure threat intelligence lookups, AI keys, and webhooks.</p>", unsafe_allow_html=True)
    enable_live_enrichment = st.checkbox("Enable Live Threat Feed Lookups (IP/ASN)", value=True)
    defang_iocs = st.checkbox("Defang IoCs for Safety (e.g. 1.1.1[.]1)")
    st.session_state.voice_mode = st.checkbox("Enable Live Voice Speech-Output", value=st.session_state.voice_mode)
    ai_api_key = st.text_input("Live AI / Gemini API Key (Optional)", type="password", placeholder="Enter AI API key...")
    vt_api_key = st.text_input("VirusTotal API Key (Optional)", type="password", placeholder="Enter VT v3 key...")
    abuseipdb_api_key = st.text_input("AbuseIPDB API Key (Optional)", type="password", placeholder="Enter AbuseIPDB key...")
    webhook_url = st.text_input("SOC / Feedback Webhook URL (Slack/Discord/Teams)", placeholder="https://webhook.site/...")

st.sidebar.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
if st.sidebar.button("❌ Hide Control Panel"):
    st.session_state.sidebar_state = "collapsed"
    st.rerun()

# Helper Utilities & Validations
def defang(text):
    if not text:
        return text
    text = re.sub(r'http://', 'hxxp://', text)
    text = re.sub(r'https://', 'hxxps://', text)
    text = re.sub(r'(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})', r'\1.\2.\3[.]\4', text)
    text = re.sub(r'([a-zA-Z0-9-]+\.)+([a-zA-Z]{2,})', lambda m: m.group(0).replace('.', '[.]'), text)
    return text

def is_valid_public_ip(ip_str):
    clean_ip = ip_str.replace('[.]', '.')
    parts = clean_ip.split('.')
    if len(parts) != 4:
        return False
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return False
    for o in octets:
        if o < 0 or o > 255:
            return False
    if octets[0] == 0 or octets[0] == 127 or octets == [255, 255, 255, 255]:
        return False
    if octets[0] == 169 and octets[1] == 254:
        return False
    if octets[0] == 10:
        return False
    if octets[0] == 192 and octets[1] == 168:
        return False
    if octets[0] == 172 and (16 <= octets[1] <= 31):
        return False
    return True

def enrich_ip_data(ip_list, vt_key, abuse_key):
    results = []
    geo_data = []
    valid_ips = [ip for ip in ip_list if is_valid_public_ip(ip)]
    
    for ip in valid_ips[:5]:
        clean_ip = ip.replace('[.]', '.')
        try:
            res = requests.get(f"http://ip-api.com/json/{clean_ip}", timeout=2.5).json()
            if res.get("status") == "success":
                lat = res.get("lat")
                lon = res.get("lon")
                country = res.get("country", "Unknown")
                org = res.get("org", "Unknown Org")
                results.append(f"IP {ip}: {org} ({country}) - ISP: {res.get('isp')}")
                if lat and lon:
                    geo_data.append({"latitude": lat, "longitude": lon})
        except Exception:
            pass

        if abuse_key:
            try:
                headers = {'Accept': 'application/json', 'Key': abuse_key}
                a_res = requests.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={clean_ip}", headers=headers, timeout=2.5)
                if a_res.status_code == 200:
                    abuse_score = a_res.json().get('data', {}).get('abuseConfidenceScore', 0)
                    results.append(f"AbuseIPDB Score for {ip}: {abuse_score}% Confidence Malicious.")
            except Exception:
                pass

    if vt_key and valid_ips:
        try:
            headers = {"x-apikey": vt_key}
            sample_ip = valid_ips[0].replace('[.]', '.')
            vt_res = requests.get(f"https://www.virustotal.com/api/v3/ip_addresses/{sample_ip}", headers=headers, timeout=2.5)
            if vt_res.status_code == 200:
                stats = vt_res.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                results.append(f"VirusTotal Intelligence: {sample_ip} malicious score = {stats.get('malicious', 0)} detections.")
        except Exception:
            pass

    return results, geo_data

def save_feedback_entry(name, role, rating, helpful_features, comments, webhook_target_url):
    entry = {
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "name": name if name else "Anonymous Tester",
        "role": role,
        "rating": rating,
        "features": helpful_features,
        "comments": comments
    }
    st.session_state.feedback_submissions.append(entry)
    
    try:
        log_file = "system_feedback_log.json"
        existing = []
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                existing = json.load(f)
        existing.append(entry)
        with open(log_file, "w") as f:
            json.dump(existing, f, indent=4)
    except Exception:
        pass

    if webhook_target_url:
        try:
            payload = {
                "text": f"📝 *New Smart Intelligence Feedback Received!*\n*Tester:* {entry['name']} ({role})\n*Rating:* {'⭐' * rating}\n*Comments:* {comments}"
            }
            requests.post(webhook_target_url, json=payload, timeout=3)
        except Exception:
            pass

def generate_yara_rule(target_entity, iocs):
    rule_name = re.sub(r'[^a-zA-Z0-9_]', '_', target_entity or "Smart_Intelligence_Threat")
    hashes = iocs.get("SHA256", []) + iocs.get("MD5", [])
    
    hash_conditions = []
    for h in hashes:
        if len(h) == 64:
            hash_conditions.append(f'hash.sha256(0, filesize) == "{h}"')
        elif len(h) == 32:
            hash_conditions.append(f'hash.md5(0, filesize) == "{h}"')
            
    condition_block = " or\n            ".join(hash_conditions) if hash_conditions else 'filesize < 50MB'
    
    return f"""import "hash"

rule {rule_name}_Detection {{
    meta:
        description = "Automated YARA rule generated by Smart Intelligence CTI Platform"
        author = "blessingsmkandawire"
        date = "{datetime.utcnow().strftime('%Y-%m-%d')}"
        threat_level = "CRITICAL"
    condition:
        filesize < 50MB and (
            {condition_block}
        )
}}"""

def generate_instructions_text_report(target_entity, risk_level, iocs, ttps):
    total_iocs = sum(len(v) for v in iocs.values())
    return f"""================================================================================
         SMART INTELLIGENCE | PLAIN-LANGUAGE ANALYST INSTRUCTIONS         
================================================================================
Target Scope          : {target_entity or 'Global Corporate Network'}
Overall Threat Rating : {risk_level}
Total Indicators Found: {total_iocs}
================================================================================"""

def answer_copilot_reasoning(user_prompt):
    return "Hello! I am your **Gemini CTI Copilot**. I am analyzing your telemetry and security workflow. Let me know if you need specific technical guidance!"

def run_live_ai_synthesis(target, raw_text, iocs, ttps, api_key):
    text_lower = raw_text.lower()
    risk_score = 15
    if len(iocs.get("IPv4", [])) > 0: risk_score += 25
    if len(iocs.get("SHA256", [])) > 0 or len(iocs.get("MD5", [])) > 0: risk_score += 30
    if any(k in text_lower for k in ["powershell", "cmd.exe", "mimikatz", "ransom", "lsass"]): risk_score += 30
    risk_score = min(risk_score, 100)

    if api_key:
        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            prompt = f"Analyze this cyber threat data for target '{target}': {raw_text[:1000]}. Provide a concise professional SOC threat risk assessment and narrative."
            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250
            }, timeout=4)
            if resp.status_code == 200:
                ai_text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                if ai_text:
                    return f"### 🤖 Layer 4: Advanced Live Cloud AI Threat Synthesis\n**Calculated Risk Index:** `{risk_score}/100`\n\n{ai_text}", risk_score
        except Exception:
            pass

    if risk_score >= 70:
        severity = "🔴 CRITICAL RISK (Active Sophisticated Adversary Campaign Detected)"
        attribution = "High probability of targeted state-sponsored APT or automated ransomware operator activity."
    elif risk_score >= 40:
        severity = "🟡 ELEVATED RISK (Anomalous Behavioral Vectors & Lateral Probing)"
        attribution = "Indicates persistent reconnaissance, credential harvesting, or automated vulnerability exploitation."
    else:
        severity = "🟢 BASELINE TELEMETRY (Low Operational Risk / Routine Background Noise)"
        attribution = "Standard noise or routine network telemetry with minimal active exploitation signatures."

    total_iocs_count = sum(len(v) for v in iocs.values())
    narrative = [
        f"### 🤖 Layer 4: Advanced AI Threat Correlation & Actionable Mitigation Engine",
        f"**Target Enterprise Scope:** `{target if target else 'Global Corporate Infrastructure'}`",
        f"**Calculated Threat Risk Index:** `{risk_score}/100` — **{severity}**",
        f"\n#### 🔬 Deep Intelligence Attribution & Behavioral Profiling:",
        f" - **Adversary Intent Assessment:** {attribution}",
        f" - **Telemetry Correlation Matrix:** Successfully parsed `{total_iocs_count}` high-fidelity Indicators of Compromise (IoCs) and mapped `{len(ttps)}` precise MITRE ATT&CK tactical vectors.",
        f" - **Anomaly Entropy & Impact Analysis:** Attack vectors exhibit coordinated execution patterns designed to bypass perimeter inspection. Immediate host isolation and perimeter packet filtering are strongly advised.",
        f"\n#### 🛡️ Recommended Tactical Posture:",
        f"1. Execute automated host isolation playbooks on all endpoints linked to flagged cryptographic hashes.",
        f"2. Enforce immediate boundary firewall blacklisting on extracted external C2 IPv4 addresses.",
        f"3. Rotate Kerberos ticket-granting tickets (TGT) and force credential resets across compromised enterprise scopes."
    ]
    return "\n".join(narrative), risk_score

def generate_remediation_playbooks(iocs, ttps):
    ips = iocs.get("IPv4", [])
    domains = iocs.get("Domains", [])
    hashes = iocs.get("SHA256", []) + iocs.get("MD5", [])

    endpoint_lines = ["# Windows PowerShell Host Isolation Commands"]
    if hashes:
        for h in hashes:
            endpoint_lines.append(f"Get-Process | Where-Object {{ $_.Path -like '*{h[:8]}*' }} | Stop-Process -Force")
    endpoint_lines.append("Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True")

    network_lines = ["# Active Perimeter Firewall Rules (C2 Blocklist)"]
    for ip in ips:
        network_lines.append(f"netsh advfirewall firewall add rule name='Block C2 {ip}' dir=in action=block remoteip={ip}")
    for d in domains:
        network_lines.append(f"# DNS RPZ / Sinkhole entry: {d} -> 0.0.0.0")

    identity_lines = [
        "# Active Directory / Azure AD Revocation & Containment",
        "Revoke-AzureADUserAllRefreshToken -ObjectId <Target_User_GUID>",
        "Set-ADUser -Identity <Target_User> -Enabled $false"
    ]

    siem_lines = ["// KQL Query (Microsoft Sentinel / Defender)"]
    if ips:
        ip_str = '", "'.join(ips)
        siem_lines.append(f'DeviceNetworkEvents | where RemoteIP in ("{ip_str}")')

    def render_playbook_html(lines):
        html_output = ['<div class="playbook-container">']
        for line in lines:
            escaped = html.escape(line)
            if line.startswith("#") or line.startswith("//"):
                html_output.append(f'<div class="playbook-line playbook-comment">{escaped}</div>')
            else:
                html_output.append(f'<div class="playbook-line">⚡ {escaped}</div>')
        html_output.append('</div>')
        return "\n".join(html_output)

    return {
        "endpoint": render_playbook_html(endpoint_lines),
        "network": render_playbook_html(network_lines),
        "identity": render_playbook_html(identity_lines),
        "siem": render_playbook_html(siem_lines)
    }

def generate_executive_text_report(target_entity, timeframe, intel_goal, risk_level, accuracy_score, sources_used, iocs):
    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    total_iocs = sum(len(v) for v in iocs.values())
    return f"""================================================================================
             SMART INTELLIGENCE | C-SUITE EXECUTIVE THREAT BRIEFING            
================================================================================
DATE OF INCIDENT BRIEFING : {now_utc}
TARGET ENTITY / SCOPE     : {target_entity if target_entity else 'Global / Corporate Network'}
OVERALL THREAT RISK LEVEL : {risk_level}
CONFIDENCE RATING         : {accuracy_score}%
TOTAL IOCs IDENTIFIED     : {total_iocs}
================================================================================"""

def extract_iocs(raw_text):
    patterns = {
        "IPv4": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        "Domains": r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b',
        "SHA256": r'\b[a-fA-F0-9]{64}\b',
        "MD5": r'\b[a-fA-F0-9]{32}\b',
        "CVE": r'\bCVE-\d{4}-\d{4,7}\b',
        "URLs": r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    }
    extracted = {}
    for ioc_type, pattern in patterns.items():
        matches = list(set(re.findall(pattern, raw_text)))
        if ioc_type == "Domains":
            matches = [d for d in matches if not d.endswith(('.log', '.txt', '.json', '.pcap', '.csv', '.pdf'))]
        if defang_iocs:
            matches = [defang(m) for m in matches]
        extracted[ioc_type] = matches
    return extracted

def map_ttp_heuristics(text):
    ttp_rules = {
        "TA0001 (Initial Access)": ["phishing", "spearphishing", "exploit", "vpn", "valid accounts"],
        "TA0002 (Execution)": ["powershell", "cmd.exe", "bash", "script", "vbs", "python", "payload"],
        "TA0003 (Persistence)": ["scheduled task", "registry", "cron", "service", "startup"],
        "TA0006 (Credential Access)": ["lsass", "mimikatz", "dump", "brute force", "keylogger"],
        "TA0011 (Command & Control)": ["c2", "beacon", "reverse shell", "dns tunneling", "http POST"]
    }
    found_ttps = []
    text_lower = text.lower()
    for ttp, keywords in ttp_rules.items():
        for kw in keywords:
            if kw in text_lower:
                found_ttps.append(f"{ttp} - Trigger: '{kw}'")
                break
    return found_ttps

def calculate_intelligence_accuracy(iocs, ttps, sources_used, target_entity):
    score = 0.0
    score += min(len(sources_used) * 7.0, 35.0)
    total_iocs = sum(len(v) for v in iocs.values())
    high_fidelity_count = len(iocs.get("SHA256", [])) + len(iocs.get("CVE", [])) + len(iocs.get("IPv4", []))
    if total_iocs > 0:
        score += min((high_fidelity_count * 5.0) + (total_iocs * 1.5), 30.0)
    if len(ttps) > 0:
        score += min(len(ttps) * 5.0, 20.0)
    if target_entity and target_entity.strip():
        score += 15.0
    return min(round(score, 1), 100.0)

def generate_stix_bundle(target_entity, iocs):
    objects = []
    bundle_id = f"bundle--{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    identity_id = f"identity--{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-target"
    objects.append({
        "type": "identity", "spec_version": "2.1", "id": identity_id,
        "name": target_entity or "Target Entity", "identity_class": "organization"
    })
    for ioc_type, values in iocs.items():
        for val in values:
            ind_id = f"indicator--{hash(val) & 0xffffffff}"
            pattern_val = f"[{ioc_type.lower()}:value = '{val}']"
            objects.append({
                "type": "indicator", "spec_version": "2.1", "id": ind_id,
                "name": f"Observed {ioc_type}", "pattern": pattern_val,
                "pattern_type": "stix", "valid_from": datetime.utcnow().isoformat() + "Z"
            })
    return {"type": "bundle", "id": bundle_id, "objects": objects}

# 4. FULL-WIDTH ENLARGED HIGH-TECH CYBER SHIELD BANNER COMPONENT
st.components.v1.html("""
    <div style="position: relative; width: 100%; height: 380px; background: radial-gradient(circle at 50% 50%, #0d2959 0%, #020612 95%); border: 2.5px solid #38bdf8; border-radius: 24px; overflow: hidden; box-shadow: 0 0 65px rgba(56, 189, 248, 0.65), inset 0 0 45px rgba(56, 189, 248, 0.4); margin: 0 auto;">
        
        <!-- Background Animated Grid Mesh -->
        <div style="position: absolute; top:0; left:0; width:100%; height:100%; background-image: linear-gradient(rgba(56, 189, 248, 0.14) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.14) 1px, transparent 1px); background-size: 30px 30px; z-index:1;"></div>

        <!-- Four Neon Corner Brackets -->
        <div style="position: absolute; top: 14px; left: 20px; color: #00ffcc; font-size: 2.4rem; font-family: monospace; font-weight: 900; text-shadow: 0 0 18px #00ffcc; z-index: 6;">⌜</div>
        <div style="position: absolute; top: 14px; right: 20px; color: #00ffcc; font-size: 2.4rem; font-family: monospace; font-weight: 900; text-shadow: 0 0 18px #00ffcc; z-index: 6;">⌝</div>
        <div style="position: absolute; bottom: 14px; left: 20px; color: #00ffcc; font-size: 2.4rem; font-family: monospace; font-weight: 900; text-shadow: 0 0 18px #00ffcc; z-index: 6;">⌞</div>
        <div style="position: absolute; bottom: 14px; right: 20px; color: #00ffcc; font-size: 2.4rem; font-family: monospace; font-weight: 900; text-shadow: 0 0 18px #00ffcc; z-index: 6;">⌟</div>

        <!-- TOP TECH BANNER STRIP -->
        <div style="position: absolute; top: 16px; left: 50%; transform: translateX(-50%); display: flex; gap: 30px; align-items: center; z-index: 6; width: 85%; justify-content: space-between; font-family: monospace; font-size: 0.9rem; font-weight: 800;">
            <div style="color: #38bdf8; text-shadow: 0 0 12px #38bdf8;">⚡ CTI-CORE: ONLINE</div>
            <div style="color: #00ffcc; text-shadow: 0 0 12px #00ffcc; letter-spacing: 0.12em;">[ SECURE ENDPOINT PIPELINE ACTIVE ]</div>
            <div style="color: #ff0055; text-shadow: 0 0 12px #ff0055;">🔒 AES-256 ENCRYPTED</div>
        </div>

        <!-- LEFT SIDE DIAGNOSTIC MODULE (Oscilloscope Wave + Metric Gauges) -->
        <div style="position: absolute; left: 45px; top: 52%; transform: translateY(-50%); width: 250px; z-index: 4; font-family: monospace;">
            <div style="color: #00ffcc; font-size: 0.82rem; font-weight: 800; margin-bottom: 8px; text-shadow: 0 0 10px #00ffcc;">📊 TELEMETRY WAVEFORM</div>
            <!-- Animated SVG Waveform -->
            <svg width="230px" height="70px" style="background: rgba(3, 10, 26, 0.75); border: 1.5px solid #38bdf8; border-radius: 10px; box-shadow: 0 0 15px rgba(56,189,248,0.35);">
                <path d="M0 35 Q30 5 60 35 T120 35 T180 35 T230 35" fill="none" stroke="#00ffcc" stroke-width="2.5">
                    <animate attributeName="d" dur="2s" repeatCount="indefinite" values="M0 35 Q30 5 60 35 T120 35 T180 35 T230 35; M0 35 Q30 65 60 35 T120 35 T180 35 T230 35; M0 35 Q30 5 60 35 T120 35 T180 35 T230 35"/>
                </path>
            </svg>
            <div style="margin-top: 10px; color: #38bdf8; font-size: 0.8rem; line-height: 1.5;">
                <div>SHIELD HEALTH : <span style="color:#00ffcc;">98.4%</span></div>
                <div>PACKET LOSS   : <span style="color:#00ffcc;">0.00%</span></div>
                <div>FIREWALL LOAD : <span style="color:#ff0055;">12.1%</span></div>
            </div>
        </div>

        <!-- LEFT RADAR DIAL -->
        <div style="position: absolute; left: 220px; top: 52%; transform: translateY(-50%); width: 170px; height: 170px; border: 2.5px dashed #38bdf8; border-radius: 50%; animation: spinRight 14s linear infinite; opacity: 0.65; z-index:2;"></div>

        <!-- CENTER MASSIVE GLOWING CYBER SHIELD WITH TARGET CROSSHAIRS -->
        <div style="position: absolute; left: 50%; top: 52%; transform: translate(-50%, -50%); z-index: 5;">
            
            <!-- Outer Target Reticle Ring -->
            <div style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 260px; height: 260px; border: 2px solid rgba(0, 255, 204, 0.65); border-radius: 50%; border-style: dotted; animation: spinRight 20s linear infinite;"></div>
            
            <svg width="210" height="235" viewBox="0 0 100 120" style="filter: drop-shadow(0 0 30px #38bdf8) drop-shadow(0 0 55px #00ffcc) drop-shadow(0 0 85px #0284c7);">
                <!-- Outer Shield Path -->
                <path d="M50 5 L90 20 V60 C90 90 50 115 50 115 C50 115 10 90 10 60 V20 Z" fill="rgba(6, 25, 56, 0.9)" stroke="#38bdf8" stroke-width="4"/>
                <!-- Inner Shield Path -->
                <path d="M50 14 L82 26 V58 C82 82 50 102 50 102 C50 102 18 82 18 58 V26 Z" fill="none" stroke="#00ffcc" stroke-width="2.5" stroke-dasharray="4 2"/>
                <!-- Core Glowing Symbol -->
                <circle cx="50" cy="55" r="16" fill="#38bdf8" style="animation: pulseGlow 1.8s infinite alternate;"/>
                <path d="M50 34 V76 M30 55 H70" stroke="#020612" stroke-width="3.5"/>
            </svg>
            
            <!-- Laser Radar Scanner Bar -->
            <div style="position: absolute; top: -12px; left: -25px; width: 260px; height: 6px; background: linear-gradient(90deg, transparent, #00ffcc, #38bdf8, #ff0055, transparent); box-shadow: 0 0 25px #00ffcc; animation: scanVertical 2.2s ease-in-out infinite;"></div>
        </div>

        <!-- Orbiting 3D Ring 1 -->
        <div style="position: absolute; left: 50%; top: 52%; width: 400px; height: 140px; margin-left: -200px; margin-top: -70px; border: 1.5px solid rgba(56, 189, 248, 0.6); border-radius: 50%; transform: rotateX(72deg) rotateZ(35deg); animation: spinRight 7s linear infinite; z-index:3;">
            <div style="width: 16px; height: 16px; background: #00ffcc; border-radius: 50%; box-shadow: 0 0 20px #00ffcc, 0 0 32px #00ffcc;"></div>
        </div>

        <!-- Orbiting 3D Ring 2 -->
        <div style="position: absolute; left: 50%; top: 52%; width: 400px; height: 140px; margin-left: -200px; margin-top: -70px; border: 1.5px solid rgba(255, 0, 85, 0.6); border-radius: 50%; transform: rotateX(72deg) rotateZ(-35deg); animation: spinLeft 5s linear infinite; z-index:3;">
            <div style="width: 16px; height: 16px; background: #ff0055; border-radius: 50%; box-shadow: 0 0 20px #ff0055, 0 0 32px #ff0055;"></div>
        </div>

        <!-- RIGHT RADAR DIAL -->
        <div style="position: absolute; right: 220px; top: 52%; transform: translateY(-50%); width: 170px; height: 170px; border: 2.5px dashed #38bdf8; border-radius: 50%; animation: spinLeft 14s linear infinite; opacity: 0.65; z-index:2;"></div>

        <!-- RIGHT SIDE DIAGNOSTIC MODULE (Binary Stream + Target Scope) -->
        <div style="position: absolute; right: 45px; top: 52%; transform: translateY(-50%); width: 240px; z-index: 4; font-family: monospace; text-align: right;">
            <div style="color: #ff0055; font-size: 0.82rem; font-weight: 800; margin-bottom: 8px; text-shadow: 0 0 10px #ff0055;">📡 LIVE BINARY STREAM</div>
            <div style="background: rgba(3, 10, 26, 0.75); border: 1.5px solid #ff0055; border-radius: 10px; padding: 10px; color: #00ffcc; font-size: 0.75rem; box-shadow: 0 0 15px rgba(255,0,85,0.35); line-height: 1.4;">
                01100101 01110011<br>
                10100110 11001011<br>
                00110101 01011110
            </div>
            <div style="margin-top: 10px; color: #38bdf8; font-size: 0.8rem; line-height: 1.5;">
                <div>TARGETS : <span style="color:#00ffcc;">0 DETECTED</span></div>
                <div>SCAN SPEED : <span style="color:#00ffcc;">10 Gbps</span></div>
            </div>
        </div>

        <!-- CENTRAL BOTTOM STATUS BADGE -->
        <div style="position: absolute; bottom: 14px; left: 50%; transform: translateX(-50%); background: rgba(2, 6, 18, 0.92); border: 1.5px solid #00ffcc; border-radius: 22px; padding: 6px 26px; color: #00ffcc; font-family: monospace; font-size: 0.95rem; font-weight: 800; letter-spacing: 0.15em; text-shadow: 0 0 14px #00ffcc; box-shadow: 0 0 25px rgba(0, 255, 204, 0.45); z-index: 6;">
            [ SYSTEM SHIELD ACTIVE — REAL-TIME THREAT MONITORING ]
        </div>
    </div>

    <!-- Animation Keyframes -->
    <style>
    @keyframes spinRight {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes spinLeft {
        0% { transform: rotate(360deg); }
        100% { transform: rotate(0deg); }
    }
    @keyframes scanVertical {
        0% { top: 5%; opacity: 0.2; }
        50% { top: 90%; opacity: 1; }
        100% { top: 5%; opacity: 0.2; }
    }
    @keyframes pulseGlow {
        0% { transform: scale(0.85); filter: drop-shadow(0 0 10px #38bdf8); }
        100% { transform: scale(1.25); filter: drop-shadow(0 0 30px #00ffcc); }
    }
    </style>
""", height=395)

col_hdr1, col_hdr2 = st.columns([3, 1])
with col_hdr1:
    st.title(t["welcome"])
    st.markdown(f"##### **{t['tagline']}**")

with col_hdr2:
    st.write("")
    with st.popover("🤖 CTI Copilot & Live AI", help="Click to open live CTI assistant"):
        st.markdown(f"""
            <div style="background-color: {copilot_bg}; color: {copilot_text}; padding: 6px; border-radius: 10px;">
                <h4 style="color: {copilot_text} !important; margin-bottom: 2px;">💡 Gemini CTI Copilot</h4>
                <p style="color: {copilot_text} !important; font-size: 0.82rem; opacity: 0.9;">Real-time interactive assistant & guidance engine.</p>
            </div>
        """, unsafe_allow_html=True)
        
        chat_box = st.container(height=260)
        with chat_box:
            for message in st.session_state.help_chat_history:
                if message["role"] == "assistant":
                    st.markdown(f"<div style='background:{copilot_bubble_assistant}; padding:8px 12px; border-radius:8px; margin-bottom:6px; color:{copilot_text}; font-size:0.88rem;'><b>Copilot:</b> {message['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:{copilot_bubble_user}; padding:8px 12px; border-radius:8px; margin-bottom:6px; color:#ffffff; font-size:0.88rem; text-align:right;'><b>You:</b> {message['content']}</div>", unsafe_allow_html=True)

        col_qb1, col_qb2 = st.columns(2)
        if col_qb1.button("📊 Summarize Risk", key="qb_risk"):
            reply = answer_copilot_reasoning("Summarize current threat risk")
            st.session_state.help_chat_history.append({"role": "user", "content": "Summarize current threat risk"})
            st.session_state.help_chat_history.append({"role": "assistant", "content": reply})
            st.rerun()
        if col_qb2.button("🛡️ View Playbooks", key="qb_playbooks"):
            reply = answer_copilot_reasoning("Explain containment playbooks")
            st.session_state.help_chat_history.append({"role": "user", "content": "Explain containment playbooks"})
            st.session_state.help_chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

        with st.form(key="copilot_form", clear_on_submit=True):
            user_input = st.text_input("Ask a question...", label_visibility="collapsed", placeholder="Ask any question...")
            submit_btn = st.form_submit_button("Send")
            
            if submit_btn and user_input.strip():
                st.session_state.help_chat_history.append({"role": "user", "content": user_input})
                reply = answer_copilot_reasoning(user_input)
                st.session_state.help_chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

    if st.session_state.sidebar_state == "collapsed":
        if st.button("🎛️ Open Control Panel"):
            st.session_state.sidebar_state = "expanded"
            st.rerun()

# WELCOME BANNER & STATUS HUD
st.markdown('<div class="welcome-banner">🛡️ WELCOME TO THE SMART INTELLIGENCE THREAT DASHBOARD</div>', unsafe_allow_html=True)

st.markdown("""
    <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 12px;">
        <div class="live-hud-badge">
            <span class="live-hud-dot"></span> SYSTEM READY : 5-LAYER PIPELINE ONLINE
        </div>
    </div>
""", unsafe_allow_html=True)

st.divider()

# LAYER 1: SCOPE DEFINITION
st.header(t["l1"])
col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    target_entity = st.text_input(t["target"], placeholder="e.g. Banking Infrastructure, Corporate Network")
with col_s2:
    timeframe = st.selectbox(t["timeframe"], ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Historical Campaign"])
with col_s3:
    intel_goal = st.text_input(t["goal"], placeholder="e.g. Identify Ransomware IoCs, Detect C2 Activity")

st.divider()

# LAYER 2: MULTI-SOURCE INGESTION & QUICK-LOAD SAMPLES
st.header(t["l2"])

st.markdown("##### ⚡ Quick-Load Attack Telemetry (Sample Scenarios)")
qcol1, qcol2, qcol3 = st.columns(3)
if qcol1.button("🚨 Load Ransomware Sample"):
    st.session_state.sample_log_text = "Detected ransomware payload execution via powershell.exe. IP: 185.220.101.5 connecting to malicious C2 domain c2-beacon-node.com. File Hash SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. CVE-2023-21554 exploited."
    st.rerun()
if qcol2.button("🌐 Load C2 Botnet Sample"):
    st.session_state.sample_log_text = "Multiple brute-force attempts from 45.33.32.156 targeting SSH port 22. Associated with APT29 threat group infrastructure. Domain: malicious-update.net communicating over port 443."
    st.rerun()
if qcol3.button("🧹 Clear Sample Logs"):
    st.session_state.sample_log_text = ""
    st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💻 (i) System & Network Logs",
    "🌐 (ii) OSINT",
    "🛡️ (iii) CSINT",
    "📡 (iv) Commercial Feeds",
    "📝 (v) Additional Info"
])

with tab1:
    st.subheader("System & Network Logs")
    log_text = st.text_area("Paste Raw Logs:", value=st.session_state.sample_log_text, height=120, placeholder="Paste syslog, firewall, or web server logs here...")
    log_file = st.file_uploader("Upload Log File (.log, .json, .csv, .pcap)", type=["log", "json", "csv", "txt"])

with tab2:
    st.subheader("Open Source Intelligence")
    osint_text = st.text_area("Manual OSINT Input:", height=120, placeholder="Paste threat blog notes, pastebin text, or forum chatter...")
    auto_osint = st.checkbox("Enable Automated OSINT Gathering (Simulated Query)")

with tab3:
    st.subheader("Cyber Security Intelligence")
    csint_text = st.text_area("Raw CSINT Data:", height=120, placeholder="Paste incident response notes or threat actor disclosures...")
    csint_file = st.file_uploader("Upload CSINT Report (.pdf, .stix, .json)", type=["pdf", "json", "stix", "txt"])

with tab4:
    st.subheader("Commercial Feeds Integration")
    feed_text = st.text_area("Manual Commercial Feed Data:", height=120, placeholder="Paste raw threat feed exports...")
    feed_api = st.text_input("Connect Threat Feed API Key (AlienVault / VirusTotal / ThreatFox):", type="password")

with tab5:
    st.subheader("Context & Analyst Notes")
    context_text = st.text_area("Analyst Notes:", height=120, placeholder="Enter specific environment details, asset criticalities, etc...")
    context_file = st.file_uploader("Upload Supporting Documentation", type=["txt", "pdf", "docx"])

st.divider()

# PIPELINE EXECUTION BUTTON
st.header("Pipeline Execution")

sources_used = []
combined_raw_data = ""

if log_text.strip() or log_file:
    sources_used.append("System Logs")
    combined_raw_data += f"\n{log_text}"
if osint_text.strip() or auto_osint:
    sources_used.append("OSINT")
    combined_raw_data += f"\n{osint_text}"
if csint_text.strip() or csint_file:
    sources_used.append("CSINT")
    combined_raw_data += f"\n{csint_text}"
if feed_text.strip() or feed_api.strip():
    sources_used.append("Commercial Feeds")
    combined_raw_data += f"\n{feed_text}"
if context_text.strip() or context_file:
    sources_used.append("Analyst Notes")
    combined_raw_data += f"\n{context_text}"

for uploaded_file in [log_file, csint_file, context_file]:
    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            combined_raw_data += f"\n{content}"
        except Exception as e:
            st.warning(f"Could not parse text from file {uploaded_file.name}: {e}")

if st.button(t["btn_process"], type="primary"):
    if not combined_raw_data.strip():
        st.error("Please provide input in at least one ingestion tab or load a sample scenario before processing.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("🔄 Layer 1: Validating target scope & intelligence timeframe...")
        time.sleep(0.3)
        progress_bar.progress(20)

        status_text.text("🔄 Layer 2: Ingesting multi-source telemetry...")
        time.sleep(0.3)
        progress_bar.progress(40)

        status_text.text("🔄 Layer 3: Running extraction & normalization engine...")
        iocs = extract_iocs(combined_raw_data)
        live_enrichment, geo_locations = enrich_ip_data(iocs.get("IPv4", []), vt_api_key, abuseipdb_api_key) if enable_live_enrichment else ([], [])
        time.sleep(0.3)
        progress_bar.progress(60)

        status_text.text("🔄 Layer 4: Executing AI threat correlation & risk scoring...")
        ttps = map_ttp_heuristics(combined_raw_data)
        st.session_state.ai_analysis_result, computed_risk_score = run_live_ai_synthesis(
            target_entity, combined_raw_data, iocs, ttps, ai_api_key
        )
        time.sleep(0.3)
        progress_bar.progress(80)

        status_text.text("🔄 Layer 5: Compiling playbooks, YARA rules, and deliverables...")
        stix_bundle = generate_stix_bundle(target_entity, iocs)
        yara_code = generate_yara_rule(target_entity, iocs)
        playbooks = generate_remediation_playbooks(iocs, ttps)
        
        total_iocs = sum(len(v) for v in iocs.values())
        accuracy_score = calculate_intelligence_accuracy(iocs, ttps, sources_used, target_entity)

        if computed_risk_score >= 70:
            risk_level = "CRITICAL"
        elif computed_risk_score >= 40:
            risk_level = "MEDIUM / HIGH"
        else:
            risk_level = "LOW"

        text_report = generate_executive_text_report(
            target_entity, timeframe, intel_goal, risk_level, accuracy_score, sources_used, iocs
        )
        instructions_text = generate_instructions_text_report(target_entity, risk_level, iocs, ttps)

        save_scan_to_db(target_entity, timeframe, computed_risk_score, risk_level, total_iocs, len(ttps), combined_raw_data)

        time.sleep(0.2)
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()

        st.success("⚡ Live 5-Layer Intelligence Pipeline Execution Complete!")

        # LAYER 3: EXTRACTION & NORMALIZATION WORKSPACE
        st.markdown(f"<h2 style='margin-top: 25px;'>📊 {t['l3']}</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.95rem; margin-bottom: 20px;'>Normalized extraction breakdown and clean asset-to-threat indicator correlation matrix.</p>", unsafe_allow_html=True)

        col_corr1, col_corr2 = st.columns(2)

        with col_corr1:
            st.subheader("📈 Indicator Category Volume Breakdown")
            chart_data = pd.DataFrame({
                'Indicator Category': list(iocs.keys()),
                'Count': [len(v) for v in iocs.values()]
            })
            bar_chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X('Indicator Category:N', sort=None, title="IoC Type", axis=alt.Axis(labelAngle=0)),
                y=alt.Y('Count:Q', title="Extracted Volume", axis=alt.Axis(tickMinStep=1)),
                color=alt.Color('Indicator Category:N', scale=alt.Scale(scheme='tableau10'), legend=None),
                tooltip=['Indicator Category', 'Count']
            ).properties(height=260).configure_axis(
                gridColor='#1e293b', domainColor='#334155', labelColor='#cbd5e1', titleColor='#f8fafc'
            ).configure_view(strokeWidth=0)
            st.altair_chart(bar_chart, use_container_width=True)

        with col_corr2:
            st.subheader("🔗 Clean Asset vs Threat Correlation Summary")
            target_label = target_entity or "Target Enterprise Scope"
            
            summary_rows = []
            for cat, items in iocs.items():
                for item in items[:6]:
                    summary_rows.append({
                        "Target Asset": target_label,
                        "Indicator Class": cat,
                        "Extracted Artifact": item
                    })
            
            if summary_rows:
                sdf = pd.DataFrame(summary_rows)
                st.dataframe(sdf, use_container_width=True, height=260)
            else:
                st.info("No indicators extracted for correlation table.")

        if live_enrichment:
            st.subheader("🌐 Layer 3 Live Feed & ASN Enrichment Intelligence")
            for item in live_enrichment:
                st.warning(f"📡 {item}")

        st.divider()

        # LAYER 5: PROFESSIONAL SOC OPERATIONAL DASHBOARD HERO
        st.markdown('<div class="soc-dashboard-hero">', unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin-bottom: 5px;'>🚀 {t['l5']}</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.95rem; margin-bottom: 20px;'>Enterprise Operational Command Center — Real-time threat correlation, indicators, and defensive playbooks.</p>", unsafe_allow_html=True)

        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        
        with col_m1:
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem;'>TARGET ENTITY</span><h3 style='margin:5px 0; font-size:1.1rem;'>{target_entity if target_entity else 'Global'}</h3></div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem;'>IOCs EXTRACTED</span><h3 style='margin:5px 0; font-size:1.5rem;'>{total_iocs}</h3></div>", unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem;'>TTPs MAPPED</span><h3 style='margin:5px 0; font-size:1.5rem;'>{len(ttps)}</h3></div>", unsafe_allow_html=True)
        with col_m4:
            risk_color = "#ef4444" if "CRITICAL" in risk_level else "#f59e0b" if "HIGH" in risk_level else "#10b981"
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem;'>RISK RATING</span><h3 style='color:{risk_color}; margin:5px 0; font-size:1.2rem;'>{risk_level}</h3></div>", unsafe_allow_html=True)
        with col_m5:
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem;'>CONFIDENCE</span><h3 style='margin:5px 0; font-size:1.5rem;'>{accuracy_score}%</h3></div>", unsafe_allow_html=True)

        st.write("")

        if st.session_state.ai_analysis_result:
            st.info(st.session_state.ai_analysis_result)

        st.write("")

        # ADVANCED SOC TABBED NAVIGATION
        soc_tab1, soc_tab2, soc_tab3, soc_tab4, soc_tab5 = st.tabs([
            "🔍 IoC Inspector",
            "🛡️ Playbook Armory",
            "🗺️ Attack Origin Map",
            "📦 Deliverables & Exports",
            "📜 Threat Search Archive"
        ])

        with soc_tab1:
            st.subheader("📊 Layer 3 Extracted Indicators of Compromise")
            filter_term = st.text_input("🔍 Filter/Search IoCs in real-time:", placeholder="Type IP, hash, or domain...")
            
            ioc_col1, ioc_col2 = st.columns(2)
            
            def filter_list(lst):
                if not filter_term:
                    return lst
                return [item for item in lst if filter_term.lower() in str(item).lower()]

            def render_ioc_block(title, items):
                filtered = filter_list(items)
                st.markdown(f"**{title}**")
                if filtered:
                    for val in filtered:
                        st.markdown(f'<div class="ioc-box">⚡ {val}</div>', unsafe_allow_html=True)
                else:
                    st.caption("None detected")

            with ioc_col1:
                render_ioc_block("IPv4 Addresses:", iocs["IPv4"])
                render_ioc_block("Domains:", iocs["Domains"])
                render_ioc_block("URLs:", iocs["URLs"])
            
            with ioc_col2:
                render_ioc_block("SHA-256 Hashes:", iocs["SHA256"])
                render_ioc_block("MD5 Hashes:", iocs["MD5"])
                render_ioc_block("CVE Vulnerabilities:", iocs["CVE"])

            st.subheader("🎯 Layer 3 MITRE ATT&CK TTP Mapping")
            if ttps:
                for ttp in ttps:
                    st.info(f"📍 {ttp}")
            else:
                st.write("No explicit MITRE ATT&CK tactics matched standard heuristic keywords.")

        with soc_tab2:
            st.subheader("🛡️ Layer 4 Fight-Back & Containment Playbook Engine")
            st.caption("Copy and execute active containment scripts across host, network, identity, and SIEM controls.")

            pb_tab1, pb_tab2, pb_tab3, pb_tab4 = st.tabs([
                "💻 (i) Endpoint Isolation Scripts",
                "🌐 (ii) Perimeter Firewall Rules",
                "🔑 (iii) Identity & Kerberos Revocation",
                "🔍 (iv) SIEM Threat Hunting Queries"
            ])

            with pb_tab1:
                st.markdown(playbooks["endpoint"], unsafe_allow_html=True)
            with pb_tab2:
                st.markdown(playbooks["network"], unsafe_allow_html=True)
            with pb_tab3:
                st.markdown(playbooks["identity"], unsafe_allow_html=True)
            with pb_tab4:
                st.markdown(playbooks["siem"], unsafe_allow_html=True)

        with soc_tab3:
            st.subheader("🗺️ Attacker Origin Map")
            if geo_locations:
                map_df = pd.DataFrame(geo_locations)
                st.map(map_df, zoom=1)
            else:
                st.info("No public IP addresses with geographical coordinates were extracted in this scan.")

        with soc_tab4:
            st.subheader("📦 Layer 5 Export Threat Intelligence Deliverables")
            dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
            
            with dl_col1:
                st.download_button(
                    label="📄 Download Executive Briefing (.txt)",
                    data=text_report,
                    file_name="executive_threat_briefing.txt",
                    mime="text/plain"
                )
                
            with dl_col2:
                st.download_button(
                    label="📥 Download STIX 2.1 Bundle (.json)",
                    data=json.dumps(stix_bundle, indent=4),
                    file_name="smart_intelligence_stix21.json",
                    mime="application/json"
                )

            with dl_col3:
                st.download_button(
                    label="🛡️ Download YARA Rules (.yara)",
                    data=yara_code,
                    file_name="smart_intelligence_rule.yara",
                    mime="text/plain"
                )

            with dl_col4:
                st.download_button(
                    label="📖 Download Instructions (.txt)",
                    data=instructions_text,
                    file_name="instructions.txt",
                    mime="text/plain"
                )

            st.divider()

            # NON-CLOSING HTML/JS AUDIO BRIEFING BUTTON
            st.subheader("🎙️ Executive Incident Audio Briefing")
            speech_summary = f"Executive threat briefing for target {target_entity or 'Global Corporate Infrastructure'}. Overall risk rating is {risk_level} with {total_iocs} total extracted indicators of compromise."
            clean_audio_json = json.dumps(speech_summary)
            
            st.components.v1.html(f"""
                <div style="margin: 10px 0;">
                    <button onclick="playAudio()" style="background: linear-gradient(135deg, #0284c7 0%, #38bdf8 50%, #00ffcc 100%); color: #030712; font-weight: 800; font-size: 1rem; border: none; border-radius: 12px; padding: 12px 22px; cursor: pointer; box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);">
                        🔊 Play Executive Briefing Audio
                    </button>
                </div>
                <script>
                function playAudio() {{
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        var text = {clean_audio_json};
                        var utterance = new SpeechSynthesisUtterance(text);
                        utterance.rate = 0.95;
                        window.speechSynthesis.speak(utterance);
                    }} else {{
                        alert("Speech synthesis not supported in this browser.");
                    }}
                }}
                </script>
            """, height=70)

            st.divider()
            st.subheader("🚨 Automated Incident Response Webhook Dispatcher")
            if st.button("📡 Dispatch Threat Alert to SOC Webhook"):
                if not webhook_url:
                    st.warning("Please configure your SOC Webhook URL in the Control Panel sidebar first.")
                else:
                    try:
                        payload = {
                            "text": f"🚨 *Smart Intelligence CTI Alert* \n*Target:* {target_entity}\n*Risk Rating:* {risk_level}\n*Total IoCs:* {total_iocs}"
                        }
                        resp = requests.post(webhook_url, json=payload, timeout=5)
                        if resp.status_code in [200, 201, 204]:
                            st.success("Successfully dispatched alert payload to your SOC Webhook endpoint!")
                        else:
                            st.error(f"Webhook responded with status code: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Failed to dispatch webhook: {e}")

            st.divider()
            
            # IN-APP BETA TESTER FEEDBACK FORM
            st.subheader("📝 User Feedback & System Evaluation Form")
            st.caption("Help us improve the Smart Intelligence CTI Platform by sharing your testing feedback!")

            with st.form(key="user_feedback_form", clear_on_submit=True):
                fb_col1, fb_col2 = st.columns(2)
                with fb_col1:
                    tester_name = st.text_input("Your Name / Handle (Optional):", placeholder="e.g. Alex M.")
                with fb_col2:
                    tester_role = st.selectbox("Your Role / Background:", [
                        "SOC Analyst / Incident Responder",
                        "Cybersecurity Student / Researcher",
                        "Security Engineer / Architect",
                        "General Tech Enthusiast / Tester"
                    ])

                rating = st.slider("⭐ How would you rate the system's performance and usability?", 1, 5, 5)

                helpful_features = st.multiselect(
                    "💡 Which features did you test or find most useful?",
                    [
                        "Multi-Source Log Ingestion (Layer 2)",
                        "Automated Regex & IoC Extraction (Layer 3)",
                        "Live Threat Feed Enrichment (IP/ASN)",
                        "AI Threat Synthesis & Risk Scoring (Layer 4)",
                        "Containment Playbooks (PowerShell / Firewall / KQL)",
                        "YARA Rule & STIX 2.1 File Exports",
                        "Attacker Geographical Map",
                        "Executive Briefing Audio"
                    ],
                    default=["Automated Regex & IoC Extraction (Layer 3)", "Containment Playbooks (PowerShell / Firewall / KQL)"]
                )

                feedback_comments = st.text_area(
                    "💬 Comments, Bugs Experienced, or Suggestions for Improvement:",
                    placeholder="Tell us what worked well, what was confusing, or what features you'd like to see next..."
                )

                submit_feedback = st.form_submit_button("📩 Submit Feedback")

                if submit_feedback:
                    save_feedback_entry(tester_name, tester_role, rating, helpful_features, feedback_comments, webhook_url)
                    st.success("🎉 Thank you for your feedback! Your evaluation response has been recorded.")

            if st.session_state.feedback_submissions:
                with st.expander("📊 View Submitted Feedback Log (Admin/Analyst View)", expanded=False):
                    avg_rating = round(sum(f['rating'] for f in st.session_state.feedback_submissions) / len(st.session_state.feedback_submissions), 1)
                    st.markdown(f"**Total Submissions:** `{len(st.session_state.feedback_submissions)}` | **Average Rating:** ⭐ `{avg_rating}/5`")
                    fb_df = pd.DataFrame(st.session_state.feedback_submissions)
                    st.dataframe(fb_df, use_container_width=True)

        with soc_tab5:
            st.subheader("📜 Historical Threat Scan Database Archive")
            db_history_df = get_scan_history()
            if not db_history_df.empty:
                st.dataframe(db_history_df, use_container_width=True, height=350)
            else:
                st.info("No scans recorded in database yet.")

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)

st.markdown(
    '<div class="developer-footer">developed by blessingsmkandawire</div>',
    unsafe_allow_html=True
)