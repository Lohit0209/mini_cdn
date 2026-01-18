# app.py — Nexus Load Balancer (FULLY FIXED)

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

# ======================= THEME STATE =======================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

# ======================= FULL THEME CSS =======================
def get_ultimate_css(theme):
    if theme == "dark":
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');

        * { font-family: 'Poppins', sans-serif !important; }

        .stApp {
            background: linear-gradient(-45deg, #0a0e27, #1a1f3a, #2d1b4e, #1e2a4a);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
            color: #ffffff;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900 !important;
            letter-spacing: 2px;
            font-size: 56px !important;
            text-align: center;
        }

        h2 { color: #ffffff !important; font-weight: 700 !important; }
        h3 { color: #e8eaf6 !important; font-weight: 600 !important; }

        .custom-card {
            background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15));
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 28px;
            border: 2px solid rgba(102,126,234,0.3);
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            margin-bottom: 20px;
        }

        .stButton > button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 16px;
            padding: 14px 36px;
            font-weight: 700;
            letter-spacing: 1.5px;
            border: none;
        }

        .status-badge {
            display: inline-block;
            padding: 6px 18px;
            border-radius: 25px;
            font-weight: 700;
            font-size: 12px;
        }

        .badge-online {
            background: linear-gradient(135deg, #10b981, #3b82f6);
            color: white;
        }

        .badge-waiting {
            background: linear-gradient(135deg, #f59e0b, #ef4444);
            color: white;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(26,31,58,0.95), rgba(10,14,39,0.95));
            border-right: 2px solid rgba(102,126,234,0.3);
        }

        ::-webkit-scrollbar {
            width: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #667eea, #764ba2);
            border-radius: 10px;
        }
        </style>
        """
    else:
        return """
        <style>
        * { font-family: 'Poppins', sans-serif !important; }

        .stApp {
            background: linear-gradient(135deg, #f8fafc, #e0e7ff, #fce7f3);
            color: #1e293b;
        }

        h1 {
            background: linear-gradient(135deg, #4f46e5, #7c3aed, #db2777);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900 !important;
            font-size: 56px !important;
        }

        .custom-card {
            background: white;
            border-radius: 20px;
            padding: 28px;
            border: 2px solid rgba(79,70,229,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }

        .stButton > button {
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
            border-radius: 16px;
            padding: 14px 36px;
            font-weight: 700;
            border: none;
        }
        </style>
        """

st.markdown(get_ultimate_css(st.session_state.theme), unsafe_allow_html=True)

# ======================= SIDEBAR - STORE VALUES IN SESSION STATE =======================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:20px;">
        <div style="font-size:42px;">⚙️</div>
        <h2>Control Panel</h2>
        <p style="font-size:13px; opacity:0.7;">
            Configure monitoring & servers
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # -------- THEME TOGGLE --------
    theme_icon = "🌙" if st.session_state.theme == "dark" else "☀️"
    if st.button(f"{theme_icon} Toggle Theme", use_container_width=True):
        toggle_theme()
        st.rerun()

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

# ======================= MAIN CONTROLS =======================
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])

with btn_col1:
    start_btn = st.button("▶️ START MONITORING", use_container_width=True)

with btn_col2:
    stop_btn = st.button("⏸️ STOP", use_container_width=True)

info_container = st.container()
chart_container = st.container()
analytics_expander = st.expander("Detailed Analytics", expanded=False)


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
                    <h3 style="word-break:break-all">{server}</h3>
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
            <div class="custom-card" style="text-align:center">
                <h2>🔄 Monitoring in Progress</h2>
                <p>Round {st.session_state.current_round} of {rounds}</p>
                <p style="margin-top:12px; font-size:18px;">
                    ⭐ <b>Active Server</b><br>
                    <span style="word-break:break-all; color:#22c55e">
                        {best}
                    </span>
                </p>
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
            <h2>🏆 Monitoring Complete</h2>
            <p><strong>Best Server:</strong></p>
            <p style="word-break:break-all">{best_overall}</p>
            <p>Selected {counts[best_overall]} times</p>
        </div>
        """, unsafe_allow_html=True)

else:
    with info_container:
        st.markdown("""
        <div class="custom-card" style="text-align:center">
            <h2>👋 Welcome to Nexus Load Balancer</h2>
            <p>Paste servers in the sidebar and click START MONITORING</p>
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
        ]
    )

    colors = ["#6366f1", "#ec4899", "#22c55e", "#f97316", "#0ea5e9"]

    for idx, server in enumerate(st.session_state.SERVERS):
        color = colors[idx % len(colors)]
        width = 4 if server == best_server else 2
        opacity = 1.0 if server == best_server else 0.6

        t = data["plot_time"]

        fig.add_trace(
            go.Scatter(
                x=t,
                y=[(v * 1000) if v is not None else None for v in data["plot_data"][server]["rtt"]],
                name=server,
                line=dict(color=color, width=width),
                opacity=opacity
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=data["plot_data"][server]["load"],
                showlegend=False,
                line=dict(color=color, width=width),
                opacity=opacity
            ),
            row=1, col=2
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=data["plot_data"][server]["health"],
                showlegend=False,
                line=dict(color=color, width=width),
                opacity=opacity
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=data["plot_data"][server]["errors"],
                showlegend=False,
                line=dict(color=color, width=width),
                opacity=opacity
            ),
            row=2, col=2
        )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=data["plot_data"][server]["bandwidth"],
                showlegend=False,
                line=dict(color=color, width=width),
                opacity=opacity
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
                opacity=opacity
            ),
            row=3, col=2
        )

    fig.update_layout(
        height=900,
        template="plotly_dark" if st.session_state.theme == "dark" else "plotly_white",
        hovermode="x unified",
        margin=dict(t=80, l=60, r=60, b=60)
    )

    st.plotly_chart(fig, use_container_width=True)

# ======================= CHART RENDER =======================
with chart_container:
    if st.session_state.monitoring_data["plot_time"]:
        counts = st.session_state.monitoring_data["selection_count"]
        best = max(counts, key=lambda k: counts[k]) if counts else None
        render_charts(best)
