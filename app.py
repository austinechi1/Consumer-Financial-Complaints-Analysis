from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Consumer Complaints Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "data" / "processed"

PAGES = [
    ("Overview", "⌂"),
    ("Complaint Trends", "⌁"),
    ("Products", "◇"),
    ("Companies", "▦"),
    ("Geography", "⌖"),
    ("Data Quality", "◉"),
]

FILTER_KEYS = ["year_filter", "product_filter", "state_filter", "company_filter"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    datasets = {
        "monthly": pd.read_csv(DATA_PATH / "monthly_trend.csv"),
        "products": pd.read_csv(DATA_PATH / "product_summary.csv"),
        "states": pd.read_csv(DATA_PATH / "state_summary.csv"),
        "companies": pd.read_csv(DATA_PATH / "company_performance.csv"),
        "responses": pd.read_csv(DATA_PATH / "product_response_performance.csv"),
        "issues": pd.read_csv(DATA_PATH / "top_product_issues.csv"),
    }

    for dataframe in datasets.values():
        dataframe.columns = (
            dataframe.columns.str.strip().str.lower().str.replace(" ", "_")
        )

    datasets["monthly"]["complaint_month"] = pd.to_datetime(
        datasets["monthly"]["complaint_month"]
    )

    numeric_columns = {
        "monthly": ["total_complaints", "three_month_moving_average"],
        "products": ["total_complaints", "percentage_of_all_complaints", "complaint_rank"],
        "states": [
            "total_complaints",
            "percentage_of_all_complaints",
            "late_responses",
            "late_response_rate_pct",
        ],
        "companies": ["total_complaints", "late_responses", "late_response_rate_pct"],
        "responses": [
            "total_complaints",
            "timely_responses",
            "late_responses",
            "timely_response_rate_pct",
        ],
        "issues": ["total_complaints", "issue_rank"],
    }

    for dataset_name, columns in numeric_columns.items():
        for column in columns:
            if column in datasets[dataset_name].columns:
                datasets[dataset_name][column] = pd.to_numeric(
                    datasets[dataset_name][column], errors="coerce"
                )

    return datasets


try:
    data = load_data()
except FileNotFoundError as error:
    st.error(
        "A required dashboard CSV file is missing. Confirm that all six summary "
        "files are inside data/processed."
    )
    st.code(str(error))
    st.stop()

monthly = data["monthly"].sort_values("complaint_month").reset_index(drop=True)
products = data["products"]
states = data["states"]
companies = data["companies"]
responses = data["responses"]
issues = data["issues"]


# ---------------------------------------------------------------------------
# Session state (navigation, theme, filters)
# ---------------------------------------------------------------------------
available_years = sorted(monthly["complaint_month"].dt.year.unique().tolist())
product_options = ["All Products"] + sorted(products["product"].dropna().unique().tolist())
state_options = ["All States"] + sorted(states["state"].dropna().unique().tolist())
company_options = ["All Companies"] + sorted(companies["company"].dropna().unique().tolist())

DEFAULT_FILTERS = {
    "year_filter": available_years,
    "product_filter": "All Products",
    "state_filter": "All States",
    "company_filter": "All Companies",
}

if "page" not in st.session_state:
    st.session_state.page = "Overview"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
for _key, _value in DEFAULT_FILTERS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _value


def go_to(page_name):
    st.session_state.page = page_name


def reset_filters():
    for key, value in DEFAULT_FILTERS.items():
        st.session_state[key] = value


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
light_theme = {
    "background": "#F4F7FB",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "text": "#0B1220",
    "muted": "#64748B",
    "border": "#DFE7F1",
    "grid": "#E7EDF5",
    "blue": "#2563EB",
    "blue_soft": "#EAF2FF",
    "teal": "#0D9488",
    "coral": "#F97366",
    "purple": "#7657F6",
}

dark_theme = {
    "background": "#0B1220",
    "surface": "#111C2F",
    "surface_alt": "#16233A",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "border": "#243653",
    "grid": "#223452",
    "blue": "#3B82F6",
    "blue_soft": "#18345C",
    "teal": "#14B8A6",
    "coral": "#F97366",
    "purple": "#8B6CF6",
}

theme = dark_theme if st.session_state.dark_mode else light_theme


def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


st.markdown(
    f"""
    <style>
        :root {{
            --background: {theme['background']};
            --surface: {theme['surface']};
            --surface-alt: {theme['surface_alt']};
            --text: {theme['text']};
            --muted: {theme['muted']};
            --border: {theme['border']};
            --blue: {theme['blue']};
            --blue-soft: {theme['blue_soft']};
            --teal: {theme['teal']};
            --coral: {theme['coral']};
        }}

        .stApp {{ background: var(--background); color: var(--text); }}

        .block-container {{
            max-width: 1680px;
            padding-top: 1.15rem;
            padding-bottom: 2rem;
        }}

        [data-testid="stHeader"] {{ background: transparent; }}

        [data-testid="stSidebar"] {{
            background: var(--surface);
            border-right: 1px solid var(--border);
        }}
        [data-testid="stSidebar"] > div:first-child {{ padding-top: 1.2rem; }}
        [data-testid="stSidebar"] hr {{ border-color: var(--border); }}

        h1, h2, h3, h4, p, label, span {{ color: var(--text); }}

        h1 {{
            font-size: clamp(2rem, 3vw, 3.25rem) !important;
            letter-spacing: -0.045em;
            margin: 0 !important;
            line-height: 1.05 !important;
        }}

        h3 {{ font-size: 1.1rem !important; font-weight: 800 !important; }}

        .app-subtitle {{
            color: var(--muted);
            font-size: 1.03rem;
            margin-top: .35rem;
        }}

        /* ---------- Sidebar brand ---------- */
        .brand {{
            display: flex;
            align-items: center;
            gap: .75rem;
            padding: .25rem .25rem 1.1rem;
        }}
        .brand-mark {{
            display: grid;
            grid-template-columns: repeat(3, 6px);
            align-items: end;
            gap: 3px;
            height: 29px;
        }}
        .brand-mark span {{
            display: block;
            width: 6px;
            background: var(--blue);
            border-radius: 4px;
        }}
        .brand-mark span:nth-child(1) {{ height: 13px; }}
        .brand-mark span:nth-child(2) {{ height: 21px; }}
        .brand-mark span:nth-child(3) {{ height: 29px; }}
        .brand-title {{
            color: var(--text);
            font-size: 1rem;
            font-weight: 800;
            line-height: 1.2;
        }}

        /* ---------- Sidebar navigation buttons ---------- */
        [data-testid="stSidebar"] .stButton > button {{
            width: 100%;
            justify-content: flex-start;
            text-align: left;
            background: transparent;
            border: none;
            border-left: 3px solid transparent;
            border-radius: 10px;
            box-shadow: none;
            padding: .72rem .8rem;
            color: var(--muted);
            font-weight: 600;
        }}
        [data-testid="stSidebar"] .stButton > button div {{
            justify-content: flex-start;
            text-align: left;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            background: var(--blue-soft);
            color: var(--blue);
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"],
        [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {{
            background: var(--blue-soft);
            color: var(--blue);
            border-left: 3px solid var(--blue);
        }}

        .stButton button p,
        .stDownloadButton button p {{ color: inherit !important; }}

        .source-card {{
            margin-top: 4rem;
            padding: 1rem .25rem .1rem;
            border-top: 1px solid var(--border);
            color: var(--muted);
            font-size: .82rem;
            line-height: 1.8;
        }}
        .source-card strong {{
            color: var(--text);
            display: block;
            font-size: .9rem;
        }}

        /* ---------- Cards ---------- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--surface);
            border-color: var(--border) !important;
            border-radius: 14px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, .04);
        }}

        div[data-testid="stMetric"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1rem 1.05rem;
            min-height: 125px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, .04);
        }}
        [data-testid="stMetricLabel"] p {{ color: var(--muted); font-weight: 650; }}
        [data-testid="stMetricValue"] {{ color: var(--text); font-weight: 800; }}
        [data-testid="stMetricDelta"] {{ color: var(--muted); }}

        .section-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1.05rem 1.1rem;
            box-shadow: 0 4px 18px rgba(15, 23, 42, .04);
            height: 100%;
        }}
        .insight-title {{
            color: var(--teal);
            font-weight: 800;
            font-size: 1.05rem;
            margin-bottom: .8rem;
        }}
        .insight-heading {{
            color: var(--text);
            font-size: 1.35rem;
            font-weight: 800;
            line-height: 1.3;
            margin-bottom: .65rem;
        }}
        .insight-copy {{ color: var(--muted); line-height: 1.55; }}
        .insight-copy strong {{ color: var(--text); }}

        [data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 4px 18px rgba(15, 23, 42, .04);
        }}

        div[data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {{
            background: var(--surface-alt) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
        }}

        [data-testid="stMain"] .stButton > button,
        .main .stButton > button,
        .stDownloadButton > button {{
            width: 100%;
            border: 1px solid var(--border) !important;
            background: var(--blue-soft) !important;
            color: var(--blue) !important;
            border-radius: 10px;
            font-weight: 700;
        }}

        .footer {{
            color: var(--muted);
            text-align: center;
            padding-top: 1.6rem;
            font-size: .82rem;
        }}

        @media (max-width: 900px) {{
            .source-card {{ margin-top: 2rem; }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def show_chart(figure, key):
    """Render a Plotly chart full width across Streamlit versions."""
    try:
        st.plotly_chart(figure, width="stretch", key=key)
    except Exception:
        st.plotly_chart(figure, use_container_width=True, key=key)


def show_table(frame, height=None):
    """Render a dataframe full width across Streamlit versions."""
    kwargs = {"hide_index": True}
    if height:
        kwargs["height"] = height
    try:
        st.dataframe(frame, width="stretch", **kwargs)
    except Exception:
        st.dataframe(frame, use_container_width=True, **kwargs)


def apply_chart_style(figure, height=390, show_legend=True):
    figure.update_layout(
        height=height,
        paper_bgcolor=theme["surface"],
        plot_bgcolor=theme["surface"],
        font=dict(color=theme["text"], family="Arial, sans-serif"),
        title=dict(font=dict(color=theme["text"], size=17), x=0.02, xanchor="left"),
        margin=dict(l=30, r=25, t=65, b=35),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=theme["muted"]),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        showlegend=show_legend,
        hoverlabel=dict(bgcolor=theme["surface"], font_color=theme["text"]),
    )
    figure.update_xaxes(
        gridcolor=theme["grid"],
        linecolor=theme["border"],
        tickfont=dict(color=theme["muted"]),
        title_font=dict(color=theme["muted"]),
        zeroline=False,
    )
    figure.update_yaxes(
        gridcolor=theme["grid"],
        linecolor=theme["border"],
        tickfont=dict(color=theme["muted"]),
        title_font=dict(color=theme["muted"]),
        zeroline=False,
    )
    return figure


def empty_notice(message="No data for the selected filters."):
    st.info(message)


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
total_records = int(products["total_complaints"].sum())
period_start = monthly["complaint_month"].min().strftime("%b %Y")
period_end = monthly["complaint_month"].max().strftime("%b %Y")

st.sidebar.markdown(
    """
    <div class="brand">
        <div class="brand-mark"><span></span><span></span><span></span></div>
        <div class="brand-title">Consumer Complaints<br>Intelligence</div>
    </div>
    """,
    unsafe_allow_html=True,
)

for page_name, icon in PAGES:
    st.sidebar.button(
        f"{icon}   {page_name}",
        key=f"nav_{page_name}",
        on_click=go_to,
        args=(page_name,),
        type="primary" if st.session_state.page == page_name else "secondary",
        use_container_width=True,
    )

st.sidebar.markdown(
    f"""
    <div class="source-card">
        <strong>▰ &nbsp; CFPB Public Data</strong>
        {total_records:,} records<br>
        Updated through {period_end}
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.session_state.page


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
title_col, theme_col = st.columns([8.5, 1.5], vertical_alignment="center")
with title_col:
    st.title("Consumer Complaints Intelligence")
    subtitles = {
        "Overview": "Explore complaint volume, response performance and emerging consumer risks",
        "Complaint Trends": "Track how complaint volume changes month by month and year over year",
        "Products": "See which financial products and issues drive the most complaints",
        "Companies": "Compare complaint volume and late-response rates across companies",
        "Geography": "Find where complaints come from and where responses run late",
        "Data Quality": "Check that the summary files are complete and consistent",
    }
    st.markdown(
        f'<div class="app-subtitle">{subtitles[page]}</div>',
        unsafe_allow_html=True,
    )

with theme_col:
    st.toggle("🌙 Dark mode", key="dark_mode")


# ---------------------------------------------------------------------------
# Filters (shown on every page except Data Quality)
# ---------------------------------------------------------------------------
if page != "Data Quality":
    with st.container(border=True):
        f_year, f_product, f_state, f_company, f_reset = st.columns(
            [1.25, 1.25, 1.25, 1.25, 0.85], vertical_alignment="bottom"
        )
        with f_year:
            st.multiselect(
                "Year", available_years, key="year_filter", placeholder="Select years"
            )
        with f_product:
            st.selectbox("Product", product_options, key="product_filter")
        with f_state:
            st.selectbox("State", state_options, key="state_filter")
        with f_company:
            st.selectbox("Company", company_options, key="company_filter")
        with f_reset:
            st.button("↻ Reset Filters", on_click=reset_filters, key="reset_button")
else:
    # Keep filter choices alive while a page without filter widgets is shown.
    for _key in FILTER_KEYS:
        st.session_state[_key] = st.session_state[_key]

selected_years = st.session_state.year_filter
selected_product = st.session_state.product_filter
selected_state = st.session_state.state_filter
selected_company = st.session_state.company_filter

if page != "Data Quality" and not selected_years:
    st.warning("Select at least one year to see complaint trends and totals.")

# Apply filters to the dataset that contains each dimension.
filtered_monthly = monthly[monthly["complaint_month"].dt.year.isin(selected_years)].copy()

filtered_products = products.copy()
filtered_issues = issues.copy()
filtered_responses = responses.copy()
if selected_product != "All Products":
    filtered_products = filtered_products[filtered_products["product"] == selected_product]
    filtered_issues = filtered_issues[filtered_issues["product"] == selected_product]
    if "product" in filtered_responses.columns:
        filtered_responses = filtered_responses[
            filtered_responses["product"] == selected_product
        ]

filtered_states = states.copy()
if selected_state != "All States":
    filtered_states = filtered_states[filtered_states["state"] == selected_state]

filtered_companies = companies.copy()
if selected_company != "All Companies":
    filtered_companies = filtered_companies[filtered_companies["company"] == selected_company]


# ---------------------------------------------------------------------------
# Shared metrics and chart builders
# ---------------------------------------------------------------------------
def response_rates(frame):
    total = frame["total_complaints"].sum()
    if not total:
        return 0.0, 0.0
    timely = frame["timely_responses"].sum() / total * 100
    return timely, 100 - timely


def render_kpis():
    selected_total = int(filtered_monthly["total_complaints"].sum())
    timely_rate, late_rate = response_rates(filtered_responses)
    top_row = products.sort_values("total_complaints", ascending=False).iloc[0]
    if selected_product != "All Products" and not filtered_products.empty:
        top_row = filtered_products.iloc[0]

    year_label = (
        ", ".join(map(str, selected_years)) if selected_years else "No year selected"
    )
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "📄  Selected Complaints",
        f"{selected_total:,.0f}",
        year_label,
        delta_color="off",
    )
    k2.metric(
        "✓  Timely Response",
        f"{timely_rate:.1f}%",
        "of complaints closed on time",
        delta_color="off",
    )
    k3.metric(
        "⏱  Late Response",
        f"{late_rate:.1f}%",
        "of complaints answered late",
        delta_color="off",
    )
    k4.metric(
        "◇  Leading Product" if selected_product == "All Products" else "◇  Product",
        str(top_row["product"]),
        f"{top_row['percentage_of_all_complaints']:.1f}% of all complaints",
        delta_color="off",
    )


def trend_figure(frame, title="Monthly Consumer Complaints", height=420):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=frame["complaint_month"],
            y=frame["total_complaints"],
            mode="lines+markers",
            name="Monthly complaints",
            line=dict(color=theme["blue"], width=3),
            marker=dict(size=6, color=theme["blue"]),
            fill="tozeroy",
            fillcolor=hex_to_rgba(theme["blue"], 0.08),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["complaint_month"],
            y=frame["three_month_moving_average"],
            mode="lines",
            name="3-month moving average",
            line=dict(color=theme["teal"], width=2.5),
        )
    )
    if not frame.empty:
        peak = frame.loc[frame["total_complaints"].idxmax()]
        figure.add_annotation(
            x=peak["complaint_month"],
            y=peak["total_complaints"],
            text=f"Peak: {int(peak['total_complaints']):,}",
            showarrow=True,
            arrowcolor=theme["coral"],
            bordercolor=theme["coral"],
            bgcolor=theme["surface"],
            font=dict(color=theme["coral"]),
            ax=70,
            ay=-45,
        )
    figure.update_layout(title=title, xaxis_title=None, yaxis_title=None)
    return apply_chart_style(figure, height=height)


