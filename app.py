import streamlit as st
import re
import json
import html
from datetime import datetime
import pandas as pd
import altair as alt
import requests
import time

# 1. SESSION STATE FOR THEME, SIDEBAR, & CHAT
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

if "ai_analysis_result" not in st.session_state:
    st.session_state.ai_analysis_result = None

if "computed_risk_score" not in st.session_state:
    st.session_state.computed_risk_score = 0

if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False

if "help_chat_history" not in st.session_state:
    st.session_state.help_chat_history = [
        {"role": "assistant", "content": "👋 **Hello! I'm your Gemini CTI Copilot.** Ask me anything about your threat pipeline or security workflows!"}
    ]

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Smart Intelligence | Enterprise CTI Suite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# 2. HIGH-VISIBILITY CONTROL PANEL (SIDEBAR)
st.sidebar.markdown("<h2 style='color: #38bdf8; text-align: center; border-bottom: 2px solid #38bdf8; padding-bottom: 8px;'>⚙️ CONTROL PANEL</h2>", unsafe_allow_html=True)

LANGUAGES = {
    "English": {
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
        "goal": "Intelligence Goal",
        "confidence": "Intelligence Confidence",
        "risk": "Threat Risk Rating",
        "iocs_found": "Total IoCs Extracted",
        "ttps_mapped": "TTPs Mapped"
    },
    "Français (French)": {
        "welcome": "Smart Intelligence CTI",
        "tagline": "Plateforme automatisée de renseignement, corrélation et atténuation des cybermenaces",
        "l1": "Couche 1: Définition du Périmètre et de la Cible",
        "l2": "Couche 2: Modules d'Ingestion de Données Multi-Sources",
        "l3": "Couche 3: Moteur d'Extraction et de Normalisation",
        "l4": "Couche 4: Moteur de Corrélation et d'Atténuation IA",
        "l5": "Couche 5: Livrables et Tableau de Bord Opérationnel",
        "btn_process": "⚡ EXÉCUTER LE PIPELINE D'INTELLIGENCE À 5 COUCHES",
        "target": "Entité Cible / Secteur",
        "timeframe": "Période d'Intelligence",
        "goal": "Objectif d'Intelligence",
        "confidence": "Confiance dans l'Intelligence",
        "risk": "Évaluation du Risque de Menace",
        "iocs_found": "Total d'IoCs Extraits",
        "ttps_mapped": "TTPs Cartographiés"
    }
}

selected_lang = st.sidebar.selectbox("🌐 Interface Language", list(LANGUAGES.keys()))
t = LANGUAGES[selected_lang]

def on_theme_change():
    pass

theme_choice = st.sidebar.selectbox(
    "🎨 UI Visual Mode", 
    ["Dark SOC Theme", "Cyberpunk Neon Mode", "Clean Light Mode"],
    on_change=on_theme_change
)

with st.sidebar.expander("🛠️ Advanced Platform & API Settings", expanded=False):
    enable_live_enrichment = st.checkbox("Enable Live Threat Feed Lookups (IP/ASN)", value=True)
    defang_iocs = st.checkbox("Defang IoCs for Safety (e.g. 1.1.1[.]1)")
    st.session_state.voice_mode = st.checkbox("Enable Live Voice Speech-Output", value=st.session_state.voice_mode)
    ai_api_key = st.text_input("Live AI / Gemini API Key (Optional)", type="password", placeholder="Enter AI API key...")
    vt_api_key = st.text_input("VirusTotal API Key (Optional)", type="password", placeholder="Enter VT v3 key...")
    webhook_url = st.text_input("SOC Webhook URL (Slack/Teams)", placeholder="https://webhook.site/...")

st.sidebar.markdown("---")
if st.sidebar.button("❌ Hide Control Panel"):
    st.session_state.sidebar_state = "collapsed"
    st.rerun()

