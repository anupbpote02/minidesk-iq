import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import API_BASE_URL, TICKET_CATEGORIES, TICKET_STATUSES  # noqa: E402
from frontend.auth import ADMIN_GRADIENT, render_login_gate  # noqa: E402
from frontend.theme import (  # noqa: E402
    BASE_CSS,
    CATEGORICAL_ORDER,
    SERIES,
    STATUS,
    chart_layout,
)

st.set_page_config(page_title="MiniDesk IQ · Admin", page_icon="📊", layout="wide")

render_login_gate(
    allowed_roles={"admin"},
    title="Admin Login",
    welcome_text="Welcome back to the Admin Dashboard",
    welcome_icon="📊",
    gradient_css=ADMIN_GRADIENT,
)

st.markdown(BASE_CSS, unsafe_allow_html=True)

TICKET_STATUS_COLORS = {"open": STATUS["warning"], "in_progress": STATUS["serious"], "resolved": STATUS["good"]}

with st.sidebar:
    st.caption(f"Logged in as **{st.session_state.display_name}**")
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_role = None
        st.session_state.display_name = None
        st.rerun()

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(ttl=15)
def load_query_logs() -> pd.DataFrame:
    try:
        resp = requests.get(f"{API_BASE_URL}/logs/queries", params={"limit": 5000}, timeout=10)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
    except Exception:
        df = pd.DataFrame()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["success"] = df["success"].astype(bool)
        df["is_knowledge_gap"] = df["is_knowledge_gap"].astype(bool)
    return df


@st.cache_data(ttl=15)
def load_tickets() -> pd.DataFrame:
    try:
        resp = requests.get(f"{API_BASE_URL}/tickets", timeout=10)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
    except Exception:
        df = pd.DataFrame()
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df


@st.cache_data(ttl=15)
def load_audit_log() -> pd.DataFrame:
    try:
        resp = requests.get(f"{API_BASE_URL}/logs/audit", params={"limit": 1000}, timeout=10)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
    except Exception:
        df = pd.DataFrame()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def classify_query_type(row) -> str:
    action = row["action_taken"]
    source = str(row.get("source") or "")
    if action == "rag":
        return "RAG"
    if "create_ticket" in source:
        return "Create Ticket"
    if "check_ticket_status" in source:
        return "Check Status"
    if "approve_request" in source:
        return "Approve"
    return "Tool" if action in ("tool", "both") else "Other"


query_logs = load_query_logs()
tickets = load_tickets()
audit_log = load_audit_log()

st.markdown("# 📊 MiniDesk IQ · Admin Dashboard")