def key_finding_html():
    change = monthly.copy()
    change["previous"] = change["total_complaints"].shift(1)
    change["pct_change"] = (
        (change["total_complaints"] - change["previous"]) / change["previous"] * 100
    )
    change = change.dropna(subset=["pct_change"])
    if change.empty:
        return ""
    row = change.loc[change["pct_change"].idxmax()]
    month_label = row["complaint_month"].strftime("%B %Y")
    previous_label = (
        row["complaint_month"] - pd.DateOffset(months=1)
    ).strftime("%B %Y")
    is_peak = row["total_complaints"] == monthly["total_complaints"].max()
    peak_note = " It is also the highest monthly volume in the period." if is_peak else ""
    return f"""
        <div class="section-card" style="min-height:420px">
            <div class="insight-title">📣 &nbsp; Key Finding</div>
            <div class="insight-heading">
                Complaints increased {row['pct_change']:.0f}% in {month_label}
            </div>
            <div class="insight-copy">
                Complaint volume rose from <strong>{int(row['previous']):,}</strong>
                in {previous_label} to <strong>{int(row['total_complaints']):,}</strong>
                in {month_label}, the largest month-over-month jump in the data.{peak_note}
            </div>
        </div>
    """


def product_donut(height=360):
    if filtered_products.empty:
        empty_notice()
        return
    figure = px.pie(
        filtered_products,
        names="product",
        values="total_complaints",
        hole=0.62,
        title="Complaints by Product",
        color_discrete_sequence=[
            theme["blue"],
            "#0EA5E9",
            theme["teal"],
            "#F59E0B",
            theme["purple"],
            "#C026D3",
            "#60A5FA",
            "#94A3B8",
        ],
    )
    figure.update_traces(
        textinfo="none", hovertemplate="%{label}<br>%{value:,}<br>%{percent}"
    )
    figure.add_annotation(
        text=(
            f"<b>{int(filtered_products['total_complaints'].sum()):,}</b>"
            "<br><span style='font-size:12px'>complaints</span>"
        ),
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(color=theme["text"], size=17),
    )
    figure.update_layout(legend=dict(orientation="v", y=0.5, x=1.02))
    return figure, height


