import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Clinical Note Intelligence — Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #070D1A;
    color: #E2E8F0;
}

.stApp {
    background: #070D1A;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 2rem 2.5rem; max-width: 1400px; }

/* Header */
.dash-header {
    border-bottom: 1px solid #1E3A5F;
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
}

.dash-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #F1F5F9;
    letter-spacing: -0.02em;
    margin: 0;
}

.dash-subtitle {
    font-size: 0.85rem;
    color: #64748B;
    margin-top: 0.25rem;
    font-weight: 400;
}

.dash-badge {
    display: inline-block;
    background: #0F2744;
    border: 1px solid #1E3A5F;
    color: #38BDF8;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-left: 0.75rem;
    vertical-align: middle;
}

/* Metric cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
}

.metric-card {
    background: #0D1B2E;
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 12px 12px 0 0;
}

.metric-card.cyan::before  { background: linear-gradient(90deg, #06B6D4, #0EA5E9); }
.metric-card.green::before { background: linear-gradient(90deg, #10B981, #34D399); }
.metric-card.amber::before { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
.metric-card.red::before   { background: linear-gradient(90deg, #EF4444, #F87171); }

.metric-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B;
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: 2.25rem;
    font-weight: 700;
    line-height: 1;
    color: #F1F5F9;
    font-variant-numeric: tabular-nums;
}

.metric-value.cyan  { color: #38BDF8; }
.metric-value.green { color: #34D399; }
.metric-value.amber { color: #FBBF24; }
.metric-value.red   { color: #F87171; }

.metric-sub {
    font-size: 0.75rem;
    color: #475569;
    margin-top: 0.4rem;
}

/* Section headers */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #38BDF8;
    margin-bottom: 0.5rem;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #E2E8F0;
    margin-bottom: 1.25rem;
}

/* Chart containers */
.chart-card {
    background: #0D1B2E;
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* Table */
.submissions-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
}

.submissions-table th {
    text-align: left;
    padding: 0.6rem 1rem;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B;
    border-bottom: 1px solid #1E3A5F;
}

.submissions-table td {
    padding: 0.75rem 1rem;
    color: #CBD5E1;
    border-bottom: 1px solid #0F2040;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
}

.submissions-table tr:hover td {
    background: #0F2040;
}

.badge-review {
    display: inline-block;
    background: #451A03;
    color: #FBBF24;
    border: 1px solid #92400E;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: 600;
}

.badge-ok {
    display: inline-block;
    background: #052E16;
    color: #34D399;
    border: 1px solid #065F46;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: 600;
}

