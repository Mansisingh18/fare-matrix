"""
FARE MATRIX — Business Dashboard
Run: streamlit run dashboard.py
"""

import os
import json
import glob
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="FARE MATRIX",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; }
[data-testid="stMetricLabel"] { font-size: 13px; color: #666; }
.stDataFrame { border-radius: 8px; }
h1 { font-family: monospace; letter-spacing: 0.05em; }
</style>
""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

BOARD_LABELS = {
    "RO": "Room Only",
    "BB": "Bed & Breakfast",
    "HB": "Half Board",
    "FB": "Full Board",
    "AI": "All Inclusive",
}


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    json_path = os.path.join(DATA_DIR, "latest.json")
    if not os.path.exists(json_path):
        return pd.DataFrame()
    with open(json_path) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["check_in"]  = pd.to_datetime(df["check_in"])
    df["check_out"] = pd.to_datetime(df["check_out"])
    df["board_label"] = df["board_basis"].map(BOARD_LABELS).fillna(df["board_basis"])
    return df


# ── Header ────────────────────────────────────────────────────────────────────
st.title("✈️ FARE MATRIX")
st.caption("Hotel Price Intelligence Dashboard — Bedsonline + Acerooms")

df = load_data()

if df.empty:
    st.warning(
        "No data loaded yet. Run `python main.py` first to fetch prices, "
        "then refresh this page.",
        icon="⚠️",
    )
    st.stop()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

    # Star rating
    stars_in_data = df["stars"].unique() if "stars" in df.columns else []
    all_stars = sorted(
        [s for s in stars_in_data if s != "N/A"],
        key=lambda x: int(x.replace("★", "")),
        reverse=True,
    )
    if "N/A" in stars_in_data:
        all_stars.append("N/A")

    selected_stars = st.multiselect(
        "Star Rating",
        options=all_stars,
        default=all_stars,
    )

    # Board basis
    all_boards  = [b for b in ["RO", "BB", "HB", "FB", "AI"] if b in df["board_basis"].unique()]
    board_labels = {b: BOARD_LABELS.get(b, b) for b in all_boards}
    selected_boards = st.multiselect(
        "Board Basis",
        options=all_boards,
        format_func=lambda b: board_labels[b],
        default=all_boards,
    )

    # Night durations
    all_nights = sorted(df["nights"].unique().tolist())
    selected_nights = st.multiselect(
        "Night Duration",
        options=all_nights,
        format_func=lambda n: f"{int(n)} Nights",
        default=all_nights,
    )

    # Date range
    min_date = df["check_in"].min().date()
    max_date = df["check_in"].max().date()
    date_range = st.date_input(
        "Check-in Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Price range
    min_price = float(df["price_gbp"].min())
    max_price = float(df["price_gbp"].max())
    price_range = st.slider(
        "Max Price (£)",
        min_value=int(min_price),
        max_value=int(max_price),
        value=int(max_price),
        step=10,
    )

    # Source
    all_sources = df["source"].unique().tolist()
    selected_sources = st.multiselect(
        "Source",
        options=all_sources,
        default=all_sources,
    )

    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Apply filters ─────────────────────────────────────────────────────────────
fdf = df.copy()
fdf = fdf[fdf["stars"].isin(selected_stars)]
fdf = fdf[fdf["board_basis"].isin(selected_boards)]
fdf = fdf[fdf["nights"].isin(selected_nights)]
fdf = fdf[fdf["price_gbp"] <= price_range]
fdf = fdf[fdf["source"].isin(selected_sources)]

if len(date_range) == 2:
    fdf = fdf[
        (fdf["check_in"].dt.date >= date_range[0]) &
        (fdf["check_in"].dt.date <= date_range[1])
    ]

# ── KPI cards ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Rates", f"{len(fdf):,}")
with col2:
    st.metric("Hotels", fdf["hotel_name"].nunique() if not fdf.empty else 0)
with col3:
    st.metric("Cheapest Rate", f"£{fdf['price_gbp'].min():.0f}" if not fdf.empty else "—")
with col4:
    if not fdf.empty:
        best_idx  = fdf["price_gbp"].idxmin()
        best_date = fdf.loc[best_idx, "check_in"].strftime("%d %b")
        st.metric("Best Date", best_date)
    else:
        st.metric("Best Date", "—")
with col5:
    st.metric("Avg Price", f"£{fdf['price_gbp'].mean():.0f}" if not fdf.empty else "—")

st.divider()

if fdf.empty:
    st.info("No results match the current filters. Try widening your selection.")
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_overview, tab_hotels, tab_calendar, tab_compare, tab_raw = st.tabs([
    "📊 Overview", "🏨 By Hotel", "📅 Price Calendar", "⚖️ Compare", "📋 Raw Data"
])

# ─── Overview ─────────────────────────────────────────────────────────────────
with tab_overview:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Cheapest by Star Rating")
        if not fdf.empty:
            best_by_star = (
                fdf.groupby("stars")["price_gbp"]
                .min()
                .reset_index()
                .rename(columns={"stars": "Stars", "price_gbp": "Cheapest (£)"})
                .sort_values("Stars")
            )
            best_by_star["Cheapest (£)"] = best_by_star["Cheapest (£)"].apply(lambda x: f"£{x:.2f}")
            st.dataframe(best_by_star, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("Cheapest by Board Basis")
        if not fdf.empty:
            best_by_board = (
                fdf.groupby("board_label")["price_gbp"]
                .min()
                .reset_index()
                .rename(columns={"board_label": "Board", "price_gbp": "Cheapest (£)"})
                .sort_values("Cheapest (£)")
            )
            best_by_board["Cheapest (£)"] = best_by_board["Cheapest (£)"].apply(lambda x: f"£{x:.2f}")
            st.dataframe(best_by_board, use_container_width=True, hide_index=True)

    st.subheader("Price Distribution by Source")
    chart_data = fdf.groupby(["source", "board_label"])["price_gbp"].mean().reset_index()
    pivot = chart_data.pivot(index="board_label", columns="source", values="price_gbp")
    st.bar_chart(pivot)

# ─── By Hotel ─────────────────────────────────────────────────────────────────
with tab_hotels:
    st.subheader("All Hotels — Min / Avg / Max Price")
    hotel_summary = (
        fdf.groupby(["hotel_name", "stars", "board_label"])["price_gbp"]
        .agg(["min", "mean", "max", "count"])
        .reset_index()
        .rename(columns={
            "hotel_name":  "Hotel",
            "stars":       "Stars",
            "board_label": "Board",
            "min":         "Min (£)",
            "mean":        "Avg (£)",
            "max":         "Max (£)",
            "count":       "Rates",
        })
        .sort_values(["Stars", "Min (£)"], ascending=[False, True])
    )
    for col in ["Min (£)", "Avg (£)", "Max (£)"]:
        hotel_summary[col] = hotel_summary[col].apply(lambda x: f"£{x:.2f}")

    st.dataframe(hotel_summary, use_container_width=True, hide_index=True)

# ─── Price Calendar ───────────────────────────────────────────────────────────
with tab_calendar:
    st.subheader("Cheapest Price by Date")

    cal_star   = st.selectbox("Star Rating", options=["All"] + all_stars, key="cal_star")
    cal_board  = st.selectbox("Board Basis", options=all_boards,
                               format_func=lambda b: BOARD_LABELS.get(b, b), key="cal_board")
    cal_nights = st.selectbox("Nights", options=all_nights,
                               format_func=lambda n: f"{int(n)} Nights", key="cal_nights")

    cal_df = fdf[(fdf["board_basis"] == cal_board) & (fdf["nights"] == cal_nights)]
    if cal_star != "All":
        cal_df = cal_df[cal_df["stars"] == cal_star]

    if not cal_df.empty:
        daily = (
            cal_df.groupby("check_in")["price_gbp"]
            .min()
            .reset_index()
            .rename(columns={"check_in": "Date", "price_gbp": "Cheapest (£)"})
            .set_index("Date")
        )
        st.line_chart(daily)

        # Table view
        daily_table = daily.copy()
        daily_table.index = daily_table.index.strftime("%d %b %Y")
        daily_table["Cheapest (£)"] = daily_table["Cheapest (£)"].apply(lambda x: f"£{x:.2f}")
        st.dataframe(daily_table, use_container_width=True)
    else:
        st.info("No data for this combination.")

# ─── Compare ─────────────────────────────────────────────────────────────────
with tab_compare:
    st.subheader("Compare Hotels Side by Side")

    all_hotel_names = sorted(fdf["hotel_name"].unique().tolist())
    selected_hotels = st.multiselect(
        "Select hotels to compare",
        options=all_hotel_names,
        default=all_hotel_names[:3] if len(all_hotel_names) >= 3 else all_hotel_names,
    )

    if selected_hotels:
        cmp_df = fdf[fdf["hotel_name"].isin(selected_hotels)]
        pivot  = cmp_df.groupby(["hotel_name", "board_label"])["price_gbp"].min().unstack(fill_value=None)
        pivot.columns.name = None
        pivot.index.name   = "Hotel"
        for col in pivot.columns:
            pivot[col] = pivot[col].apply(lambda x: f"£{x:.2f}" if pd.notna(x) else "—")
        st.dataframe(pivot, use_container_width=True)

# ─── Raw Data ─────────────────────────────────────────────────────────────────
with tab_raw:
    st.subheader(f"Raw Data — {len(fdf):,} records")

    display_cols = ["hotel_name", "stars", "check_in", "nights",
                    "board_label", "price_gbp", "source"]
    available    = [c for c in display_cols if c in fdf.columns]
    show         = fdf[available].copy()
    show["check_in"]  = show["check_in"].dt.strftime("%d %b %Y")
    show["price_gbp"] = show["price_gbp"].apply(lambda x: f"£{x:.2f}")
    show = show.rename(columns={
        "hotel_name":  "Hotel",
        "stars":       "Stars",
        "check_in":    "Check-in",
        "nights":      "Nights",
        "board_label": "Board",
        "price_gbp":   "Price",
        "source":      "Source",
    })

    st.dataframe(show, use_container_width=True, hide_index=True)

    csv = fdf.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name="fare_matrix_export.csv",
        mime="text/csv",
        use_container_width=True,
    )
