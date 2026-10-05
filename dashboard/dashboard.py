"""
Government-facing analytics dashboard — the 'Analytics & Dashboards
(Performance Analytics)' block from the architecture diagram.
Run alongside the FastAPI service:
    streamlit run dashboard/dashboard.py
"""
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Nagrik Setu — Command Dashboard", layout="wide", page_icon="📊")

# ---------------------------------------------------------------- BRAND CSS
NAVY = "#12233F"
NAVY_SOFT = "#1D3660"
MARIGOLD = "#E8871E"
MARIGOLD_SOFT = "#FCEBD5"
GREEN = "#1F8A5F"
GREEN_SOFT = "#E4F3EC"
RED = "#C23B3B"
RED_SOFT = "#FBE7E7"
AMBER = "#B9781A"
PAPER = "#F7F8FA"
INK = "#1B2430"
INK_SOFT = "#5B6675"
BORDER = "#DDE3EA"

PRIORITY_COLORS = {"Critical": RED, "High": AMBER, "Medium": MARIGOLD, "Low": GREEN}
SENTIMENT_COLORS = {"negative": RED, "neutral": "#8A93A3", "positive": GREEN}

# IMPORTANT: Streamlit's markdown parser can break a long <style> block if it
# contains blank lines OR comment-only lines, silently leaking raw CSS text
# onto the page above the real content. Building the CSS as one string then
# stripping blank/comment lines before rendering guarantees this can't happen,
# no matter how the CSS itself is authored below.
_RAW_CSS = f"""
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@600&display=swap" rel="stylesheet">
<style>
.stApp {{ background: {PAPER} !important; }}
html, body, [class*="css"], .stApp, .stApp p, .stApp span, .stApp label {{ font-family: 'IBM Plex Sans', sans-serif; color: {INK} !important; }}
.block-container {{ padding-top: 1.6rem; max-width: 1300px; }}
#MainMenu, footer, header {{visibility: hidden;}}
.dash-header {{ background: {NAVY}; color: #fff; padding: 20px 28px; border-radius: 14px; margin-bottom: 26px; display: flex; justify-content: space-between; align-items: center; }}
.dash-brand {{ display: flex; align-items: center; gap: 14px; }}
.dash-mark {{ width: 42px; height: 42px; border-radius: 10px; background: {MARIGOLD}; display: flex; align-items: center; justify-content: center; font-family: 'Fraunces', serif; font-weight: 700; font-size: 21px; color: {NAVY}; flex-shrink: 0; }}
.dash-title {{ font-family: 'Fraunces', serif; font-weight: 700; font-size: 24px; margin: 0; color: #fff !important; line-height: 1.2; }}
.dash-sub {{ color: #B9C4D6 !important; font-size: 13.5px; margin-top: 3px; }}
.dash-pill {{ background: {MARIGOLD}; color: {NAVY} !important; font-weight: 700; font-size: 12.5px; padding: 6px 14px; border-radius: 20px; white-space: nowrap; }}
.streamlit-expanderHeader, div[data-testid="stExpander"] summary {{ background: {NAVY} !important; color: #fff !important; border-radius: 10px !important; font-weight: 600; font-size: 14px; }}
div[data-testid="stExpander"] summary p {{ color: #fff !important; }}
div[data-testid="stExpander"] {{ border: 1px solid {BORDER} !important; border-radius: 10px !important; margin-bottom: 22px; background: #fff !important; }}
div[data-baseweb="select"] > div {{ background: #fff !important; border: 1.5px solid {BORDER} !important; color: {INK} !important; border-radius: 9px !important; }}
div[data-baseweb="select"] span {{ color: {INK} !important; }}
ul[role="listbox"] {{ background: #fff !important; }}
li[role="option"] {{ color: {INK} !important; }}
.kpi-card {{ background: #fff; border: 1px solid {BORDER}; border-top: 3px solid {NAVY}; border-radius: 12px; padding: 18px 20px; height: 100%; transition: box-shadow .15s ease, transform .15s ease; }}
.kpi-card:hover {{ box-shadow: 0 6px 18px rgba(18,35,63,0.08); transform: translateY(-1px); }}
.kpi-label {{ font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: {INK_SOFT} !important; margin-bottom: 8px; }}
.kpi-value {{ font-family: 'Fraunces', serif; font-weight: 700; font-size: 32px; color: {NAVY} !important; line-height: 1; }}
.kpi-value.alert {{ color: {RED} !important; }}
.kpi-value.good {{ color: {GREEN} !important; }}
.kpi-card.alert {{ border-top-color: {RED}; }}
.kpi-card.good {{ border-top-color: {GREEN}; }}
.section-title {{ font-family: 'Fraunces', serif; font-weight: 600; font-size: 18px; color: {NAVY} !important; margin: 6px 0 14px; padding-left: 12px; border-left: 3px solid {MARIGOLD}; }}
.chart-card {{ background: #fff; border: 1px solid {BORDER}; border-radius: 12px; padding: 18px 20px 6px; margin-bottom: 20px; transition: box-shadow .15s ease; }}
.chart-card:hover {{ box-shadow: 0 6px 18px rgba(18,35,63,0.06); }}
div[data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 10px; overflow: hidden; }}
div[data-testid="stDataFrame"] * {{ color: {INK} !important; }}
div[data-testid="stDataFrame"] thead tr th {{ background: {NAVY} !important; color: #fff !important; font-weight: 600 !important; }}
div[data-testid="stDataFrame"] thead tr th * {{ color: #fff !important; }}
.stCaption, [data-testid="stCaptionContainer"] p {{ color: {INK_SOFT} !important; }}
.stButton button {{ background: {MARIGOLD}; color: {NAVY} !important; font-weight: 700; border: none; border-radius: 8px; }}
.stButton button p {{ color: {NAVY} !important; }}
.stButton button:hover {{ background: #d67a12; color: {NAVY} !important; }}
div[data-testid="stAlert"] p {{ color: {INK} !important; }}
.grievance-preview {{ background: {PAPER}; border: 1px solid {BORDER}; border-left: 4px solid {MARIGOLD}; border-radius: 8px; padding: 14px 18px; margin-top: 10px; font-size: 14px; line-height: 1.55; color: {INK} !important; }}
.grievance-preview .k {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: {INK_SOFT} !important; margin-bottom: 6px; }}
.filter-note {{ font-size: 12.5px; color: {INK_SOFT} !important; margin-bottom: 14px; }}
</style>
"""
_clean_lines = [
    line for line in _RAW_CSS.split("\n")
    if line.strip() != "" and not line.strip().startswith("/*")
]
st.markdown("\n".join(_clean_lines), unsafe_allow_html=True)

