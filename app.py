# app.py — Nexus Load Balancer (Enhanced Dark Theme)

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time
from collections import deque
from datetime import datetime
import random

# ======================= PROBE =======================
from probe import probe_server

# ======================= PAGE CONFIG =======================
st.set_page_config(
    page_title="Nexus Load Balancer Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================= DEFAULT SERVERS =======================
DEFAULT_SERVERS = [
    "https://www.google.com",
    "https://www.github.com",
    "https://www.wikipedia.org"
]

if "SERVERS" not in st.session_state:
    st.session_state.SERVERS = DEFAULT_SERVERS.copy()

# ======================= SCORING FUNCTION =======================
def compute_score(pred_rtt, pred_load, pred_health, error_rate, pred_bandwidth,
                  alpha=1.0, beta=0.5, gamma=0.3, delta=0.2, epsilon=0.4):

    if pred_rtt is None:
        return float("inf")

    health_penalty = (100 - pred_health) / 100.0
    bandwidth_penalty = (1000 - pred_bandwidth) / 1000.0 if pred_bandwidth else 1.0

    return (
        alpha * pred_rtt +
        beta * (pred_load / 100.0) +
        gamma * health_penalty +
        delta * error_rate +
        epsilon * bandwidth_penalty
    )

# ======================= THEME (FIXED TO DARK) =======================
st.session_state.theme = "dark"

# ======================= STUNNING DARK THEME CSS =======================
def get_ultimate_css(theme):
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Root Variables */
    :root {
        --primary-blue: #3b82f6;
        --primary-purple: #8b5cf6;
        --accent-cyan: #06b6d4;
        --dark-bg: #0a0f1e;
        --card-bg: #141b2d;
        --card-border: rgba(59, 130, 246, 0.2);
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
    }
    
    /* Global Styles */
    body, .stApp {
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: linear-gradient(180deg, #0a0f1e 0%, #0f1729 50%, #1a1f3a 100%);
        background-attachment: fixed;
        color: var(--text-primary);
    }
    
    /* Animated Background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(6, 182, 212, 0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Main content wrapper */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        position: relative;
        z-index: 1;
    }

    /* Typography */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }

    h2 { 
        color: var(--text-primary) !important; 
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        letter-spacing: -0.01em;
    }
    
    h3 { 
        color: var(--text-primary) !important; 
        font-weight: 600 !important;
        font-size: 1.125rem !important;
    }

    /* Custom Card Styles */
    .custom-card {
        background: var(--card-bg);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 1.75rem;
        border: 1px solid var(--card-border);
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.3),
            0 2px 4px -1px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 0 rgba(255, 255, 255, 0.05);
        margin-bottom: 1.25rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .custom-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent, 
            var(--primary-blue), 
            var(--primary-purple), 
            transparent
        );
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .custom-card:hover::before {
        opacity: 1;
    }
    
    .custom-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 
            0 8px 16px -4px rgba(59, 130, 246, 0.2),
            0 4px 6px -1px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 0 rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
        color: white;
        border-radius: 12px;
        padding: 0.875rem 2rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        border: none;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.9375rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px -4px rgba(59, 130, 246, 0.5);
        background: linear-gradient(135deg, #4f8ff7, #9d6ef7);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }

    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.375rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .badge-online {
        background: linear-gradient(135deg, var(--success), var(--accent-cyan));
        color: white;
    }

    .badge-waiting {
        background: linear-gradient(135deg, var(--warning), var(--error));
        color: white;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(20, 27, 45, 0.98), rgba(10, 15, 30, 0.98));
        border-right: 1px solid rgba(59, 130, 246, 0.15);
        backdrop-filter: blur(20px);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: var(--text-primary) !important;
    }

    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background: rgba(20, 27, 45, 0.6) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.875rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
    }

    /* Sliders */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-purple)) !important;
    }
    
    /* Slider Value Display - Remove Blue Background */
    .stSlider [data-baseweb="slider"] {
        background: transparent !important;
    }
    
    .stSlider [data-testid="stTickBar"] > div {
        background: transparent !important;
        color: var(--text-primary) !important;
    }
    
    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        padding: 0 !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        color: var(--primary-blue) !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(20, 27, 45, 0.3);
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--primary-blue), var(--primary-purple));
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #4f8ff7, #9d6ef7);
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: rgba(20, 27, 45, 0.6);
        border-radius: 12px;
        border: 1px solid rgba(59, 130, 246, 0.15);
        margin-top: 1.25rem;
        backdrop-filter: blur(10px);
    }

    [data-testid="stExpander"] summary {
        font-weight: 600;
        font-size: 1rem;
        color: var(--text-primary) !important;
        padding: 1rem;
    }
    
    [data-testid="stExpander"] summary:hover {
        color: var(--primary-blue) !important;
    }

    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-purple), var(--accent-cyan));
        border-radius: 10px;
    }

    /* Divider */
    hr {
        border-color: rgba(59, 130, 246, 0.15) !important;
        margin: 1.5rem 0 !important;
    }

    /* Toast/Info Messages */
    .stAlert {
        background: rgba(20, 27, 45, 0.8) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }

    /* Label text */
    label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }

    /* Plotly Chart Container */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Glow effect for active elements */
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.3); }
        50% { box-shadow: 0 0 30px rgba(139, 92, 246, 0.4); }
    }
    
    .glow-effect {
        animation: glow 3s ease-in-out infinite;
    }
    </style>
    """

st.markdown(get_ultimate_css(st.session_state.theme), unsafe_allow_html=True)

# ======================= SIDEBAR - STORE VALUES IN SESSION STATE =======================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1.5rem 1rem;">
        <div style="font-size:2.5rem; margin-bottom:0.75rem;">⚙️</div>
        <h2 style="margin-bottom:0.5rem;">Control Panel</h2>
        <p style="font-size:0.8125rem; opacity:0.7; color: var(--text-secondary);">
            Configure monitoring & servers
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # -------- SERVER INPUT --------
    st.markdown("### 🌐 Server List")

    server_text = st.text_area(
        "One server per line (URL or IP:PORT)",
        value="\n".join(st.session_state.get("SERVERS", [])),
        height=140,
        help=(
            "Examples:\n"
            "https://www.wikipedia.org\n"
            "https://postman-echo.com\n"
            "http://127.0.0.1:8001"
        )
    )

    if st.button("Apply Servers", use_container_width=True):
        parsed = [s.strip() for s in server_text.splitlines() if s.strip()]

        if not parsed:
            st.warning("Please enter at least one server")
        else:
            st.session_state.SERVERS = parsed

            st.session_state.monitoring_data = {
                "plot_time": [],
                "plot_data": {
                    s: {
                        "rtt": [],
                        "load": [],
                        "health": [],
                        "errors": [],
                        "bandwidth": [],
                        "chosen": []
                    } for s in parsed
                },
                "rtt_history": {s: deque(maxlen=10) for s in parsed},
                "load_history": {s: deque(maxlen=10) for s in parsed},
                "health_history": {s: deque(maxlen=10) for s in parsed},
                "error_history": {s: deque(maxlen=10) for s in parsed},
                "bandwidth_history": {s: deque(maxlen=10) for s in parsed},
                "selection_count": {s: 0 for s in parsed},
            }

            st.session_state.current_round = 0
            st.session_state.prev_best = None
            st.session_state.monitoring_active = False

            st.success("✅ Server list updated")
            st.rerun()

    st.markdown("---")

    # -------- MONITORING SETTINGS --------
    st.markdown("### ⏱ Monitoring Settings")
    st.session_state.rounds = st.slider("Rounds", 5, 100, st.session_state.get("rounds", 20))
    st.session_state.interval = st.slider("Interval (seconds)", 0.5, 5.0, st.session_state.get("interval", 1.0), 0.5)

    st.markdown("---")

    # -------- SCORING WEIGHTS --------
    st.markdown("### ⚖️ Scoring Weights")
    with st.expander("Advanced"):
        st.session_state.alpha = st.number_input("RTT Weight (α)", 0.0, 10.0, st.session_state.get("alpha", 1.0), 0.1)
        st.session_state.beta = st.number_input("Load Weight (β)", 0.0, 10.0, st.session_state.get("beta", 0.5), 0.1)
        st.session_state.gamma = st.number_input("Health Weight (γ)", 0.0, 10.0, st.session_state.get("gamma", 0.3), 0.1)
        st.session_state.delta = st.number_input("Error Weight (δ)", 0.0, 10.0, st.session_state.get("delta", 0.2), 0.1)

    st.markdown("---")

    # -------- BANDIT SETTINGS --------
    st.markdown("### 🎲 Selection Strategy")
    st.session_state.eps = st.slider("Exploration ε", 0.0, 0.6, st.session_state.get("eps", 0.2), 0.05)
    st.session_state.anti_stick = st.slider("Anti-stickiness", 0.0, 0.2, st.session_state.get("anti_stick", 0.03), 0.01)

    st.markdown("---")

    if st.button("🔄 RESET SESSION", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k not in ("theme",):
                del st.session_state[k]
        st.success("Session reset")
        time.sleep(0.8)
        st.rerun()

# ======================= EXTRACT VALUES FROM SESSION STATE =======================
rounds = st.session_state.get("rounds", 20)
interval = st.session_state.get("interval", 1.0)
alpha = st.session_state.get("alpha", 1.0)
beta = st.session_state.get("beta", 0.5)
gamma = st.session_state.get("gamma", 0.3)
delta = st.session_state.get("delta", 0.2)
eps = st.session_state.get("eps", 0.2)
anti_stick = st.session_state.get("anti_stick", 0.03)

# ======================= SESSION STATE =======================
if "monitoring_data" not in st.session_state:
    st.session_state.monitoring_data = {
        "plot_time": [],
        "plot_data": {
            p: {
                "rtt": [],
                "load": [],
                "health": [],
                "errors": [],
                "bandwidth": [],
                "chosen": []
            } for p in st.session_state.SERVERS
        },
        "rtt_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "load_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "health_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "error_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "bandwidth_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "selection_count": {p: 0 for p in st.session_state.SERVERS},
        "session_start": None,
        "session_end": None
    }

if "monitoring_active" not in st.session_state:
    st.session_state.monitoring_active = False

if "current_round" not in st.session_state:
    st.session_state.current_round = 0

if "prev_best" not in st.session_state:
    st.session_state.prev_best = None

# ======================= HEADER =======================
st.markdown("""
<h1 style='text-align:center; margin-bottom:0.25rem;'>
    ⚡ Nexus Load Balancer Pro
