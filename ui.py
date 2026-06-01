import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date

DARK_THEME = {
    "bg": "#0b1120",
    "card": "rgba(19, 27, 46, 0.75)",
    "card_border": "rgba(0, 212, 170, 0.15)",
    "accent_teal": "#00d4aa",
    "accent_cyan": "#00e5ff",
    "accent_purple": "#7c3aed",
    "accent_indigo": "#4f46e5",
    "accent_gold": "#f59e0b",
    "gradient_teal_purple": "linear-gradient(135deg, #00d4aa, #7c3aed)",
    "gradient_cyan_indigo": "linear-gradient(135deg, #00e5ff, #4f46e5)",
    "positive": "#00d4aa",
    "negative": "#ef4444",
    "text": "#e8edf5",
    "text_muted": "#8892a8",
    "text_dim": "#4a5578",
    "plot_bg": "#0d1428",
    "paper_bg": "rgba(0,0,0,0)",
}

CUSTOM_CSS = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * {{ font-family: 'Inter', -apple-system, sans-serif; }}
        .stApp {{ background: {DARK_THEME["bg"]}; }}
        .stApp > header {{ background: rgba(11, 17, 32, 0.8); backdrop-filter: blur(12px); }}

        .main-header {{
            font-size: 2rem; font-weight: 800;
            background: {DARK_THEME["gradient_teal_purple"]};
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
            padding: 0.5rem 0;
        }}
        .sub-header {{
            color: {DARK_THEME["text_muted"]}; font-size: 0.85rem;
            font-weight: 400; letter-spacing: 0.3px;
            margin-bottom: 1.5rem;
        }}

        .glass-card {{
            background: {DARK_THEME["card"]};
            border: 1px solid {DARK_THEME["card_border"]};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .glass-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 40px rgba(0, 212, 170, 0.08), 0 4px 24px rgba(0, 0, 0, 0.3);
        }}

        .kpi-label {{
            color: {DARK_THEME["text_muted"]}; font-size: 0.7rem;
            text-transform: uppercase; letter-spacing: 1.2px; font-weight: 500;
        }}
        .kpi-value {{
            font-size: 1.75rem; font-weight: 700; color: {DARK_THEME["text"]};
            margin: 0.15rem 0; letter-spacing: -0.3px;
        }}
        .kpi-delta-pos {{ color: {DARK_THEME["positive"]}; font-weight: 600; font-size: 0.85rem; }}
        .kpi-delta-neg {{ color: {DARK_THEME["negative"]}; font-weight: 600; font-size: 0.85rem; }}
        .metric-icon {{ font-size: 1.5rem; margin-right: 0.5rem; }}

        .stTabs [data-baseweb="tab-list"] {{ gap: 0; border-bottom: 1px solid rgba(255,255,255,0.06); }}
        .stTabs [data-baseweb="tab"] {{
            color: {DARK_THEME["text_muted"]}; font-weight: 500;
            padding: 0.75rem 1.5rem;
            transition: color 0.2s;
        }}
        .stTabs [aria-selected="true"] {{
            color: {DARK_THEME["accent_teal"]} !important;
            box-shadow: inset 0 -2px 0 {DARK_THEME["accent_teal"]};
        }}

        div[data-testid="stDataFrame"] {{ background: transparent; }}
        .st-dg {{ background: transparent !important; }}

        .upload-section {{
            background: {DARK_THEME["card"]};
            border: 2px dashed rgba(0, 212, 170, 0.25);
            border-radius: 16px; padding: 2rem; text-align: center;
            transition: border-color 0.3s, box-shadow 0.3s;
        }}
        .upload-section:hover {{
            border-color: {DARK_THEME["accent_teal"]};
            box-shadow: 0 0 24px rgba(0, 212, 170, 0.06);
        }}

        .stProgress .st-bo {{ background: {DARK_THEME["gradient_teal_purple"]}; }}

        .stDateInput input {{
            background: {DARK_THEME["card"]} !important;
            border: 1px solid {DARK_THEME["card_border"]} !important;
            color: {DARK_THEME["text"]} !important;
            border-radius: 10px !important;
        }}
        .stSelectbox div[data-baseweb="select"] {{
            background: {DARK_THEME["card"]} !important;
            border-color: {DARK_THEME["card_border"]} !important;
            border-radius: 10px !important;
        }}
        .st-bb {{ color: {DARK_THEME["text"]} !important; }}

        hr {{ border-color: rgba(255, 255, 255, 0.04); margin: 1.5rem 0; }}

        .stButton button {{
            border-radius: 10px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }}
        .stButton button[kind="primary"] {{
            background: {DARK_THEME["gradient_teal_purple"]} !important;
            border: none !important;
            color: white !important;
            box-shadow: 0 4px 16px rgba(0, 212, 170, 0.2) !important;
        }}
        .stButton button[kind="primary"]:hover {{
            box-shadow: 0 6px 24px rgba(0, 212, 170, 0.35) !important;
            transform: translateY(-1px);
        }}
        .stButton button[kind="secondary"] {{
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            color: {DARK_THEME["text_muted"]} !important;
        }}
        .stButton button[kind="secondary"]:hover {{
            border-color: {DARK_THEME["accent_teal"]} !important;
            color: {DARK_THEME["accent_teal"]} !important;
        }}

        .stAlert {{
            background: {DARK_THEME["card"]} !important;
            border: 1px solid {DARK_THEME["card_border"]} !important;
            border-radius: 12px !important;
        }}
        .stAlert > div:first-child {{ color: {DARK_THEME["accent_gold"]} !important; }}

        ::-webkit-scrollbar {{
            width: 6px; height: 6px;
        }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(255,255,255,0.08);
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.15); }}
    </style>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = ""):
    st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="sub-header">{subtitle}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, delta: str = None, delta_positive: bool = True, icon: str = ""):
    delta_class = "kpi-delta-pos" if delta_positive else "kpi-delta-neg"
    arrow = "▲" if delta_positive else "▼"
    delta_html = f'<div class="{delta_class}">{arrow} {delta}</div>' if delta is not None else ""
    st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-label">{icon} {label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def make_dark_figure():
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=DARK_THEME["paper_bg"],
        plot_bgcolor=DARK_THEME["plot_bg"],
        font=dict(color=DARK_THEME["text"], family="Inter, sans-serif", size=12),
        margin=dict(l=20, r=20, t=50, b=40),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(19, 27, 46, 0.95)",
            bordercolor="rgba(0, 212, 170, 0.3)",
            font=dict(color=DARK_THEME["text"], size=12),
        ),
        legend=dict(
            orientation="h", y=1.12, x=0.5, xanchor="center",
            font=dict(size=11, color=DARK_THEME["text_muted"]),
        ),
    )
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.03)",
        zeroline=False,
        tickfont=dict(size=11, color=DARK_THEME["text_dim"]),
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.03)",
        zeroline=False,
        tickfont=dict(size=11, color=DARK_THEME["text_dim"]),
    )
    return fig