def issues_chart(top_n=6, height=360, key="issues"):
    chart_data = (
        filtered_issues.groupby("issue", as_index=False)["total_complaints"]
        .sum()
        .nlargest(top_n, "total_complaints")
        .sort_values("total_complaints")
    )
    if chart_data.empty:
        empty_notice()
        return
    figure = px.bar(
        chart_data,
        x="total_complaints",
        y="issue",
        orientation="h",
        title=(
            "Top Complaint Issues"
            if selected_product == "All Products"
            else f"Top Issues: {selected_product}"
        ),
        text="total_complaints",
    )
    figure.update_traces(
        marker_color=theme["blue"],
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
    )
    figure.update_layout(xaxis_title=None, yaxis_title=None)
    show_chart(apply_chart_style(figure, height=height, show_legend=False), key)


def company_table(top_n=7, height=305):
    table = filtered_companies.nlargest(top_n, "total_complaints").copy()
    if table.empty:
        empty_notice()
        return
    table["timely_response_rate_pct"] = 100 - table["late_response_rate_pct"]
    table = table[
        ["company", "total_complaints", "timely_response_rate_pct", "late_response_rate_pct"]
    ].rename(
        columns={
            "company": "Company",
            "total_complaints": "Complaints",
            "timely_response_rate_pct": "Timely %",
            "late_response_rate_pct": "Late %",
        }
    )
    styled = table.style.format(
        {"Complaints": "{:,.0f}", "Timely %": "{:.1f}%", "Late %": "{:.1f}%"}
    )
    try:
        styled = styled.background_gradient(subset=["Late %"], cmap="Reds")
    except Exception:  # matplotlib is optional
        pass
    show_table(styled, height=height)