# ---------------------------------------------------------------- DATA LOAD
try:
    cases = requests.get(f"{API_URL}/cases", timeout=5).json()
except requests.exceptions.ConnectionError:
    st.error("Can't reach the API. Run `uvicorn app.main:app --reload` first, then refresh this page.")
    st.stop()

st.markdown(f"""<div class="dash-header">
<div class="dash-brand">
<div class="dash-mark">न</div>
<div><div class="dash-title">Nagrik Setu — Command Dashboard</div><div class="dash-sub">Live grievance intake, triage &amp; department performance</div></div>
</div>
<div class="dash-pill">Government view</div>
</div>""", unsafe_allow_html=True)

if not cases:
    st.info("No grievances submitted yet. File one through the citizen portal or POST to /grievance.")
    st.stop()

df = pd.DataFrame(cases)
df["created_at"] = pd.to_datetime(df["created_at"])
df["date"] = df["created_at"].dt.date
df["language"] = df["language"].fillna("en").map({"hi": "Hindi", "en": "English"}).fillna("English")

# Kept separate from the filtered `df` used everywhere below, so the critical
# alert always checks EVERY open critical case regardless of active filters.
all_df = df.copy()

# ---------------------------------------------------------------- SESSION STATE
if "acknowledged_critical" not in st.session_state:
    st.session_state.acknowledged_critical = set()
if "assign_case_override" not in st.session_state:
    st.session_state.assign_case_override = None
if "scroll_to_assign" not in st.session_state:
    st.session_state.scroll_to_assign = False