def trend_chart(data: pd.DataFrame, x_col: str, y_cols: list[str], names: list[str],
                title: str = "", colors: list[str] = None) -> go.Figure:
    if colors is None:
        colors = [DARK_THEME["accent_teal"], DARK_THEME["accent_purple"],
                  DARK_THEME["accent_cyan"], DARK_THEME["accent_gold"]]
    fig = make_dark_figure()
    for i, yc in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=data[x_col], y=data[yc], mode="lines+markers",
            name=names[i] if i < len(names) else yc,
            line=dict(color=colors[i % len(colors)], width=2.5),
            marker=dict(size=5, color=colors[i % len(colors)],
                        line=dict(color="rgba(255,255,255,0.15)", width=1)),
            hovertemplate=f"%{{x|%b %d, %Y}}<br>%{{y:,.0f}}<extra></extra>"
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=DARK_THEME["text"])),
        shapes=[dict(
            type="rect", xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color=DARK_THEME["card_border"], width=1),
        )],
    )
    return fig


def bar_chart(data: pd.DataFrame, x_col: str, y_col: str, title: str = "",
              color: str = None) -> go.Figure:
    if color is None:
        color = DARK_THEME["accent_teal"]
    fig = make_dark_figure()
    fig.add_trace(go.Bar(
        x=data[x_col], y=data[y_col],
        marker=dict(
            color=color,
            line=dict(color="rgba(255,255,255,0.1)", width=0.5),
        ),
        opacity=0.9,
        hovertemplate=f"%{{x}}<br>%{{y:,.0f}}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=DARK_THEME["text"])),
        xaxis=dict(tickangle=-45),
        shapes=[dict(
            type="rect", xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color=DARK_THEME["card_border"], width=1),
        )],
    )
    return fig


def donut_chart(data: pd.DataFrame, names_col: str, values_col: str, title: str = "",
                n: int = 8) -> go.Figure:
    df = data.head(n).copy()
    colors = ["#00d4aa", "#7c3aed", "#00e5ff", "#4f46e5",
              "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]
    fig = go.Figure(data=[go.Pie(
        labels=df[names_col], values=df[values_col],
        hole=0.6,
        marker=dict(
            colors=colors[:len(df)],
            line=dict(color=DARK_THEME["plot_bg"], width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=11, color=DARK_THEME["text"]),
        hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>",
        rotation=90,
    )])
    fig.update_layout(
        paper_bgcolor=DARK_THEME["paper_bg"],
        plot_bgcolor=DARK_THEME["plot_bg"],
        font=dict(color=DARK_THEME["text"], family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(text=title, font=dict(size=14, color=DARK_THEME["text"])),
        showlegend=False,
    )
    return fig