def state_map(height=390, key="state_map"):
    if filtered_states.empty:
        empty_notice()
        return
    figure = px.choropleth(
        filtered_states,
        locations="state",
        locationmode="USA-states",
        color="total_complaints",
        scope="usa",
        title="Complaints by State",
        color_continuous_scale=["#DBEAFE", theme["blue"]],
        hover_name="state",
        hover_data={"total_complaints": ":,", "late_response_rate_pct": ":.1f"},
        labels={"total_complaints": "Complaints", "late_response_rate_pct": "Late %"},
    )
    figure.update_geos(bgcolor=theme["surface"], lakecolor=theme["surface"])
    figure.update_layout(
        coloraxis_colorbar=dict(
            title="Complaints", tickfont=dict(color=theme["muted"]),
            title_font=dict(color=theme["muted"]),
        )
    )
    show_chart(apply_chart_style(figure, height=height, show_legend=False), key)


def top_states_chart(top_n=5, height=390, key="top_states"):
    chart_data = filtered_states.nlargest(top_n, "total_complaints").sort_values(
        "total_complaints"
    )
    if chart_data.empty:
        empty_notice()
        return
    figure = px.bar(
        chart_data,
        x="total_complaints",
        y="state",
        orientation="h",
        title=f"Top {top_n} States by Complaint Volume",
        text="total_complaints",
    )
    figure.update_traces(
        marker_color=theme["blue"],
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
    )
    figure.update_layout(xaxis_title=None, yaxis_title=None)
    show_chart(apply_chart_style(figure, height=height, show_legend=False), key)