# Dynamic Theme Variables
if theme_choice == "Cyberpunk Neon Mode":
    bg_color_solid = "#030208"
    bg_gradient = "radial-gradient(circle at 50% 10%, #2a0845 0%, #030208 85%)"
    card_bg = "rgba(18, 15, 36, 0.82)"
    text_color = "#00ffcc"
    accent_color = "#ff0055"
    border_color = "#00ffcc"
    glow_shadow = "0 0 20px rgba(0, 255, 204, 0.5), 0 0 40px rgba(255, 0, 85, 0.3)"
    matrix_glow_color = "#00ffcc"
    copilot_bg = "#0d0a1a"
    copilot_text = "#00ffcc"
    copilot_bubble_user = "#ff0055"
    copilot_bubble_assistant = "#1e153b"
elif theme_choice == "Clean Light Mode":
    bg_color_solid = "#f1f5f9"
    bg_gradient = "linear-gradient(135deg, #e0f2fe 0%, #cbd5e1 100%)"
    card_bg = "rgba(255, 255, 255, 0.92)"
    text_color = "#0f172a"
    accent_color = "#0284c7"
    border_color = "#0284c7"
    glow_shadow = "0 0 20px rgba(2, 132, 199, 0.3)"
    matrix_glow_color = "#0284c7"
    copilot_bg = "#ffffff"
    copilot_text = "#0f172a"
    copilot_bubble_user = "#0284c7"
    copilot_bubble_assistant = "#f1f5f9"
else:
    bg_color_solid = "#040714"
    bg_gradient = "radial-gradient(circle at 50% 10%, #0d2147 0%, #040714 90%)"
    card_bg = "rgba(10, 18, 36, 0.82)"
    text_color = "#f8fafc"
    accent_color = "#38bdf8"
    border_color = "#38bdf8"
    glow_shadow = "0 0 18px rgba(56, 189, 248, 0.4), inset 0 0 15px rgba(56, 189, 248, 0.15)"
    matrix_glow_color = "#38bdf8"
    copilot_bg = "#070d1d"
    copilot_text = "#f8fafc"
    copilot_bubble_user = "#38bdf8"
    copilot_bubble_assistant = "#101d38"

# LIVE GLOWING ANIMATED BACKGROUND INJECTION
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
        ctx.shadowBlur = 8;
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

