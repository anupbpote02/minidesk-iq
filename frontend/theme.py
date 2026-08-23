"""Shared light-theme tokens for both Streamlit apps (validated dataviz palette, light mode)."""

PAGE_PLANE = "#f9f9f7"
SURFACE = "#ffffff"
CHART_SURFACE = "#fcfcfb"
BORDER = "rgba(11,11,11,0.10)"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"

SERIES = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
}
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

CATEGORICAL_ORDER = [SERIES["blue"], SERIES["orange"], SERIES["aqua"], SERIES["yellow"]]

FONT_STACK = "system-ui, -apple-system, 'Segoe UI', sans-serif"

BASE_CSS = f"""
<style>
    .stApp {{ background-color: {PAGE_PLANE}; color: {TEXT_PRIMARY}; }}
    section[data-testid="stSidebar"] {{
        background-color: {SURFACE};
        border-right: 1px solid {GRIDLINE};
    }}
    div[data-testid="stMetric"] {{
        background-color: {SURFACE};
        border: 1px solid {GRIDLINE};
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 2px {BORDER};
    }}
    div[data-testid="stMetricValue"] {{ color: {TEXT_PRIMARY} !important; }}
    div[data-testid="stMetricLabel"] {{ color: {TEXT_SECONDARY} !important; }}
    .block-container {{ padding-top: 2rem; }}
    h1, h2, h3, h4, h5, h6 {{ color: {TEXT_PRIMARY} !important; }}
    p, span, label, .stMarkdown {{ color: {TEXT_PRIMARY}; }}
    .stCaption, [data-testid="stCaptionContainer"] {{ color: {TEXT_MUTED} !important; }}
</style>
"""


def chart_layout(**overrides):
    base = dict(
        paper_bgcolor=CHART_SURFACE,
        plot_bgcolor=CHART_SURFACE,
        font=dict(color=TEXT_SECONDARY, family=FONT_STACK),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_SECONDARY)),
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(gridcolor=GRIDLINE, zerolinecolor=BASELINE, color=TEXT_MUTED),
        yaxis=dict(gridcolor=GRIDLINE, zerolinecolor=BASELINE, color=TEXT_MUTED),
    )
    for axis_key in ("xaxis", "yaxis"):
        if axis_key in overrides:
            base[axis_key] = {**base[axis_key], **overrides.pop(axis_key)}
    base.update(overrides)
    return base