def late_rate_chart(frame, label_col, title, top_n=8, height=390, key="late_rate"):
    chart_data = frame.nlargest(top_n, "late_response_rate_pct").sort_values(
        "late_response_rate_pct"
    )
    if chart_data.empty:
        empty_notice()
        return
    hover = [c for c in ["total_complaints", "late_responses"] if c in chart_data.columns]
    figure = px.bar(
        chart_data,
        x="late_response_rate_pct",
        y=label_col,
        orientation="h",
        title=title,
        text="late_response_rate_pct",
        hover_data=hover,
    )
    figure.update_traces(
        marker_color=theme["coral"],
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )
    figure.update_layout(xaxis_title=None, yaxis_title=None)
    show_chart(apply_chart_style(figure, height=height, show_legend=False), key)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def page_overview():
    render_kpis()

    trend_col, insight_col = st.columns([3.25, 1])
    with trend_col:
        if filtered_monthly.empty:
            empty_notice("Select at least one year to see the monthly trend.")
        else:
            show_chart(trend_figure(filtered_monthly), "overview_trend")
    with insight_col:
        st.markdown(key_finding_html(), unsafe_allow_html=True)

    product_col, issue_col, company_table_col = st.columns([1.12, 1.2, 1.35])
    with product_col:
        result = product_donut()
        if result:
            figure, height = result
            show_chart(apply_chart_style(figure, height=height), "overview_donut")
    with issue_col:
        issues_chart(key="overview_issues")
    with company_table_col:
        st.markdown("### Company Response Performance")
        company_table()
        st.button(
            "View all companies →",
            key="overview_to_companies",
            on_click=go_to,
            args=("Companies",),
        )

    map_col, states_col = st.columns([1.45, 1])
    with map_col:
        state_map(key="overview_map")
    with states_col:
        late_rate_chart(
            filtered_companies,
            "company",
            "Highest Late-Response Rates",
            key="overview_late",
        )


