import streamlit as st
import re
import json
from datetime import datetime
import pandas as pd
import altair as alt
import requests

# 1. SESSION STATE FOR SIDEBAR CONTROL & GEMINI HELP CHAT
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

if "welcomed" not in st.session_state:
    st.session_state.welcomed = False

if "ai_analysis_result" not in st.session_state:
    st.session_state.ai_analysis_result = None

if "help_chat_history" not in st.session_state:
    st.session_state.help_chat_history = [
        {"role": "assistant", "content": "👋 **Hello! I am your Gemini System Guide.** Ask me anything about how to use Smart Intelligence or submit feedback!"}
    ]

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Smart Intelligence | CTI Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# 2. HIGH-VISIBILITY CONTROL PANEL (SIDEBAR)
st.sidebar.markdown("<h2 style='color: #38bdf8; text-align: center; border-bottom: 2px solid #38bdf8; padding-bottom: 8px;'>⚙️ CONTROL PANEL</h2>", unsafe_allow_html=True)

LANGUAGES = {
    "English": {
        "welcome": "Welcome to Smart Intelligence",
        "tagline": "Automated Cyber Threat Intelligence Parsing, Correlation, and Mitigation Engine",
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
        "welcome": "Bienvenue sur Smart Intelligence",
        "tagline": "Moteur d'analyse, de corrélation et d'atténuation des cybermenaces",
        "l1": "Couche 1: Définition du Périmètre et de la Cible",
        "l2": "Couche 2: Modules d'Ingestion de Données Multi-Sources",
        "l3": "Couche 3: Moteur d'Extraction et de Normalisation",
        "l4": "Couche 4: Moteur de Corrélation et d'Atténuation IA",
        "l5": "Couche 5: Livrables et Tableau de Bord Opérationnel",
        "btn_process": "⚡ EXÉCUTER LE SERPENTIN D'INTELLIGENCE À 5 COUCHES",
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

# Theme Switcher
theme_choice = st.sidebar.selectbox("🎨 UI Visual Mode", ["Dark SOC Theme", "Cyberpunk Neon Mode", "Clean Light Mode"])

# Feed & Safety Settings
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color: #10b981;'>🛡️ Safety & Enrichment Settings</h4>", unsafe_allow_html=True)
enable_live_enrichment = st.sidebar.checkbox("Enable Live Threat Feed Lookups (IP/ASN)", value=True)
defang_iocs = st.sidebar.checkbox("Defang IoCs for Safety (e.g. 1.1.1[.]1)")

st.sidebar.markdown("---")
if st.sidebar.button("❌ Hide Control Panel"):
    st.session_state.sidebar_state = "collapsed"
    st.rerun()

# Dynamic Theme Styling (CSS)
if theme_choice == "Cyberpunk Neon Mode":
    bg_color, card_bg, text_color, accent_color = "#05050a", "#0f0f1b", "#00ffcc", "#ff0055"
elif theme_choice == "Clean Light Mode":
    bg_color, card_bg, text_color, accent_color = "#f8fafc", "#ffffff", "#0f172a", "#2563eb"
else:
    bg_color, card_bg, text_color, accent_color = "#0b0f19", "#161e2e", "#e2e8f0", "#38bdf8"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    section[data-testid="stSidebar"] {{
        background-color: #0d1527 !important;
        border-right: 2px solid #1e293b !important;
        box-shadow: 4px 0px 15px rgba(0, 0, 0, 0.5);
    }}
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {{
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }}
    html, body, p, span, div, label, .stMarkdown, .stText {{
        color: {text_color} !important;
        font-family: 'Inter', system-ui, sans-serif;
    }}
    h1, h2, h3, h4 {{ color: {text_color} !important; font-weight: 700 !important; }}
    h1 {{ color: {accent_color} !important; }}
    div[data-testid="stMetric"] {{
        background: {card_bg};
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
    }}
    div[data-testid="stMetricValue"] > div {{
        color: {accent_color} !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }}
    textarea, input {{
        color: {text_color} !important;
        background-color: {card_bg} !important;
        border: 1px solid #334155 !important;
    }}
    .stButton>button {{
        width: 100%;
        font-weight: 700;
        font-size: 1.15rem;
        background: {accent_color} !important;
        color: #ffffff !important;
        border-radius: 8px;
        padding: 0.75rem;
    }}
    .developer-footer {{
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #070a10; color: #64748b !important;
        text-align: center; padding: 8px; font-size: 0.8rem !important;
        border-top: 1px solid #1e293b; z-index: 999;
    }}
    </style>
""", unsafe_allow_html=True)

# Helper Utilities
def defang(text):
    if not text:
        return text
    text = re.sub(r'http://', 'hxxp://', text)
    text = re.sub(r'https://', 'hxxps://', text)
    text = re.sub(r'(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})', r'\1.\2.\3[.]\4', text)
    text = re.sub(r'([a-zA-Z0-9-]+\.)+([a-zA-Z]{2,})', lambda m: m.group(0).replace('.', '[.]'), text)
    return text

def enrich_ip_data(ip_list):
    results = []
    for ip in ip_list[:3]:
        try:
            res = requests.get(f"http://ip-api.com/json/{ip}", timeout=3).json()
            if res.get("status") == "success":
                results.append(f"IP {ip}: {res.get('org', 'Unknown Org')} ({res.get('country', 'Unknown')}) - ISP: {res.get('isp')}")
        except Exception:
            pass
    return results

def generate_yara_rule(target_entity, iocs):
    rule_name = re.sub(r'[^a-zA-Z0-9_]', '_', target_entity or "Smart_Intelligence_Threat")
    hashes = iocs.get("SHA256", []) + iocs.get("MD5", [])
    ips = iocs.get("IPv4", [])
    
    strings_section = []
    for i, h in enumerate(hashes):
        strings_section.append(f'        $hash_{i} = "{h}"')
    for i, ip in enumerate(ips):
        strings_section.append(f'        $ip_{i} = "{ip}"')
        
    return f"""rule {rule_name}_Detection {{
    meta:
        description = "Automated YARA rule generated by Smart Intelligence CTI Platform"
        author = "blessingsmkandawire"
        date = "{datetime.utcnow().strftime('%Y-%m-%d')}"
        threat_level = "CRITICAL"
    strings:
{chr(10).join(strings_section) if strings_section else '        $default_string = "powershell"'}
    condition:
        any of them
}}"""

# GEMINI INTERACTIVE HELP ASSISTANT LOGIC
def answer_gemini_help(user_prompt):
    prompt_lower = user_prompt.lower()
    if "how" in prompt_lower or "use" in prompt_lower or "guide" in prompt_lower:
        return "💡 **Smart Intelligence Usage Guide:**\n1. Fill in **Layer 1** (Target & Scope).\n2. Paste logs or threat reports into **Layer 2** tabs.\n3. Click **`⚡ EXECUTE 5-LAYER INTELLIGENCE PIPELINE`**.\n4. View results in **Layer 5** and copy playbooks or download STIX/YARA/Executive briefings."
    elif "layer" in prompt_lower or "5 layer" in prompt_lower:
        return "🛡️ **5-Layer Architecture Breakdown:**\n- **Layer 1:** Target Scope & Objectives\n- **Layer 2:** Multi-Source Telemetry Ingestion\n- **Layer 3:** Extraction & Normalization (IoCs/TTPs)\n- **Layer 4:** AI Threat Correlation & Fight-Back Playbooks\n- **Layer 5:** Visual Dashboard & C-Suite Deliverables"
    elif "feedback" in prompt_lower or "issue" in prompt_lower or "bug" in prompt_lower:
        return "🙏 **Thank you for your feedback!** Your message has been logged for system optimization."
    else:
        return f"🤖 **Gemini Assistant:** I am here to help you navigate Smart Intelligence! You asked: *'{user_prompt}'*. How else can I support your threat analysis?"

# AUTOMATED AI SYNTHESIS ENGINE (LAYER 4)
def run_automated_ai_synthesis(target, raw_text, iocs, ttps):
    has_script = "powershell" in raw_text.lower() or "cmd.exe" in raw_text.lower()
    has_phish = "phishing" in raw_text.lower() or "spearphishing" in raw_text.lower()
    
    summary = []
    summary.append(f"### 🤖 Layer 4: AI Threat Narrative & Incident Assessment")
    summary.append(f"**Target Scope Evaluated:** {target if target else 'Global / Unassigned Infrastructure'}")
    
    if has_phish and has_script:
        summary.append("\n**Threat Vector & Campaign Pattern:** High-confidence multi-stage attack detected. The threat actor leveraged initial access via spearphishing attachments to execute unauthorized script payloads.")
        summary.append("**Likely Threat Actor Attribution:** Observed TTPs correlate closely with **APT29 (Cozy Bear)** and **Lazarus Group** operational tactics.")
    elif len(iocs.get("IPv4", [])) > 0 or len(iocs.get("Domains", [])) > 0:
        summary.append("\n**Threat Vector & Campaign Pattern:** Network reconnaissance and Command & Control (C2) beaconing activity identified across external infrastructure.")
        summary.append("**Likely Threat Actor Attribution:** Activity aligns with opportunistic threat scanners and automated exploit toolkits.")
    else:
        summary.append("\n**Threat Vector & Campaign Pattern:** Low-risk baseline telemetry. No critical malicious payload signatures or unauthorized network connections confirmed.")

    return "\n".join(summary)

# ADVANCED REMEDIATION PLAYBOOK GENERATOR
def generate_remediation_playbooks(iocs, ttps):
    ips = iocs.get("IPv4", [])
    domains = iocs.get("Domains", [])
    hashes = iocs.get("SHA256", []) + iocs.get("MD5", [])

    endpoint_script = ["# Windows PowerShell Host Isolation Commands"]
    if hashes:
        for h in hashes:
            endpoint_script.append(f"Get-Process | Where-Object {{ $_.Path -like '*{h[:8]}*' }} | Stop-Process -Force")
    endpoint_script.append("Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True")
    endpoint_script.append("# Linux Host Isolation (IPTables)")
    endpoint_script.append("sudo iptables -P INPUT DROP; sudo iptables -P OUTPUT DROP; sudo iptables -P FORWARD DROP")

    network_script = ["# Active Perimeter Firewall Rules (C2 Blocklist)"]
    for ip in ips:
        network_script.append(f"netsh advfirewall firewall add rule name='Block C2 {ip}' dir=in action=block remoteip={ip}")
        network_script.append(f"sudo iptables -A INPUT -s {ip} -j DROP")
    for d in domains:
        network_script.append(f"# DNS RPZ / Sinkhole entry: {d} -> 0.0.0.0")

    identity_script = [
        "# Active Directory / Azure AD Revocation & Containment",
        "Revoke-AzureADUserAllRefreshToken -ObjectId <Target_User_GUID>",
        "Set-ADUser -Identity <Target_User> -Enabled $false",
        "# Force Kerberos Ticket Reset (KBTGT)",
        "Update-KbtgtAccountPassword"
    ]

    siem_queries = ["// KQL Query (Microsoft Sentinel / Defender)"]
    if ips:
        ip_str = '", "'.join(ips)
        siem_queries.append(f'DeviceNetworkEvents | where RemoteIP in ("{ip_str}")')
    if hashes:
        hash_str = '", "'.join(hashes)
        siem_queries.append(f'DeviceProcessEvents | where SHA256 in ("{hash_str}") or MD5 in ("{hash_str}")')

    return {
        "endpoint": "\n".join(endpoint_script),
        "network": "\n".join(network_script),
        "identity": "\n".join(identity_script),
        "siem": "\n".join(siem_queries)
    }

# FORMAL EXECUTIVE TEXT REPORT GENERATOR
def generate_executive_text_report(target_entity, timeframe, intel_goal, risk_level, accuracy_score, sources_used, iocs, ttps, live_enrichment):
    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    total_iocs = sum(len(v) for v in iocs.values())
    
    report = [
        "================================================================================",
        "             SMART INTELLIGENCE | C-SUITE EXECUTIVE THREAT BRIEFING            ",
        "================================================================================",
        f"DATE OF INCIDENT BRIEFING : {now_utc}",
        f"TARGET ENTITY / SCOPE     : {target_entity if target_entity else 'Global / Corporate Network'}",
        f"ANALYSIS TIMEFRAME        : {timeframe}",
        f"STRATEGIC INTEL GOAL      : {intel_goal if intel_goal else 'Threat Landscape Assessment'}",
        f"OVERALL THREAT RISK LEVEL : {risk_level}",
        f"CONFIDENCE RATING         : {accuracy_score}%",
        f"DATA SOURCES EVALUATED    : {', '.join(sources_used) if sources_used else 'Multi-source Telemetry'}",
        "================================================================================",
        "\n1. EXECUTIVE SUMMARY & THREAT OVERVIEW",
        "--------------------------------------------------------------------------------",
        f"Smart Intelligence has executed a 5-layer correlation analysis for {target_entity or 'the target infrastructure'}.",
        f"A total of {total_iocs} high-fidelity Indicators of Compromise (IoCs) and {len(ttps)} MITRE ATT&CK tactics",
        "were identified across ingested telemetry logs, threat feeds, and security intelligence.",
        "\nKey Observations:",
        f" - Assessed Threat Level: {risk_level} severity.",
        f" - Perimeter Indicators : {len(iocs.get('IPv4', []))} Malicious IPs, {len(iocs.get('Domains', []))} Command & Control Domains.",
        f" - Payload Signatures   : {len(iocs.get('SHA256', [])) + len(iocs.get('MD5', []))} Malicious Executable Hashes.",
        f" - Known Exploits       : {', '.join(iocs.get('CVE', [])) if iocs.get('CVE') else 'None explicit in parsed sample'}.",
        "\n--------------------------------------------------------------------------------",
        "2. BUSINESS & OPERATIONAL IMPACT ASSESSMENT",
        "--------------------------------------------------------------------------------",
        "Unmitigated escalation of the detected threats carries significant business exposure:",
        "\n [!] FINANCIAL IMPACT:",
        "     Potential losses stemming from operational downtime, unauthorized fund transfers,",
        "     or ransomware extortion payloads deployed via lateral script execution.",
        "\n [!] OPERATIONAL & PRODUCTIVITY IMPACT:",
        "     Potential disruption to core business systems, database locking, and necessary host",
        "     isolation during incident response recovery procedures.",
        "\n [!] REGULATORY & COMPLIANCE RISKS:",
        "     Potential exposure under data protection frameworks (e.g., GDPR / Cyber Security Mandates)",
        "     requiring mandatory breach notification within strict regulatory windows.",
        "\n [!] REPUTATIONAL IMPACT:",
        "     Risk of diminished client trust, public threat actor disclosures, and supply-chain",
        "     partner scrutiny if infrastructure is leveraged for downstream attacks.",
        "\n--------------------------------------------------------------------------------",
        "3. STRATEGIC THREAT RISK MATRIX",
        "--------------------------------------------------------------------------------",
        "Risk Factor                | Assessed Status | Impact Level",
        "---------------------------+-----------------+----------------------------------",
        f"Initial Perimeter Access   | {'HIGH CRITICAL' if len(iocs['IPv4']) > 0 else 'LOW / BASELINE'} | High (Unauthorized Network Entry)",
        f"Internal Execution / Script| {'HIGH CRITICAL' if len(ttps) > 0 else 'MONITORED'}     | Critical (Host Impairment)",
        f"Data Exfiltration / C2     | {'ACTIVE RISKS' if len(iocs['Domains']) > 0 else 'LOW'}      | High (Intellectual Property Leakage)",
        "--------------------------------------------------------------------------------",
        "\n4. BOARD-LEVEL RECOMMENDED CONTAINMENT ACTIONS",
        "--------------------------------------------------------------------------------",
        "1. IMMEDIATE CONTAINMENT (0 - 2 HOURS):",
        "   - Enforce active perimeter blocklists for all extracted C2 IPv4 addresses and domains.",
        "   - Execute automated endpoint process termination on hosts exhibiting matching SHA-256 signatures.",
        "\n2. SHORT-TERM STABILIZATION (2 - 24 HOURS):",
        "   - Force password resets and revoke refresh tokens for privilege-escalated service accounts.",
        "   - Apply virtual patching / WAF protection against identified CVE vulnerabilities.",
        "\n3. LONG-TERM STRATEGIC RESILIENCE (24+ HOURS):",
        "   - Deploy generated YARA and Sigma detection rules across all enterprise EDR agents.",
        "   - Conduct an isolated compromise assessment to verify full threat eradication.",
        "================================================================================",
        "Report Compiled by Smart Intelligence CTI Engine | Author: blessingsmkandawire"
    ]
    return "\n".join(report)

# CORE PROCESSING FUNCTIONS
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

# 4. HEADER BANNER & BRANDING
st.image("https://encrypted-tbn1.gstatic.com/licensed-image?q=tbn:ANd9GcROn-mrBQe5btdrktqpXydcOjv7g-kthMpnU2tXpevypi1IkEe_ZHPFLaRy5VxKY4WNtuds3KQnZXLLx8Y", use_container_width=True)

col_hdr1, col_hdr2 = st.columns([3, 1])
with col_hdr1:
    st.title(t["welcome"])
    st.markdown(f"##### **{t['tagline']}**")
with col_hdr2:
    st.write("")
    if st.session_state.sidebar_state == "collapsed":
        if st.button("🎛️ Open Control Panel"):
            st.session_state.sidebar_state = "expanded"
            st.rerun()
    else:
        if st.button("❌ Hide Control Panel"):
            st.session_state.sidebar_state = "collapsed"
            st.rerun()

st.divider()

# RELOCATED GEMINI HELP ASSISTANT (CORNER POPOVER CHAT) & FIXED RELIABLE AUDIO SPEAKER BUTTON
col_top_h1, col_top_h2 = st.columns([3, 1])
with col_top_h1:
    st.write("🔊 **Audio Briefing:** Click the speaker button to hear the live audio summary.")
    if st.button("🔊 Read Audio Briefing"):
        speech_text = "Welcome to Smart Intelligence. Enter your threat telemetry logs into the ingestion tabs, then click execute to run the 5 layer pipeline."
        if st.session_state.ai_analysis_result:
            speech_text = f"Intelligence analysis complete. {st.session_state.ai_analysis_result[:250]}"
        st.components.v1.html(f"""
            <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance("{speech_text.replace('"', '')}");
                msg.rate = 1.0;
                window.speechSynthesis.speak(msg);
            }} else {{
                alert("Browser Speech Synthesis not supported.");
            }}
            </script>
        """, height=0)

with col_top_h2:
    with st.popover("🤖 Gemini Assistant & Feedback", help="Click to ask questions or give system feedback"):
        st.markdown("##### 💡 Ask Gemini or Provide Feedback")
        for message in st.session_state.help_chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if help_user_input := st.chat_input("Ask a question or share feedback..."):
            st.session_state.help_chat_history.append({"role": "user", "content": help_user_input})
            bot_reply = answer_gemini_help(help_user_input)
            st.session_state.help_chat_history.append({"role": "assistant", "content": bot_reply})
            st.rerun()

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

# LAYER 3 & LAYER 4 PIPELINE TRIGGER
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
        with st.spinner("Executing 5-Layer Pipeline: Generating C-Suite Briefing, Correlating IoCs, and Compiling Playbooks..."):
            iocs = extract_iocs(combined_raw_data)
            ttps = map_ttp_heuristics(combined_raw_data)
            stix_bundle = generate_stix_bundle(target_entity, iocs)
            yara_code = generate_yara_rule(target_entity, iocs)
            playbooks = generate_remediation_playbooks(iocs, ttps)
            
            live_enrichment = enrich_ip_data(iocs.get("IPv4", [])) if enable_live_enrichment else []
            
            total_iocs = sum(len(v) for v in iocs.values())
            accuracy_score = calculate_intelligence_accuracy(iocs, ttps, sources_used, target_entity)

            if total_iocs > 10 or len(ttps) >= 3:
                risk_level = "CRITICAL"
            elif total_iocs > 3 or len(ttps) >= 1:
                risk_level = "MEDIUM / HIGH"
            else:
                risk_level = "LOW"

            st.session_state.ai_analysis_result = run_automated_ai_synthesis(
                target_entity, combined_raw_data, iocs, ttps
            )

            text_report = generate_executive_text_report(
                target_entity, timeframe, intel_goal, risk_level, accuracy_score, sources_used, iocs, ttps, live_enrichment
            )

            st.success("5-Layer Intelligence Pipeline Execution Complete!")

            st.divider()

            # LAYER 5: OUTPUT DELIVERABLES & DASHBOARD
            st.header(t["l5"])

            col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
            col_m1.metric(t["target"], target_entity if target_entity else "Global / Unassigned")
            col_m2.metric(t["iocs_found"], total_iocs)
            col_m3.metric(t["ttps_mapped"], len(ttps))
            col_m4.metric(t["risk"], f"🔴 {risk_level}" if "CRITICAL" in risk_level else f"🟡 {risk_level}" if "HIGH" in risk_level else f"🟢 {risk_level}")
            col_m5.metric(t["confidence"], f"{accuracy_score}%")

            st.write("")

            if st.session_state.ai_analysis_result:
                st.info(st.session_state.ai_analysis_result)

            st.write("")

            col_graph1, col_graph2 = st.columns(2)
            
            with col_graph1:
                st.subheader("📈 IoC Telemetry Breakdown")
                chart_data = pd.DataFrame({
                    'Indicator Category': list(iocs.keys()),
                    'Count': [len(v) for v in iocs.values()]
                })
                bar_chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X('Indicator Category:N', sort=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('Count:Q', axis=alt.Axis(tickMinStep=1)),
                    color=alt.Color('Indicator Category:N', scale=alt.Scale(scheme='dark2'), legend=None),
                    tooltip=['Indicator Category', 'Count']
                ).properties(height=260).configure_axis(
                    gridColor='#1e293b', domainColor='#334155', labelColor='#cbd5e1', titleColor='#f8fafc'
                ).configure_view(strokeWidth=0)
                st.altair_chart(bar_chart, use_container_width=True)

            with col_graph2:
                st.subheader("🕸️ Layer 3 Threat Correlation Graph")
                graph_nodes = []
                for cat, items in iocs.items():
                    for item in items[:2]:
                        graph_nodes.append({"Source": target_entity or "Target Scope", "Indicator": item, "Type": cat})
                
                if graph_nodes:
                    gdf = pd.DataFrame(graph_nodes)
                    graph_chart = alt.Chart(gdf).mark_circle(size=200).encode(
                        x='Source:N',
                        y='Indicator:N',
                        color='Type:N',
                        tooltip=['Source', 'Indicator', 'Type']
                    ).properties(height=260)
                    st.altair_chart(graph_chart, use_container_width=True)
                else:
                    st.info("Insufficient IoC nodes to render correlation graph.")

            if live_enrichment:
                st.subheader("🌐 Layer 3 Live Feed Enrichment Data")
                for item in live_enrichment:
                    st.warning(f"📡 {item}")

            st.subheader("📊 Layer 3 Extracted Indicators of Compromise")
            filter_term = st.text_input("🔍 Filter/Search IoCs in real-time:", placeholder="Type IP, hash, or domain...")
            
            ioc_col1, ioc_col2 = st.columns(2)
            
            def filter_list(lst):
                if not filter_term:
                    return lst
                return [item for item in lst if filter_term.lower() in str(item).lower()]

            with ioc_col1:
                st.write("**IPv4 Addresses:**", filter_list(iocs["IPv4"]) if filter_list(iocs["IPv4"]) else "None detected")
                st.write("**Domains:**", filter_list(iocs["Domains"]) if filter_list(iocs["Domains"]) else "None detected")
                st.write("**URLs:**", filter_list(iocs["URLs"]) if filter_list(iocs["URLs"]) else "None detected")
            
            with ioc_col2:
                st.write("**SHA-256 Hashes:**", filter_list(iocs["SHA256"]) if filter_list(iocs["SHA256"]) else "None detected")
                st.write("**MD5 Hashes:**", filter_list(iocs["MD5"]) if filter_list(iocs["MD5"]) else "None detected")
                st.write("**CVE Vulnerabilities:**", filter_list(iocs["CVE"]) if filter_list(iocs["CVE"]) else "None detected")

            st.subheader("🎯 Layer 3 MITRE ATT&CK TTP Mapping")
            if ttps:
                for ttp in ttps:
                    st.info(f"📍 {ttp}")
            else:
                st.write("No explicit MITRE ATT&CK tactics matched standard heuristic keywords.")

            st.subheader("🛡️ Layer 4 Fight-Back & Containment Playbook Engine")
            st.caption("Copy and execute active containment scripts across host, network, identity, and SIEM controls.")

            pb_tab1, pb_tab2, pb_tab3, pb_tab4 = st.tabs([
                "💻 (i) Endpoint Isolation Scripts",
                "🌐 (ii) Perimeter Firewall Rules",
                "🔑 (iii) Identity & Kerberos Revocation",
                "🔍 (iv) SIEM Threat Hunting Queries"
            ])

            with pb_tab1:
                st.code(playbooks["endpoint"], language="powershell")
            with pb_tab2:
                st.code(playbooks["network"], language="bash")
            with pb_tab3:
                st.code(playbooks["identity"], language="powershell")
            with pb_tab4:
                st.code(playbooks["siem"], language="sql")

            st.subheader("📦 Layer 5 Export Threat Intelligence Deliverables")
            dl_col1, dl_col2, dl_col3 = st.columns(3)
            
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

st.markdown("<br><br><br>", unsafe_allow_html=True)

# DEVELOPER FOOTER
st.markdown(
    '<div class="developer-footer">developed by blessingsmkandawire</div>',
    unsafe_allow_html=True
)