# CSS STYLING
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
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #060b18 0%, #030611 100%) !important;
        border-right: 2px solid {border_color} !important;
        box-shadow: 8px 0px 35px rgba(56, 189, 248, 0.3) !important;
        z-index: 999999 !important;
        padding-top: 10px;
        overflow: visible !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="popover"], 
    section[data-testid="stSidebar"] [data-baseweb="menu"], 
    div[data-baseweb="select"] ul {{
        z-index: 9999999 !important;
        background-color: #060d1c !important;
        border: 1.5px solid {border_color} !important;
    }}
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h4 {{
        font-family: 'Inter', system-ui, sans-serif !important;
        letter-spacing: 0.1em !important;
        text-shadow: 0 0 15px {accent_color}, 0 0 25px rgba(56, 189, 248, 0.6) !important;
    }}
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span {{
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
    }}
    html, body, p, span, div, label, .stMarkdown, .stText {{
        color: {text_color} !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }}
    h1, h2, h3, h4 {{ color: {text_color} !important; font-weight: 700 !important; }}
    h1 {{ color: {accent_color} !important; text-shadow: 0 0 20px {accent_color}, 0 0 35px rgba(56, 189, 248, 0.6); }}
    textarea, input, select, div[data-baseweb="select"] > div {{
        color: {text_color} !important;
        background-color: rgba(6, 13, 28, 0.9) !important;
        border: 1.5px solid {border_color} !important;
        border-radius: 10px !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.25), inset 0 0 8px rgba(56, 189, 248, 0.1) !important;
    }}
    div[data-testid="stMetric"], .stExpander, div.stTabs {{
        background: {card_bg} !important;
        backdrop-filter: blur(20px) saturate(200%);
        border: 1px solid {border_color} !important;
        border-top: 3px solid {accent_color} !important;
        border-radius: 14px;
        padding: 18px 22px;
        box-shadow: {glow_shadow} !important;
    }}
    .soc-dashboard-hero {{
        background: linear-gradient(135deg, rgba(11, 19, 43, 0.95) 0%, rgba(4, 9, 22, 0.98) 100%) !important;
        border: 2px solid {border_color} !important;
        border-top: 6px solid {accent_color} !important;
        border-radius: 20px !important;
        padding: 32px !important;
        box-shadow: 0 0 40px rgba(56, 189, 248, 0.35), inset 0 0 20px rgba(56, 189, 248, 0.1) !important;
        margin-top: 15px !important;
        margin-bottom: 40px !important;
    }}
    .soc-metric-card {{
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 16px;
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
        border-radius: 12px;
        padding: 0.95rem 1.5rem;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.6), 0 0 40px rgba(0, 255, 204, 0.4);
    }}
    .live-hud-badge {{
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.2);
        border: 1.5px solid #34d399;
        color: #34d399;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.88rem;
        font-weight: 800;
        box-shadow: 0 0 18px rgba(52, 211, 153, 0.4);
    }}
    .live-hud-dot {{
        height: 10px; width: 10px;
        background-color: #34d399;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
        box-shadow: 0 0 15px #34d399;
        animation: pulse-animation 1.8s infinite;
    }}
    @keyframes pulse-animation {{
        0% {{ transform: scale(0.9); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.8); }}
        70% {{ transform: scale(1.15); box-shadow: 0 0 0 12px rgba(52, 211, 153, 0); }}
        100% {{ transform: scale(0.9); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }}
    }}
    .ioc-box {{
        background: rgba(3, 7, 18, 0.95);
        border: 1px solid {border_color};
        border-left: 4px solid #00ffcc;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-family: 'Courier New', monospace;
        color: #38bdf8;
    }}
    .playbook-container {{
        background-color: #020617 !important;
        border: 1.5px solid {border_color} !important;
        border-radius: 12px !important;
        padding: 18px 22px !important;
        margin-top: 10px !important;
        margin-bottom: 15px !important;
    }}
    .playbook-line {{
        font-family: 'Fira Code', 'Courier New', Consolas, monospace !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        color: #00ffcc !important;
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        margin-bottom: 4px !important;
    }}
    .playbook-comment {{
        color: #38bdf8 !important;
        font-weight: 700 !important;
    }}
    .stApp > div {{ padding-bottom: 90px; z-index: 10; position: relative; }}
    .developer-footer {{
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #03050c; color: #38bdf8 !important;
        text-shadow: 0 0 10px #38bdf8;
        text-align: center; padding: 10px; font-size: 0.88rem !important;
        font-weight: 700;
        border-top: 1px solid #1e293b; z-index: 999;
        letter-spacing: 0.1em;
    }}
    </style>