def page_trends():
    if filtered_monthly.empty:
        empty_notice("Select at least one year to see complaint trends.")
        return

    render_kpis()
    show_chart(trend_figure(filtered_monthly, height=430), "trends_main")

    left, right = st.columns(2)
    with left:
        yoy = filtered_monthly.copy()
        yoy["year"] = yoy["complaint_month"].dt.year.astype(str)
        yoy["month"] = yoy["complaint_month"].dt.month
        yoy["month_name"] = yoy["complaint_month"].dt.strftime("%b")
        yoy = yoy.sort_values("month")
        figure = px.line(
            yoy,
            x="month_name",
            y="total_complaints",
            color="year",
            markers=True,
            title="Year-over-Year Comparison",
            category_orders={
                "month_name": [
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                ]
            },
            color_discrete_sequence=[
                theme["blue"], theme["teal"], theme["coral"], theme["purple"],
            ],
        )
        figure.update_layout(xaxis_title=None, yaxis_title=None, legend_title_text="")
        show_chart(apply_chart_style(figure, height=380), "trends_yoy")

    with right:
        mom = monthly.copy()
        mom["change"] = mom["total_complaints"].pct_change() * 100
        mom = mom[mom["complaint_month"].dt.year.isin(selected_years)].dropna(
            subset=["change"]
        )
        figure = px.bar(
            mom,
            x="complaint_month",
            y="change",
            title="Month-over-Month Change (%)",
        )
        figure.update_traces(
            marker_color=[
                theme["teal"] if value >= 0 else theme["coral"] for value in mom["change"]
            ]
        )
        figure.update_layout(xaxis_title=None, yaxis_title=None)
        show_chart(apply_chart_style(figure, height=380, show_legend=False), "trends_mom")

    table = filtered_monthly.copy()
    table["complaint_month"] = table["complaint_month"].dt.strftime("%Y-%m")
    table = table.rename(
        columns={
            "complaint_month": "Month",
            "total_complaints": "Complaints",
            "three_month_moving_average": "3-Month Avg",
        }
    )
    st.markdown("### Monthly Data")
    show_table(table, height=300)
    st.download_button(
        "⬇ Download monthly data (CSV)",
        table.to_csv(index=False).encode("utf-8"),
        file_name="monthly_complaints.csv",
        mime="text/csv",
    )