.conf-high { color: #34D399; }
.conf-mid  { color: #FBBF24; }
.conf-low  { color: #F87171; }

/* Divider */
.dash-divider {
    border: none;
    border-top: 1px solid #1E3A5F;
    margin: 2rem 0;
}

/* Status dot */
.status-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    background: #10B981;
    border-radius: 50%;
    margin-right: 6px;
    box-shadow: 0 0 6px #10B981;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
</style>
""", unsafe_allow_html=True)


# ── Fetch data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_analytics():
    try:
        response = requests.get(f"{API_URL}/analytics", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

data = fetch_analytics()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <div>
        <span class="dash-title">Clinical Note Intelligence</span>
        <span class="dash-badge">Live</span>
    </div>
    <div class="dash-subtitle">
        <span class="status-dot"></span>
        AI extraction system · Performance analytics
    </div>
</div>
""", unsafe_allow_html=True)

if not data:
    st.markdown("""
    <div style="background:#1A0A0A; border:1px solid #7F1D1D; border-radius:10px; 
                padding:1.5rem; color:#FCA5A5; font-size:0.9rem;">
        ⚠️ Cannot reach the API at <code>localhost:8000</code>. 
        Make sure <code>docker-compose up</code> is running.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Metrics ─────────────────────────────────────────────────────────────────────
total = data["total_notes"]
avg_conf = data["avg_confidence"]
needs_review = data["notes_needing_review"]
review_rate = (needs_review / total * 100) if total > 0 else 0
passed = total - needs_review

conf_color = "green" if avg_conf >= 0.8 else "amber" if avg_conf >= 0.6 else "red"
rate_color = "green" if review_rate < 30 else "amber" if review_rate < 60 else "red"

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card cyan">
        <div class="metric-label">Total Notes Processed</div>
        <div class="metric-value cyan">{total}</div>
        <div class="metric-sub">All time submissions</div>
    </div>
    <div class="metric-card {conf_color}">
        <div class="metric-label">Avg Confidence Score</div>
        <div class="metric-value {conf_color}">{avg_conf:.0%}</div>
        <div class="metric-sub">Across all extractions</div>
    </div>
    <div class="metric-card amber">
        <div class="metric-label">Flagged for Review</div>
        <div class="metric-value amber">{needs_review}</div>
        <div class="metric-sub">{passed} passed automatically</div>
    </div>
    <div class="metric-card {rate_color}">
        <div class="metric-label">Review Rate</div>
        <div class="metric-value {rate_color}">{review_rate:.0f}%</div>
        <div class="metric-sub">Target: below 30%</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Charts row ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 2], gap="medium")

with col1:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Confidence Score Over Time</div>', unsafe_allow_html=True)

    if data["confidence_over_time"] and len(data["confidence_over_time"]) > 0:
        df_time = pd.DataFrame(data["confidence_over_time"])
        df_time["date"] = pd.to_datetime(df_time["date"])
        df_time = df_time.sort_values("date")

        fig_line = go.Figure()

        # Threshold line
        fig_line.add_hline(
            y=0.7,
            line_dash="dash",
            line_color="#475569",
            line_width=1,
            annotation_text="Review threshold (70%)",
            annotation_font_color="#64748B",
            annotation_font_size=11
        )

        # Confidence line
        fig_line.add_trace(go.Scatter(
            x=df_time["date"],
            y=df_time["avg_confidence"],
            mode="lines+markers",
            line=dict(color="#38BDF8", width=2.5, shape="spline"),
            marker=dict(size=8, color="#38BDF8", 
                       line=dict(color="#070D1A", width=2)),
            fill="tozeroy",
            fillcolor="rgba(56,189,248,0.08)",
            name="Avg Confidence",
            hovertemplate="<b>%{x|%b %d}</b><br>Confidence: %{y:.0%}<extra></extra>"
        ))

        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#94A3B8", size=12),
            margin=dict(l=0, r=0, t=10, b=0),
            height=240,
            xaxis=dict(
                showgrid=False,
                showline=False,
                tickfont=dict(size=11, color="#64748B"),
                tickformat="%b %d"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#1E3A5F",
                gridwidth=0.5,
                showline=False,
                tickformat=".0%",
                range=[0, 1.05],
                tickfont=dict(size=11, color="#64748B")
            ),
            showlegend=False,
            hovermode="x unified"
        )

        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown("""
        <div style="height:200px; display:flex; align-items:center; justify-content:center;
                    color:#475569; font-size:0.85rem;">
            Submit more notes to see the confidence trend
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Error Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Most Flagged Fields</div>', unsafe_allow_html=True)

    if data["flagged_fields"]:
        fields = {k.replace("_", " ").title(): v 
                  for k, v in data["flagged_fields"].items()}
        df_flags = pd.DataFrame(
            list(fields.items()),
            columns=["Field", "Count"]
        ).sort_values("Count", ascending=True)

        # Color bars by count
        max_count = df_flags["Count"].max()
        colors = ["#F87171" if c == max_count 
                  else "#FBBF24" if c >= max_count * 0.6 
                  else "#38BDF8" 
                  for c in df_flags["Count"]]

        fig_bar = go.Figure(go.Bar(
            x=df_flags["Count"],
            y=df_flags["Field"],
            orientation="h",
            marker=dict(
                color=colors,
                cornerradius=4
            ),
            hovertemplate="<b>%{y}</b><br>Flagged %{x} time(s)<extra></extra>"
        ))

        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#94A3B8", size=12),
            margin=dict(l=0, r=20, t=10, b=0),
            height=240,
            xaxis=dict(
                showgrid=True,
                gridcolor="#1E3A5F",
                gridwidth=0.5,
                showline=False,
                tickfont=dict(size=11, color="#64748B"),
                dtick=1
            ),
            yaxis=dict(
                showgrid=False,
                showline=False,
                tickfont=dict(size=12, color="#CBD5E1")
            ),
            showlegend=False
        )

        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown("""
        <div style="height:200px; display:flex; align-items:center; justify-content:center;
                    color:#475569; font-size:0.85rem;">
            No flagged fields yet
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Recent submissions ──────────────────────────────────────────────────────────
st.markdown('<hr class="dash-divider">', unsafe_allow_html=True)
st.markdown('<div class="section-label">History</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Recent Submissions</div>', unsafe_allow_html=True)

if data["recent_notes"]:
    table_rows = ""
    for note in data["recent_notes"]:
        conf = note["overall_confidence"]
        conf_pct = f"{conf:.0%}"
        conf_class = "conf-high" if conf >= 0.8 else "conf-mid" if conf >= 0.6 else "conf-low"
        review_badge = (
            '<span class="badge-review">⚠ Review</span>'
            if note["needs_human_review"]
            else '<span class="badge-ok">✓ Passed</span>'
        )
        try:
            dt = datetime.fromisoformat(note["created_at"])
            formatted_dt = dt.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_dt = note["created_at"]

        table_rows += (
            f"<tr>"
            f"<td>{note['note_id']}</td>"
            f'<td class="{conf_class}">{conf_pct}</td>'
            f"<td>{review_badge}</td>"
            f'<td style="color:#475569">{formatted_dt}</td>'
            f"</tr>"
        )

    table_html = (
        '<div class="chart-card">'
        '<table class="submissions-table">'
        "<thead><tr>"
        "<th>Note ID</th>"
        "<th>Confidence</th>"
        "<th>Status</th>"
        "<th>Submitted At</th>"
        "</tr></thead>"
        f"<tbody>{table_rows}</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="chart-card" style="text-align:center; padding:3rem; color:#475569;">
        No submissions yet — process a note to see it here
    </div>
    """, unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem; padding-top:1rem; border-top:1px solid #1E3A5F;
            color:#334155; font-size:0.72rem; text-align:center;">
    Clinical Note Intelligence System · Analytics Dashboard · 
    Data refreshes every 30 seconds
</div>
""", unsafe_allow_html=True)