col1, col2, col3 = st.columns(3)
with col1:
    date_range = st.selectbox("Date range", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"], index=1)
with col2:
    category_filter = st.selectbox("Category", ["All"] + TICKET_CATEGORIES)
with col3:
    status_filter = st.selectbox("Status", ["All"] + TICKET_STATUSES)

now = datetime.now(timezone.utc)
range_days = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All time": None}[date_range]
cutoff = now - timedelta(days=range_days) if range_days else None

if not query_logs.empty:
    qdf = query_logs.copy()
    qdf["timestamp"] = qdf["timestamp"].dt.tz_localize("UTC") if qdf["timestamp"].dt.tz is None else qdf["timestamp"]
    if cutoff:
        qdf = qdf[qdf["timestamp"] >= cutoff]
else:
    qdf = query_logs

if not tickets.empty:
    tdf = tickets.copy()
    tdf["created_at"] = tdf["created_at"].dt.tz_localize("UTC") if tdf["created_at"].dt.tz is None else tdf["created_at"]
    if cutoff:
        tdf = tdf[tdf["created_at"] >= cutoff]
    if category_filter != "All":
        tdf = tdf[tdf["category"] == category_filter]
    if status_filter != "All":
        tdf = tdf[tdf["status"] == status_filter]
else:
    tdf = tickets

st.markdown("---")

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
total_queries = len(qdf)
tickets_created = len(tdf)
avg_latency = qdf["latency_ms"].mean() if not qdf.empty else None
rag_queries = qdf[qdf["action_taken"].isin(["rag", "both"])] if not qdf.empty else qdf
retrieval_success_rate = (
    100 * (1 - rag_queries["is_knowledge_gap"].mean()) if not rag_queries.empty else None
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Queries", f"{total_queries:,}")
k2.metric("Tickets Created", f"{tickets_created:,}")
k3.metric("Avg Response Time", f"{avg_latency/1000:.2f}s" if pd.notna(avg_latency) else "—")
k4.metric("Retrieval Success Rate", f"{retrieval_success_rate:.0f}%" if pd.notna(retrieval_success_rate) else "—")

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart grid
# ---------------------------------------------------------------------------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown("#### Queries Over Time")
    if not qdf.empty:
        by_minute = qdf.set_index("timestamp").resample("1min").size().reset_index(name="count")
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=by_minute["timestamp"],
                y=by_minute["count"],
                mode="lines",
                line=dict(color=SERIES["blue"], width=2, shape="spline"),
                fill="tozeroy",
                fillcolor="rgba(42,120,214,0.12)",
                hovertemplate="%{x|%H:%M}: %{y} queries<extra></extra>",
            )
        )
        fig.update_layout(
            **chart_layout(
                height=300,
                showlegend=False,
                xaxis=dict(type="date", tickformat="%H:%M", hoverformat="%H:%M"),
                yaxis=dict(rangemode="tozero"),
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No query data yet.")

with row1_col2:
    st.markdown("#### Query Type Split")
    if not qdf.empty:
        qdf_local = qdf.copy()
        qdf_local["query_type"] = qdf_local.apply(classify_query_type, axis=1)
        type_counts = qdf_local["query_type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=type_counts["type"],
                    values=type_counts["count"],
                    hole=0.55,
                    marker=dict(colors=CATEGORICAL_ORDER, line=dict(color="#ffffff", width=2)),
                    textinfo="label+percent",
                    textposition="outside",
                    textfont=dict(color="#0b0b0b"),
                )
            ]
        )
        fig.update_layout(**chart_layout(height=300))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No query data yet.")

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("#### Ticket Status")
    if not tickets.empty:
        status_by_cat = tickets.groupby(["category", "status"]).size().reset_index(name="count")
        fig = go.Figure()
        for status in TICKET_STATUSES:
            sub = status_by_cat[status_by_cat["status"] == status]
            fig.add_trace(
                go.Bar(
                    x=sub["category"],
                    y=sub["count"],
                    name=status.replace("_", " ").title(),
                    marker=dict(color=TICKET_STATUS_COLORS[status]),
                )
            )
        fig.update_layout(**chart_layout(height=320, barmode="stack", showlegend=True))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tickets yet.")

with row2_col2:
    st.markdown("#### Top Requested Policies")
    if not qdf.empty:
        rag_hits = qdf[qdf["action_taken"].isin(["rag", "both"]) & qdf["source"].notna()]
        if not rag_hits.empty:
            sources = rag_hits["source"].str.split(", ").explode()
            top_sources = sources.value_counts().reset_index()
            top_sources.columns = ["doc", "count"]
            top_sources = top_sources.head(10).sort_values("count")
            fig = go.Figure(
                go.Bar(
                    x=top_sources["count"],
                    y=top_sources["doc"],
                    orientation="h",
                    marker=dict(color=SERIES["aqua"]),
                )
            )
            fig.update_layout(**chart_layout(height=320, showlegend=False))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No policy retrievals yet.")
    else:
        st.info("No query data yet.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Knowledge gaps table
# ---------------------------------------------------------------------------
st.markdown("#### ⚠️ Knowledge Gaps (Unanswered Questions)")
if not qdf.empty:
    gaps = qdf[qdf["is_knowledge_gap"]][["timestamp", "user_query", "response"]].sort_values(
        "timestamp", ascending=False
    )
    if not gaps.empty:
        st.dataframe(gaps, use_container_width=True, hide_index=True)
    else:
        st.success("No knowledge gaps in this range.")
else:
    st.info("No query data yet.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Searchable audit log
# ---------------------------------------------------------------------------
st.markdown("#### Audit Log")
search_term = st.text_input("Search audit log", placeholder="Filter by actor, event type, or detail...")
if not audit_log.empty:
    filtered_audit = audit_log
    if search_term:
        mask = audit_log.apply(
            lambda r: search_term.lower() in str(r.get("actor", "")).lower()
            or search_term.lower() in str(r.get("event_type", "")).lower()
            or search_term.lower() in str(r.get("detail", "")).lower(),
            axis=1,
        )
        filtered_audit = audit_log[mask]
    st.dataframe(
        filtered_audit.sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No audit log entries yet.")