def page_products():
    render_kpis()

    left, right = st.columns([1, 1.2])
    with left:
        result = product_donut(height=400)
        if result:
            figure, height = result
            show_chart(apply_chart_style(figure, height=height), "products_donut")
    with right:
        if filtered_products.empty:
            empty_notice()
        else:
            chart_data = filtered_products.sort_values("total_complaints")
            figure = px.bar(
                chart_data,
                x="total_complaints",
                y="product",
                orientation="h",
                title="Complaint Volume by Product",
                text="total_complaints",
            )
            figure.update_traces(
                marker_color=theme["blue"],
                texttemplate="%{text:,.0f}",
                textposition="outside",
                cliponaxis=False,
            )
            figure.update_layout(xaxis_title=None, yaxis_title=None)
            show_chart(
                apply_chart_style(figure, height=400, show_legend=False), "products_bar"
            )

    issues_col, response_col = st.columns(2)
    with issues_col:
        issues_chart(top_n=10, height=420, key="products_issues")
    with response_col:
        if "product" in filtered_responses.columns and not filtered_responses.empty:
            chart_data = filtered_responses.sort_values("timely_response_rate_pct")
            figure = px.bar(
                chart_data,
                x="timely_response_rate_pct",
                y="product",
                orientation="h",
                title="Timely Response Rate by Product",
                text="timely_response_rate_pct",
            )
            figure.update_traces(
                marker_color=theme["teal"],
                texttemplate="%{text:.1f}%",
                textposition="outside",
                cliponaxis=False,
            )
            figure.update_layout(xaxis_title=None, yaxis_title=None)
            figure.update_xaxes(range=[0, 105])
            show_chart(
                apply_chart_style(figure, height=420, show_legend=False), "products_timely"
            )
        else:
            empty_notice("No response data for the selected product.")

    st.markdown("### Product Summary")
    show_table(
        filtered_products.rename(
            columns={
                "product": "Product",
                "total_complaints": "Complaints",
                "percentage_of_all_complaints": "% of All",
                "complaint_rank": "Rank",
            }
        ),
        height=300,
    )


def page_companies():
    render_kpis()

    min_complaints = st.slider(
        "Minimum complaints per company (hides very small companies from the rankings)",
        min_value=0,
        max_value=int(max(companies["total_complaints"].max(), 1)),
        value=0,
        step=100,
    )
    pool = filtered_companies[filtered_companies["total_complaints"] >= min_complaints]

    left, right = st.columns(2)
    with left:
        chart_data = pool.nlargest(10, "total_complaints").sort_values("total_complaints")
        if chart_data.empty:
            empty_notice()
        else:
            figure = px.bar(
                chart_data,
                x="total_complaints",
                y="company",
                orientation="h",
                title="Companies with the Most Complaints",
                text="total_complaints",
            )
            figure.update_traces(
                marker_color=theme["blue"],
                texttemplate="%{text:,.0f}",
                textposition="outside",
                cliponaxis=False,
            )
            figure.update_layout(xaxis_title=None, yaxis_title=None)
            show_chart(
                apply_chart_style(figure, height=420, show_legend=False), "companies_volume"
            )
    with right:
        late_rate_chart(
            pool, "company", "Highest Late-Response Rates", top_n=10, height=420,
            key="companies_late",
        )

    if not pool.empty:
        figure = px.scatter(
            pool,
            x="total_complaints",
            y="late_response_rate_pct",
            hover_name="company",
            title="Complaint Volume vs Late-Response Rate",
            labels={
                "total_complaints": "Complaints",
                "late_response_rate_pct": "Late %",
            },
        )
        figure.update_traces(marker=dict(color=theme["purple"], size=10, opacity=0.8))
        show_chart(apply_chart_style(figure, height=400, show_legend=False), "companies_scatter")

    st.markdown("### Company Response Performance")
    table = pool.sort_values("total_complaints", ascending=False).copy()
    table["timely_response_rate_pct"] = 100 - table["late_response_rate_pct"]
    show_table(
        table[
            ["company", "total_complaints", "late_responses",
             "timely_response_rate_pct", "late_response_rate_pct"]
        ].rename(
            columns={
                "company": "Company",
                "total_complaints": "Complaints",
                "late_responses": "Late Responses",
                "timely_response_rate_pct": "Timely %",
                "late_response_rate_pct": "Late %",
            }
        ),
        height=320,
    )