""", unsafe_allow_html=True)

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

def enrich_ip_data(ip_list, vt_key):
    results = []
    valid_ips = [ip for ip in ip_list if is_valid_public_ip(ip)]
    for ip in valid_ips[:3]:
        try:
            res = requests.get(f"http://ip-api.com/json/{ip.replace('[.]', '.')}", timeout=2).json()
            if res.get("status") == "success":
                results.append(f"IP {ip}: {res.get('org', 'Unknown Org')} ({res.get('country', 'Unknown')}) - ISP: {res.get('isp')}")
        except Exception:
            pass
            
    if vt_key and valid_ips:
        try:
            headers = {"x-apikey": vt_key}
            sample_ip = valid_ips[0].replace('[.]', '.')
            vt_res = requests.get(f"https://www.virustotal.com/api/v3/ip_addresses/{sample_ip}", headers=headers, timeout=2)
            if vt_res.status_code == 200:
                stats = vt_res.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                results.append(f"VT Intelligence: {sample_ip} malicious score = {stats.get('malicious', 0)} detections.")
        except Exception:
            pass
            
    return results

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
    report = [
        "================================================================================",
        "         SMART INTELLIGENCE | PLAIN-LANGUAGE ANALYST INSTRUCTIONS         ",
        "================================================================================",
        f"Target Scope          : {target_entity or 'Global Corporate Network'}",
        f"Overall Threat Rating : {risk_level}",
        f"Total Indicators Found: {total_iocs}",
        "================================================================================",
        "\n1. ABOUT THIS INSTRUCTION GUIDE",
        "--------------------------------------------------------------------------------",
        "This document explains the deliverables generated by the Smart Intelligence CTI",
        "Platform and breaks down your extracted Indicators of Compromise (IoCs) into clear,",
        "plain language for security analysts and incident responders.",
        "",
        "2. PLAIN-LANGUAGE BREAKDOWN OF EXTRACTED ARTIFACTS",
        "--------------------------------------------------------------------------------"
    ]
    
    ips = iocs.get("IPv4", [])
    if ips:
        report.append(f"• IP Addresses ({len(ips)} found):")
        report.append("  What they are: Network identifiers pointing to external or internal hosts.")
        report.append("  What they mean: In telemetry logs, external IPs often represent Command and")
        report.append("  Control (C2) servers, automated scanning bots, or active brute-force attempts.")
        report.append("  Recommended Action: Block malicious addresses at your perimeter firewall.")
        report.append("")
        
    hashes = iocs.get("SHA256", []) + iocs.get("MD5", [])
    if hashes:
        report.append(f"• Cryptographic File Hashes ({len(hashes)} found):")
        report.append("  What they are: Unique digital fingerprints calculated from file contents.")
        report.append("  What they mean: Indicates unauthorized executables or malicious payloads.")
        report.append("  Recommended Action: Run the generated YARA rule across your endpoints.")
        report.append("")

    return "\n".join(report)

# COPILOT REASONING ASSISTANT
def answer_copilot_reasoning(user_prompt):
    prompt_lower = user_prompt.lower()
    if any(k in prompt_lower for k in ["how", "use", "guide", "start", "begin", "steps", "workflow"]):
        return (
            "Here is your step-by-step workflow for **Smart Intelligence**:\n\n"
            "1. **Layer 1:** Specify your target scope.\n"
            "2. **Layer 2:** Ingest logs or threat reports.\n"
            "3. **Pipeline Execution:** Click **Execute 5-Layer Intelligence Pipeline** to watch the live engine run.\n"
            "4. **Layer 5:** Access executive briefings, IoC tables, and export bundles."
        )
    elif any(k in prompt_lower for k in ["hello", "hi", "hey"]):
        return "Hello! I am your **Gemini CTI Copilot**. How can I assist you with your threat analysis today?"
    else:
        return f"Regarding your query: *'{user_prompt}'*\n\nI am analyzing your telemetry and security workflow. Let me know if you need specific technical guidance!"

def run_live_ai_synthesis(target, raw_text, iocs, ttps, api_key):
    # Hybrid engine local fallback baseline
    text_lower = raw_text.lower()
    risk_score = 15
    if len(iocs.get("IPv4", [])) > 0: risk_score += 25
    if len(iocs.get("SHA256", [])) > 0 or len(iocs.get("MD5", [])) > 0: risk_score += 30
    if any(k in text_lower for k in ["powershell", "cmd.exe", "mimikatz", "ransom", "lsass"]): risk_score += 30
    risk_score = min(risk_score, 100)

    # If live API key is provided, attempt real online AI generation
    if api_key:
        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            prompt = f"Analyze this cyber threat data for target '{target}': {raw_text[:1000]}. Provide a concise professional SOC threat risk assessment and narrative."
            # Standard OpenAI / compatible endpoint structure or simulation
            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250
            }, timeout=4)
            if resp.status_code == 200:
                ai_text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                if ai_text:
                    return f"### 🤖 Layer 4: Live Cloud AI Intelligence & Reasoning Assessment\n**Calculated Risk Index:** `{risk_score}/100`\n\n{ai_text}", risk_score
        except Exception:
            pass

    # Default robust deterministic synthesis
    if risk_score >= 70:
        severity = "🔴 CRITICAL RISK (Immediate Active Threat Vector)"
    elif risk_score >= 40:
        severity = "🟡 ELEVATED RISK (Suspicious Activity Detected)"
    else:
        severity = "🟢 BASELINE TELEMETRY (Low Operational Risk)"

    narrative = [
        f"### 🤖 Layer 4: Hybrid Deterministic & Heuristic AI Synthesis",
        f"**Target Scope:** `{target if target else 'Global Enterprise Infrastructure'}`",
        f"**Calculated Threat Risk Index:** `{risk_score}/100` — **{severity}**",
        f"\n#### 🔬 Behavioral Telemetry & Correlation Results:",
        f" - Extracted `{sum(len(v) for v in iocs.values())}` total indicators across multi-source ingestion modules.",
        f" - Mapped `{len(ttps)}` MITRE ATT&CK tactical vectors from raw logs and threat notes."
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
    
    report = [
        "================================================================================",
        "             SMART INTELLIGENCE | C-SUITE EXECUTIVE THREAT BRIEFING            ",
        "================================================================================",
        f"DATE OF INCIDENT BRIEFING : {now_utc}",
        f"TARGET ENTITY / SCOPE     : {target_entity if target_entity else 'Global / Corporate Network'}",
        f"ANALYSIS TIMEFRAME        : {timeframe}",
        f"OVERALL THREAT RISK LEVEL : {risk_level}",
        f"CONFIDENCE RATING         : {accuracy_score}%",
        "================================================================================",
        "\n1. EXECUTIVE SUMMARY & THREAT OVERVIEW",
        "--------------------------------------------------------------------------------",
        f"Smart Intelligence has executed a 5-layer correlation analysis for {target_entity or 'the target infrastructure'}.",
        f"A total of {total_iocs} high-fidelity Indicators of Compromise (IoCs) were identified.",
        "================================================================================",
        "Report Compiled by Smart Intelligence CTI Engine | Author: blessingsmkandawire"
    ]
    return "\n".join(report)

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

# 4. HEADER BANNER & PROFESSIONAL TOP-RIGHT ADAPTIVE COPILOT POPOVER
st.image("https://encrypted-tbn1.gstatic.com/licensed-image?q=tbn:ANd9GcROn-mrBQe5btdrktqpXydcOjv7g-kthMpnU2tXpevypi1IkEe_ZHPFLaRy5VxKY4WNtuds3KQnZXLLx8Y", use_container_width=True)

col_hdr1, col_hdr2 = st.columns([3, 1])
with col_hdr1:
    st.title(t["welcome"])
    st.markdown(f"##### **{t['tagline']}**")

with col_hdr2:
    st.write("")
    with st.popover("🤖 CTI Copilot & Live AI", help="Click to open live CTI assistant"):
        st.markdown(f"""
            <div style="background-color: {copilot_bg}; color: {copilot_text}; padding: 4px; border-radius: 8px;">
                <h4 style="color: {copilot_text} !important; margin-bottom: 2px;">💡 Gemini CTI Copilot</h4>
                <p style="color: {copilot_text} !important; font-size: 0.82rem; opacity: 0.9;">Real-time interactive assistant & general guidance engine.</p>
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
                
                if st.session_state.voice_mode:
                    clean_speech = reply.replace('"', '').replace('\n', ' ')
                    st.components.v1.html(f"""
                        <script>
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                            var utterance = new SpeechSynthesisUtterance("{clean_speech}");
                            utterance.rate = 1.0;
                            window.speechSynthesis.speak(utterance);
                        }}
                        </script>
                    """, height=0)
                st.rerun()

    if st.session_state.sidebar_state == "collapsed":
        if st.button("🎛️ Open Control Panel"):
            st.session_state.sidebar_state = "expanded"
            st.rerun()