</h1>
<p style='text-align:center; color: var(--text-secondary); font-size: 1rem; margin-bottom: 2.5rem;'>
    Intelligent server monitoring & selection powered by adaptive algorithms
</p>
""", unsafe_allow_html=True)

# ======================= MAIN CONTROLS =======================
btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])

with btn_col1:
    start_btn = st.button("▶️ START MONITORING", use_container_width=True)

with btn_col2:
    stop_btn = st.button("⏸️ STOP", use_container_width=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

info_container = st.container()
chart_container = st.container()

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

analytics_expander = st.expander("📊 Detailed Analytics", expanded=False)


# ======================= BUTTON HANDLERS =======================
if stop_btn:
    st.session_state.monitoring_active = False

if start_btn:
    st.session_state.monitoring_active = True
    st.session_state.current_round = 0
    st.session_state.prev_best = None

    st.session_state.monitoring_data = {
        "plot_time": [],
        "plot_data": {
            p: {
                "rtt": [],
                "load": [],
                "health": [],
                "errors": [],
                "bandwidth": [],
                "chosen": []
            } for p in st.session_state.SERVERS
        },
        "rtt_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "load_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "health_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "error_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "bandwidth_history": {p: deque(maxlen=10) for p in st.session_state.SERVERS},
        "selection_count": {p: 0 for p in st.session_state.SERVERS},
        "session_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_end": None
    }

# ======================= BANDIT SELECTION =======================
def bandit_select(score_map, prev_best, epsilon, anti_stick):
    adjusted = {}
    for s, v in score_map.items():
        penalty = anti_stick if prev_best and s == prev_best else 0.0
        adjusted[s] = v + penalty

    if random.random() < epsilon:
        scores = np.array(list(adjusted.values()), dtype=float)
        inv = 1.0 / np.clip(scores, 1e-6, None)
        prob = inv / inv.sum()
        return np.random.choice(list(adjusted.keys()), p=prob)

    return min(adjusted, key=lambda k: adjusted[k])

# ======================= MONITOR ONE ROUND =======================
def monitor_round(round_idx, alpha, beta, gamma, delta, epsilon, anti_stick):
    data = st.session_state.monitoring_data
    results = {}

    for server in st.session_state.SERVERS:
        results[server] = probe_server(server)

    for server, m in results.items():
        data["rtt_history"][server].append(m["rtt"])
        data["load_history"][server].append(m["load"])
        data["health_history"][server].append(m["health_score"])

        handled = m.get("total_handled")
        errors = m.get("total_errors")

        handled = handled if isinstance(handled, (int, float)) and handled > 0 else 1
        errors = errors if isinstance(errors, (int, float)) else 0

        err_rate = errors / handled
        data["error_history"][server].append(err_rate)
        data["bandwidth_history"][server].append(m["bandwidth_mbps"])

    scores = {}
    for server in st.session_state.SERVERS:
        rtt_vals = [v for v in data["rtt_history"][server] if v is not None]
        pred_rtt = np.mean(rtt_vals) if rtt_vals else 10.0

        scores[server] = compute_score(
            pred_rtt,
            np.mean(data["load_history"][server]),
            np.mean(data["health_history"][server]),
            np.mean(data["error_history"][server]),
            np.mean(data["bandwidth_history"][server]),
            alpha, beta, gamma, delta, epsilon
        )

    prev = st.session_state.prev_best
    best = bandit_select(scores, prev, epsilon, anti_stick)

    if prev and best != prev:
        st.info(f"🔁 Switched server: {prev} → {best}")

    st.session_state.prev_best = best
    data["selection_count"][best] += 1
    data["plot_time"].append(round_idx)

    for server in st.session_state.SERVERS:
        data["plot_data"][server]["rtt"].append(data["rtt_history"][server][-1])
        data["plot_data"][server]["load"].append(data["load_history"][server][-1])
        data["plot_data"][server]["health"].append(data["health_history"][server][-1])
        data["plot_data"][server]["errors"].append(data["error_history"][server][-1] * 100)
        data["plot_data"][server]["bandwidth"].append(data["bandwidth_history"][server][-1])
        data["plot_data"][server]["chosen"].append(1 if server == best else 0)

    return best

# ======================= METRIC CARDS =======================
def render_metrics():
    data = st.session_state.monitoring_data
    cols = st.columns(len(st.session_state.SERVERS))

    for i, server in enumerate(st.session_state.SERVERS):
        with cols[i]:
            online = len(data["rtt_history"][server]) > 0
            badge = "badge-online" if online else "badge-waiting"
            status = "ONLINE" if online else "WAITING"

            st.markdown(f"""
            <div class="custom-card">
                <div style="text-align:center">
                    <h3 style="word-break:break-all; margin-bottom:0.75rem;">{server}</h3>
                    <span class="status-badge {badge}">{status}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if online:
                raw_rtt = data["rtt_history"][server][-1]
                rtt = f"{raw_rtt * 1000:.1f} ms" if raw_rtt is not None else "N/A"
                load = data["load_history"][server][-1]
                health = data["health_history"][server][-1]
                raw_bw = data["bandwidth_history"][server][-1]
                bw = f"{raw_bw:.0f} Mbps" if raw_bw is not None else "N/A"
                raw_err = data["error_history"][server][-1]
                xerr = f"{raw_err * 100:.2f} %" if raw_err is not None else "N/A"
                st.metric("⚡ RTT", rtt)
                st.metric("💻 Load", f"{load:.0f} %")
                st.metric("💚 Health", f"{health:.0f}/100")
                st.metric("📡 Bandwidth", bw)
                st.metric("⚠️ Errors", xerr)
            else:
                st.info("Awaiting data...")