def page_geography():
    render_kpis()

    map_col, bar_col = st.columns([1.45, 1])
    with map_col:
        state_map(height=430, key="geo_map")
    with bar_col:
        top_states_chart(top_n=10, height=430, key="geo_top")

    left, right = st.columns(2)
    with left:
        min_state = st.slider(
            "Minimum complaints per state (for late-response ranking)",
            min_value=0,
            max_value=int(max(states["total_complaints"].max(), 1)),
            value=0,
            step=100,
        )
        late_rate_chart(
            filtered_states[filtered_states["total_complaints"] >= min_state],
            "state",
            "Highest Late-Response Rates by State",
            top_n=10,
            height=400,
            key="geo_late",
        )
    with right:
        st.markdown("### State Summary")
        show_table(
            filtered_states.sort_values("total_complaints", ascending=False).rename(
                columns={
                    "state": "State",
                    "total_complaints": "Complaints",
                    "percentage_of_all_complaints": "% of All",
                    "late_responses": "Late Responses",
                    "late_response_rate_pct": "Late %",
                }
            ),
            height=400,
        )
    st.caption("Complaint volume is not adjusted for state population.")


def page_data_quality():
    st.markdown("### Source file checks")
    rows = []
    for name, frame in data.items():
        rows.append(
            {
                "File": name,
                "Rows": len(frame),
                "Columns": frame.shape[1],
                "Missing values": int(frame.isna().sum().sum()),
                "Duplicate rows": int(frame.duplicated().sum()),
            }
        )
    show_table(pd.DataFrame(rows))

    st.markdown("### Cross-file reconciliation")
    totals = {
        "Monthly trend": monthly["total_complaints"].sum(),
        "Product summary": products["total_complaints"].sum(),
        "State summary": states["total_complaints"].sum(),
        "Company performance": companies["total_complaints"].sum(),
        "Product response performance": responses["total_complaints"].sum(),
        "Top product issues": issues["total_complaints"].sum(),
    }
    reference = totals["Product summary"]
    reconcile = pd.DataFrame(
        {
            "Source": list(totals.keys()),
            "Total complaints": [int(v) for v in totals.values()],
            "Difference vs product summary": [int(v - reference) for v in totals.values()],
        }
    )
    reconcile["Status"] = reconcile["Difference vs product summary"].apply(
        lambda diff: "✓ Match" if diff == 0 else "ℹ Differs"
    )
    show_table(reconcile)
    st.caption(
        "Company, state and issue files can legitimately differ from the full total "
        "when they only list top entries or exclude records with a missing value."
    )

    st.markdown("### Response consistency")
    if {"timely_responses", "late_responses", "total_complaints"}.issubset(responses.columns):
        mismatch = (
            responses["timely_responses"] + responses["late_responses"]
            != responses["total_complaints"]
        ).sum()
        if mismatch == 0:
            st.success("Timely + late responses equal total complaints for every product.")
        else:
            st.warning(f"{mismatch} product row(s) where timely + late ≠ total complaints.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Records analyzed", f"{total_records:,}")
    c2.metric("Analysis period", f"{period_start} – {period_end}")
    c3.metric("Months covered", f"{len(monthly)}")

    with st.expander("Methodology and data limitations", expanded=True):
        st.markdown(
            f"""
            - Source: Consumer Financial Protection Bureau complaint database.
            - Analysis period: {period_start} through {period_end}.
            - PostgreSQL was used for cleaning, validation and business analysis.
            - Each filter applies to the summary dataset that contains that dimension.
            - Complaint volume is not adjusted for customer base or state population.
            - A submitted complaint does not automatically establish wrongdoing.
            """
        )


PAGE_RENDERERS = {
    "Overview": page_overview,
    "Complaint Trends": page_trends,
    "Products": page_products,
    "Companies": page_companies,
    "Geography": page_geography,
    "Data Quality": page_data_quality,
}

PAGE_RENDERERS[page]()

if page != "Data Quality":
    with st.expander("Methodology and data limitations"):
        st.markdown(
            f"""
            - Source: Consumer Financial Protection Bureau complaint database.
            - Analysis period: {period_start} through {period_end}.
            - PostgreSQL was used for cleaning, validation and business analysis.
            - Each filter applies to the summary dataset that contains that dimension.
            - Complaint volume is not adjusted for customer base or state population.
            - A submitted complaint does not automatically establish wrongdoing.
            """
        )

st.markdown(
    '<div class="footer">Built with PostgreSQL, Python, Pandas, Plotly and Streamlit</div>',
    unsafe_allow_html=True,
)