# LIVE STATUS HUD BADGE
st.markdown("""
    <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 10px;">
        <div class="live-hud-badge">
            <span class="live-hud-dot"></span> SYSTEM READY : LIVE HYBRID PIPELINE ONLINE
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

# LAYER 2: MULTI-SOURCE INGESTION
st.header(t["l2"])

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💻 (i) System & Network Logs",
    "🌐 (ii) OSINT",
    "🛡️ (iii) CSINT",
    "📡 (iv) Commercial Feeds",
    "📝 (v) Additional Info"
])

with tab1:
    st.subheader("System & Network Logs")
    log_text = st.text_area("Paste Raw Logs:", height=120, placeholder="Paste syslog, firewall, or web server logs here...")
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

# LAYER 3 & LAYER 4 PIPELINE TRIGGER WITH STAGED LIVE PROGRESS BAR
st.header("3. Core Pipeline Execution")

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
        st.error("Please provide input in at least one ingestion tab before processing.")
    else:
        # LIVE STAGED PROGRESS ANIMATION
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("🔄 Layer 1: Validating target scope & intelligence timeframe...")
        time.sleep(0.3)
        progress_bar.progress(20)

        status_text.text("🔄 Layer 2: Ingesting multi-source telemetry & parsing artifacts...")
        iocs = extract_iocs(combined_raw_data)
        time.sleep(0.4)
        progress_bar.progress(40)

        status_text.text("🔄 Layer 3: Running regex extraction & live API feed lookups...")
        ttps = map_ttp_heuristics(combined_raw_data)
        live_enrichment = enrich_ip_data(iocs.get("IPv4", []), vt_api_key) if enable_live_enrichment else []
        time.sleep(0.4)
        progress_bar.progress(65)

        status_text.text("🔄 Layer 4: Executing AI threat correlation & risk scoring...")
        st.session_state.ai_analysis_result, computed_risk_score = run_live_ai_synthesis(
            target_entity, combined_raw_data, iocs, ttps, ai_api_key
        )
        time.sleep(0.4)
        progress_bar.progress(85)

        status_text.text("🔄 Layer 5: Compiling playbooks, YARA rules, and export deliverables...")
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

        time.sleep(0.3)
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()

        st.success("⚡ Live 5-Layer Intelligence Pipeline Execution Complete!")

        # ==========================================
        # LAYER 5: PROFESSIONAL SOC OPERATIONAL DASHBOARD HERO
        # ==========================================
        st.markdown('<div class="soc-dashboard-hero">', unsafe_allow_html=True)
        st.markdown(f"<h2 style='color: #38bdf8; margin-bottom: 5px;'>🚀 {t['l5']}</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8; font-size: 0.95rem; margin-bottom: 20px;'>Enterprise Operational Command Center — Real-time threat correlation, indicators, and defensive playbooks.</p>", unsafe_allow_html=True)

        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        
        with col_m1:
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem; color:#94a3b8;'>TARGET ENTITY</span><h3 style='color:#38bdf8; margin:5px 0; font-size:1.1rem;'>{target_entity if target_entity else 'Global'}</h3></div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem; color:#94a3b8;'>IOCs EXTRACTED</span><h3 style='color:#38bdf8; margin:5px 0; font-size:1.5rem;'>{total_iocs}</h3></div>", unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem; color:#94a3b8;'>TTPs MAPPED</span><h3 style='color:#38bdf8; margin:5px 0; font-size:1.5rem;'>{len(ttps)}</h3></div>", unsafe_allow_html=True)
        with col_m4:
            risk_color = "#ef4444" if "CRITICAL" in risk_level else "#f59e0b" if "HIGH" in risk_level else "#10b981"
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem; color:#94a3b8;'>RISK RATING</span><h3 style='color:{risk_color}; margin:5px 0; font-size:1.2rem;'>{risk_level}</h3></div>", unsafe_allow_html=True)
        with col_m5:
            st.markdown(f"<div class='soc-metric-card'><span style='font-size:0.8rem; color:#94a3b8;'>CONFIDENCE</span><h3 style='color:#38bdf8; margin:5px 0; font-size:1.5rem;'>{accuracy_score}%</h3></div>", unsafe_allow_html=True)

        st.write("")

        if st.session_state.ai_analysis_result:
            st.info(st.session_state.ai_analysis_result)

        st.write("")

        # ADVANCED SOC TABBED NAVIGATION
        soc_tab1, soc_tab2, soc_tab3, soc_tab4 = st.tabs([
            "📊 Telemetry & Correlation",
            "🔍 IoC Inspector",
            "🛡️ Playbook Armory",
            "📦 Deliverables & Exports"
        ])

        with soc_tab1:
            col_graph1, col_graph2 = st.columns(2)
            with col_graph1:
                st.subheader("📈 IoC Telemetry Breakdown")
                chart_data = pd.DataFrame({
                    'Indicator Category': list(iocs.keys()),
                    'Count': [len(v) for v in iocs.values()]
                })
                bar_chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                    x=alt.X('Indicator Category:N', sort=None, title="IoC Type", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('Count:Q', title="Detected Count", axis=alt.Axis(tickMinStep=1)),
                    color=alt.Color('Indicator Category:N', scale=alt.Scale(scheme='tableau10'), legend=None),
                    tooltip=['Indicator Category', 'Count']
                ).properties(height=280).configure_axis(
                    gridColor='#1e293b', domainColor='#334155', labelColor='#cbd5e1', titleColor='#f8fafc'
                ).configure_view(strokeWidth=0)
                st.altair_chart(bar_chart, use_container_width=True)

            with col_graph2:
                st.subheader("🕸️ Layer 3 Interactive Threat Correlation Graph")
                graph_nodes = []
                target_label = target_entity or "Target Scope"
                
                for cat, items in iocs.items():
                    for item in items[:4]:
                        graph_nodes.append({
                            "Target_Entity": target_label,
                            "Indicator": str(item),
                            "Category": cat,
                            "Risk_Weight": 85 if cat in ["IPv4", "SHA256"] else 45
                        })
                
                if graph_nodes:
                    gdf = pd.DataFrame(graph_nodes)
                    base = alt.Chart(gdf).encode(
                        x=alt.X('Target_Entity:N', title="Target Environment Scope"),
                        y=alt.Y('Indicator:N', title="Extracted Threat Artifacts"),
                        color=alt.Color('Category:N', scale=alt.Scale(scheme='set1'), title="Indicator Class"),
                        size=alt.Size('Risk_Weight:Q', scale=alt.Scale(range=[150, 400]), legend=None),
                        tooltip=['Target_Entity', 'Indicator', 'Category', 'Risk_Weight']
                    )
                    points = base.mark_circle(opacity=0.85, stroke='#00ffcc', strokeWidth=1.5)
                    rules = base.mark_rule(strokeDash=[4, 4], opacity=0.4, color='#38bdf8')
                    correlation_chart = (rules + points).properties(height=280).configure_axis(
                        gridColor='#1e293b', domainColor='#334155', labelColor='#cbd5e1', titleColor='#f8fafc'
                    ).configure_view(strokeWidth=0)
                    st.altair_chart(correlation_chart, use_container_width=True)
                else:
                    st.info("Insufficient IoC nodes to render correlation graph.")

            if live_enrichment:
                st.subheader("🌐 Layer 3 Live Feed & API Enrichment Data")
                for item in live_enrichment:
                    st.warning(f"📡 {item}")

        with soc_tab2:
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

        with soc_tab3:
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

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)

# DEVELOPER FOOTER
st.markdown(
    '<div class="developer-footer">developed by blessingsmkandawire</div>',
    unsafe_allow_html=True
)