# ---------------------------------------------------------------- CRITICAL CASE ALERT (popup)
# Fires the moment the dashboard opens if there's an unacknowledged, unresolved
# Critical case. "Acknowledge & Assign" closes the dialog, pre-selects that
# case in the "Look Up & Update a Case" section below, suggests "Assigned" as
# the next status, and smooth-scrolls the page straight to that section.
@st.dialog("🚨 Critical Grievance Alert", width="large")
def _show_critical_alert(case_row):
    st.markdown(f"""
    <style>
    @keyframes criticalPulse {{
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(194,59,59,0.35); }}
        50% {{ box-shadow: 0 0 0 12px rgba(194,59,59,0); }}
    }}
    .critical-alert-box {{
        border: 2px solid {RED}; background: {RED_SOFT}; border-radius: 12px;
        padding: 22px 24px; animation: criticalPulse 1.8s infinite; margin-bottom: 18px;
    }}
    .critical-alert-top {{ display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }}
    .critical-alert-badge {{
        display: inline-flex; align-items: center; gap: 6px; background: {RED}; color: #fff;
        font-weight: 700; font-size: 12px; letter-spacing: 0.5px; text-transform: uppercase;
        padding: 6px 13px; border-radius: 20px;
    }}
    .critical-alert-case {{ font-family: 'IBM Plex Mono', monospace; font-weight: 700; font-size: 17px; color: {NAVY} !important; }}
    .critical-alert-meta {{ font-size: 13px; color: {INK_SOFT} !important; margin-top: 3px; }}
    .critical-alert-text {{
        margin-top: 16px; padding-top: 16px; border-top: 1px solid #F0BFBF;
        font-size: 15px; color: {INK} !important; line-height: 1.6;
    }}
    </style>
    <div class="critical-alert-box">
      <div class="critical-alert-top">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{RED}" stroke-width="2.2">
          <path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="critical-alert-badge">Immediate attention required</span>
      </div>
      <div class="critical-alert-case">{case_row['case_number']}</div>
      <div class="critical-alert-meta">{case_row['department']} &middot; Filed {case_row['created_at'].strftime('%d %b %Y, %H:%M')} &middot; Sentiment: {case_row['sentiment']}</div>
      <div class="critical-alert-text">{case_row['raw_text']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("This grievance has been marked **Critical priority**. Acknowledging will immediately mark it **Assigned** and take you to the assignment section.")

    if st.button("Acknowledge & Assign This Case", use_container_width=True, type="primary"):
        try:
            r = requests.patch(
                f"{API_URL}/cases/{int(case_row['id'])}/status",
                params={"status": "Assigned"}, timeout=5,
            )
            if not r.ok:
                st.error("Could not update this case's status. Please try again.")
                st.stop()
        except requests.exceptions.ConnectionError:
            st.error("Can't reach the API. Please try again.")
            st.stop()

        st.session_state.acknowledged_critical.add(case_row["case_number"])
        st.session_state.assign_case_override = case_row["case_number"]
        st.session_state.scroll_to_assign = True
        st.rerun()


# Only fires for cases still in "New" status — the moment a case is actually
# marked Assigned (via the button above), this becomes durable in the
# DATABASE, not just in-session memory. That's what stops the popup from
# reappearing after a full browser refresh (which wipes session_state but
# NOT the database), unlike relying on acknowledged_critical alone.
_open_critical = all_df[(all_df["priority"] == "Critical") & (all_df["status"] == "New")]
_unacked_critical = _open_critical[~_open_critical["case_number"].isin(st.session_state.acknowledged_critical)]
if not _unacked_critical.empty:
    _alert_row = _unacked_critical.sort_values("created_at", ascending=False).iloc[0]
    _show_critical_alert(_alert_row)

# ---------------------------------------------------------------- FILTERS
with st.expander("Filter cases", expanded=False):
    f1, f2, f3, f4 = st.columns([1.3, 1, 1, 1])
    min_d, max_d = df["date"].min(), df["date"].max()
    with f1:
        date_range = st.date_input("Filed between", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    with f2:
        dept_filter = st.multiselect("Department", sorted(df["department"].unique()))
    with f3:
        priority_filter = st.multiselect("Priority", ["Critical", "High", "Medium", "Low"])
    with f4:
        status_filter = st.multiselect("Status", ["New", "Assigned", "In Progress", "Resolved"])

fdf = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
    fdf = fdf[(fdf["date"] >= start_d) & (fdf["date"] <= end_d)]
if dept_filter:
    fdf = fdf[fdf["department"].isin(dept_filter)]
if priority_filter:
    fdf = fdf[fdf["priority"].isin(priority_filter)]
if status_filter:
    fdf = fdf[fdf["status"].isin(status_filter)]

if len(fdf) != len(df):
    st.markdown(f'<div class="filter-note">Showing {len(fdf)} of {len(df)} total cases based on your filters.</div>', unsafe_allow_html=True)

df = fdf
if df.empty:
    st.warning("No cases match the current filters.")
    st.stop()

# ---------------------------------------------------------------- KPI ROW
total = len(df)
resolved = int((df["status"] == "Resolved").sum())
critical_open = int(((df["priority"] == "Critical") & (df["status"] != "Resolved")).sum())
negative_pct = round(100 * df["sentiment"].str.lower().eq("negative").mean(), 1) if total else 0
resolution_rate = round(100 * resolved / total, 1) if total else 0

k1, k2, k3, k4, k5 = st.columns(5)
kpis = [
    (k1, "Total Grievances", f"{total}", ""),
    (k2, "Open Critical Cases", f"{critical_open}", "alert" if critical_open else ""),
    (k3, "Resolution Rate", f"{resolution_rate}%", "good" if resolution_rate >= 50 else ""),
    (k4, "Negative Sentiment", f"{negative_pct}%", "alert" if negative_pct > 60 else ""),
    (k5, "Languages Served", f"{df['language'].nunique()}", ""),
]
for col, label, value, cls in kpis:
    col.markdown(f'<div class="kpi-card {cls}"><div class="kpi-label">{label}</div><div class="kpi-value {cls}">{value}</div></div>', unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------------- CHART ROW 1
c1, c2 = st.columns([1.2, 1])

with c1:
    st.markdown('<div class="section-title">Grievances by Department</div>', unsafe_allow_html=True)
    dept_counts = df["department"].value_counts().reset_index()
    dept_counts.columns = ["department", "count"]
    dept_counts = dept_counts.sort_values("count")
    fig = px.bar(dept_counts, x="count", y="department", orientation="h", text="count")
    fig.update_traces(marker_color=NAVY, textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=320, margin=dict(l=0, r=20, t=6, b=6),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor=BORDER, title="", color=INK),
        yaxis=dict(title="", color=INK),
        font=dict(family="IBM Plex Sans", color=INK, size=13),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    st.markdown('<div class="section-title">Priority Breakdown</div>', unsafe_allow_html=True)
    pr_counts = df["priority"].value_counts().reset_index()
    pr_counts.columns = ["priority", "count"]
    order = ["Critical", "High", "Medium", "Low"]
    pr_counts["priority"] = pd.Categorical(pr_counts["priority"], categories=order, ordered=True)
    pr_counts = pr_counts.sort_values("priority")
    fig = go.Figure(data=[go.Pie(
        labels=pr_counts["priority"], values=pr_counts["count"], hole=0.62,
        marker=dict(colors=[PRIORITY_COLORS.get(p, "#999") for p in pr_counts["priority"]]),
        textinfo="label+percent", textfont=dict(family="IBM Plex Sans", size=12, color="white"),
    )])
    fig.update_layout(
        height=320, margin=dict(l=6, r=6, t=6, b=6),
        showlegend=False, paper_bgcolor="white",
        annotations=[dict(text=f"{total}<br>total", x=0.5, y=0.5, font_size=16, showarrow=False,
                           font_family="Fraunces", font_color=NAVY)],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------- CHART ROW 2
c3, c4 = st.columns(2)

with c3:
    st.markdown('<div class="section-title">Grievance Volume Over Time</div>', unsafe_allow_html=True)
    daily = df.groupby("date").size().reset_index(name="count")
    fig = px.area(daily, x="date", y="count")
    fig.update_traces(line_color=MARIGOLD, fillcolor="rgba(232,135,30,0.18)")
    fig.update_layout(
        height=280, margin=dict(l=0, r=10, t=6, b=6),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=False, title="", color=INK),
        yaxis=dict(showgrid=True, gridcolor=BORDER, title="", color=INK),
        font=dict(family="IBM Plex Sans", color=INK, size=13),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c4:
    st.markdown('<div class="section-title">Sentiment &amp; Language Mix</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1:
        sent_counts = df["sentiment"].str.lower().value_counts().reset_index()
        sent_counts.columns = ["sentiment", "count"]
        fig = go.Figure(data=[go.Pie(
            labels=sent_counts["sentiment"], values=sent_counts["count"], hole=0.55,
            marker=dict(colors=[SENTIMENT_COLORS.get(s, "#999") for s in sent_counts["sentiment"]]),
            textinfo="percent", textfont=dict(size=11, color="white"),
        )])
        fig.update_layout(height=230, margin=dict(l=0, r=0, t=20, b=0), showlegend=True,
                           legend=dict(orientation="h", y=-0.15, font=dict(size=10, color=INK)),
                           paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with sc2:
        lang_counts = df["language"].value_counts().reset_index()
        lang_counts.columns = ["language", "count"]
        fig = go.Figure(data=[go.Pie(
            labels=lang_counts["language"], values=lang_counts["count"], hole=0.55,
            marker=dict(colors=[NAVY, MARIGOLD]),
            textinfo="percent", textfont=dict(size=11, color="white"),
        )])
        fig.update_layout(height=230, margin=dict(l=0, r=0, t=20, b=0), showlegend=True,
                           legend=dict(orientation="h", y=-0.15, font=dict(size=10, color=INK)),
                           paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------- CASE TABLE
st.markdown('<div class="section-title">All Cases</div>', unsafe_allow_html=True)
st.caption("Click any column header to sort. Click a ROW to open that case in \"Look Up & Update a Case\" below.")

display_df = df[["case_number", "created_at", "language", "category", "department", "priority", "sentiment", "status"]].copy()
display_df = display_df.rename(columns={"created_at": "filed_on"})
display_df["filed_on"] = display_df["filed_on"].dt.strftime("%d %b %Y, %H:%M")
display_df = display_df.sort_values("filed_on", ascending=False).reset_index(drop=True)

table_event = st.dataframe(
    display_df, use_container_width=True, hide_index=True, height=280,
    on_select="rerun", selection_mode="single-row", key="cases_table",
)

clicked_case_number = None
if table_event and table_event.selection and table_event.selection["rows"]:
    clicked_idx = table_event.selection["rows"][0]
    clicked_case_number = display_df.iloc[clicked_idx]["case_number"]

# ---------------------------------------------------------------- STATUS UPDATER + GRIEVANCE PREVIEW
st.markdown('<div id="assign-section"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Look Up &amp; Update a Case</div>', unsafe_allow_html=True)
st.caption("Select a case (or click a row above) to read the full grievance and move it forward in its journey — updates instantly on the citizen tracking portal too.")

if st.session_state.get("scroll_to_assign"):
    components.html("""
    <script>
        setTimeout(function() {
            var el = window.parent.document.getElementById('assign-section');
            if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
        }, 150);
    </script>
    """, height=0)
    st.session_state.scroll_to_assign = False

case_list = df["case_number"].tolist()
override_case = st.session_state.pop("assign_case_override", None)

suggest_assigned = False
if override_case and override_case in case_list:
    default_idx = case_list.index(override_case)
    suggest_assigned = True
elif clicked_case_number in case_list:
    default_idx = case_list.index(clicked_case_number)
else:
    default_idx = 0

u1, u2, u3 = st.columns([2, 1.4, 1])
with u1:
    selected_case = st.selectbox("Case", case_list, index=default_idx, label_visibility="collapsed")

status_options = ["New", "Assigned", "In Progress", "Resolved"]
current_status = df.loc[df["case_number"] == selected_case, "status"].iloc[0]
if suggest_assigned and selected_case == override_case and current_status != "Resolved":
    status_default_idx = status_options.index("Assigned")
else:
    status_default_idx = status_options.index(current_status) if current_status in status_options else 0

with u2:
    new_status = st.selectbox(
        f"New status (currently: {current_status})",
        status_options, index=status_default_idx, label_visibility="collapsed",
    )
with u3:
    if st.button("Update status", use_container_width=True):
        case_id = int(df.loc[df["case_number"] == selected_case, "id"].iloc[0])
        try:
            r = requests.patch(f"{API_URL}/cases/{case_id}/status", params={"status": new_status}, timeout=5)
            if r.ok:
                st.success(f"{selected_case} → {new_status}")
                st.rerun()
            else:
                st.error("Update failed.")
        except requests.exceptions.ConnectionError:
            st.error("Can't reach the API.")

st.caption(f"Currently selected: **{selected_case}** — current status is **{current_status}**.")

selected_row = df.loc[df["case_number"] == selected_case].iloc[0]
image_url = selected_row.get("image_url")

pv1, pv2 = st.columns([1.4, 1])
with pv1:
    source_label = {"text": "Typed", "voice": "Voice recording", "image": "Photo"}.get(selected_row.get("source"), "Typed")
    st.markdown(f"""<div class="grievance-preview">
<div class="k">Grievance text — {selected_row['case_number']} · filed {selected_row['created_at'].strftime('%d %b %Y, %H:%M')} · {source_label}</div>
{selected_row['raw_text']}
</div>""", unsafe_allow_html=True)

    if image_url:
        st.markdown('<div class="k" style="margin-top:14px; margin-bottom:6px;">Attached photo</div>', unsafe_allow_html=True)
        st.image(f"{API_URL}{image_url}", use_column_width=True)

with pv2:
    citizen_name = selected_row.get("citizen_name") or "Not available"
    citizen_phone = selected_row.get("citizen_phone") or "Not available"
    citizen_email = selected_row.get("citizen_email") or "Not available"
    citizen_address = selected_row.get("citizen_address") or "Not provided"
    st.markdown(f"""<div class="grievance-preview" style="border-left-color: {NAVY};">
<div class="k">Filed by</div>
<div style="font-weight:600; font-size:15px; color:{NAVY}; margin-bottom:6px;">{citizen_name}</div>
<div style="font-size:13.5px; line-height:1.7;">
📞 {citizen_phone}<br>
✉️ {citizen_email}<br>
📍 {citizen_address}
</div>
</div>""", unsafe_allow_html=True)