# ======================= LIVE MONITORING =======================
info_placeholder = st.empty()

if st.session_state.monitoring_active:
    progress = st.progress(st.session_state.current_round / rounds)

    for r in range(st.session_state.current_round, rounds):
        if not st.session_state.monitoring_active:
            st.warning("Monitoring stopped")
            break

        try:
            best = monitor_round(r, alpha, beta, gamma, delta, eps, anti_stick)

            prev = st.session_state.prev_best
            if prev is not None and prev != best:
                st.toast(f"🔁 Switched to {best}", icon="🔄")

            st.session_state.prev_best = best
            st.session_state.current_round = r + 1

            info_placeholder.markdown(f"""
            <div class="custom-card glow-effect" style="text-align:center">
                <h2 style="margin-bottom:0.75rem;">🔄 Monitoring in Progress</h2>
                <p style="color: var(--text-secondary); margin-bottom:1rem;">
                    Round {st.session_state.current_round} of {rounds}
                </p>
                <div style="margin-top:1.5rem; padding:1.25rem; background: rgba(59, 130, 246, 0.1); border-radius:12px; border: 1px solid rgba(59, 130, 246, 0.2);">
                    <p style="font-size:0.875rem; color: var(--text-secondary); margin-bottom:0.5rem; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">
                        ⭐ Active Server
                    </p>
                    <p style="word-break:break-all; color:#3b82f6; font-size:1.125rem; font-weight:600; font-family: 'JetBrains Mono', monospace;">
                        {best}
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            progress.progress(st.session_state.current_round / rounds)

            with analytics_expander:
                render_metrics()

            if r < rounds - 1:
                time.sleep(interval)

        except Exception as e:
            st.error(f"Monitoring error: {e}")
            break

    info_placeholder.empty()

    if st.session_state.current_round >= rounds:
        st.session_state.monitoring_active = False
        st.session_state.monitoring_data["session_end"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        st.balloons()

        counts = st.session_state.monitoring_data["selection_count"]
        best_overall = max(counts, key=lambda k: counts[k])

        st.markdown(f"""
        <div class="custom-card" style="text-align:center">
            <h2 style="margin-bottom:1rem;">🏆 Monitoring Complete</h2>
            <div style="padding:1.5rem; background: rgba(16, 185, 129, 0.1); border-radius:12px; border: 1px solid rgba(16, 185, 129, 0.2);">
                <p style="font-size:0.875rem; color: var(--text-secondary); margin-bottom:0.75rem; font-weight:600;">
                    OPTIMAL SERVER
                </p>
                <p style="word-break:break-all; font-size:1.25rem; font-weight:600; color:#10b981; margin-bottom:0.5rem; font-family: 'JetBrains Mono', monospace;">
                    {best_overall}
                </p>
                <p style="color: var(--text-secondary); font-size:0.875rem;">
                    Selected {counts[best_overall]} times out of {rounds} rounds
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    with info_container:
        st.markdown("""
        <div class="custom-card" style="text-align:center; padding:2.5rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">👋</div>
            <h2 style="margin-bottom:0.75rem;">Welcome to Nexus Load Balancer</h2>
            <p style="color: var(--text-secondary); font-size:1rem;">
                Configure your servers in the sidebar and click <strong>START MONITORING</strong> to begin
            </p>
        </div>
        """, unsafe_allow_html=True)

# ======================= PLOTLY DASHBOARD =======================
def render_charts(best_server=None):
    data = st.session_state.monitoring_data
    if not data["plot_time"]:
        return

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            "⚡ RTT (ms)",
            "💻 Load (%)",
            "💚 Health Score",
            "⚠️ Error Rate (%)",
            "📡 Bandwidth (Mbps)",
            "🎯 Selection History"
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )

    colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#06b6d4"]

    for idx, server in enumerate(st.session_state.SERVERS):
        color = colors[idx % len(colors)]
        width = 3 if server == best_server else 2
        opacity = 1.0 if server == best_server else 0.6

        t = data["plot_time"]

        fig.add_trace(
            go.Scatter(
                x=t,
                y=[(v * 1000) if v is not None else None for v in data["plot_data"][server]["rtt"]],
                name=server,
                line=dict(color=color, width=width),
                opacity=opacity,
                mode='lines+markers',
                marker=dict(size=4)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=data["plot_data"][server]["load"],
                showlegend=False,
                line=dict(color=color, width=width),
                opacity=opacity,
                mode='lines+markers',
                marker=dict(size=4)
            ),
            row=1, col=2
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=data["plot_data"][server]["health"],
                showlegend=False,
                line=dict(color=color, width=width),
                opacity=opacity,
                mode='lines+markers',
                marker=dict(size=4)
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=data["plot_data"][server]["errors"],
                showlegend=False,
                line=dict(color=color, width=width),
                opacity=opacity,
                mode='lines+markers',
                marker=dict(size=4)
            ),
            row=2, col=2
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=data["plot_data"][server]["bandwidth"],
                showlegend=False,
                line=dict(color=color, width=width),
                opacity=opacity,
                mode='lines+markers',
                marker=dict(size=4)
            ),
            row=3, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=np.cumsum(data["plot_data"][server]["chosen"]),
                showlegend=False,
                fill="tozeroy",
                line=dict(color=color, width=width),
                opacity=opacity,
                mode='lines'
            ),
            row=3, col=2
        )

    fig.update_layout(
        height=900,
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(t=100, l=60, r=60, b=60),
        font=dict(size=11, family='Space Grotesk, sans-serif'),
        paper_bgcolor='rgba(10,15,30,0.8)',
        plot_bgcolor='rgba(20,27,45,0.4)',
        legend=dict(
            font=dict(size=10),
            bgcolor='rgba(20,27,45,0.8)',
            bordercolor='rgba(59,130,246,0.3)',
            borderwidth=1
        )
    )

    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=13, weight='bold', family='Space Grotesk')
        annotation['yshift'] = 5

    fig.update_xaxes(
        gridcolor='rgba(59,130,246,0.1)',
        zerolinecolor='rgba(59,130,246,0.2)'
    )
    fig.update_yaxes(
        gridcolor='rgba(59,130,246,0.1)',
        zerolinecolor='rgba(59,130,246,0.2)'
    )

    st.plotly_chart(fig, use_container_width=True)

# ======================= CHART RENDER =======================
with chart_container:
    if st.session_state.monitoring_data["plot_time"]:
        counts = st.session_state.monitoring_data["selection_count"]
        best = max(counts, key=lambda k: counts[k]) if counts else None
        render_charts(best)
