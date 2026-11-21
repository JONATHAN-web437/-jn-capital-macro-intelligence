import streamlit as st
import pandas as pd
import re
import textwrap
from datetime import datetime

from modules.data import (
    load_dashboard_data,
    load_yield_curve_history,
    calculate_yoy_inflation,
    fred_historical,
    calculate_currency_strength,
    load_fed_monetary_policy_feed,
    calculate_fundamental_score,
    classify_fundamental_indicator,
    calculate_fed_policy_bias,
        load_cot_market_data,
    calculate_cot_positioning,
    load_fed_policy_history,
    load_fomc_statement_history,
)
from modules.ui import apply_theme, metric_card


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="JN Capital | Macro Intelligence",
    page_icon="â—†",
    layout="wide"
)

apply_theme()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.markdown("## â—† JN CAPITAL")
st.sidebar.caption("MACRO INTELLIGENCE")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Overview",
        "Economic Data",
        "Inflation Dashboard",
        "Economic Calendar",
        "Live News & Market Intelligence",
        "Labour Market Dashboard",
        "USD & Currency Intelligence",
        "Federal Reserve Intelligence",
        "Asset Scorecard",
        "Research & Sources",
        "System Status"
    ]
)
st.sidebar.markdown("---")
st.sidebar.caption("LOCAL RESEARCH TERMINAL â€¢ V1")
st.sidebar.caption("Free-source architecture")
st.sidebar.markdown("---")

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.sidebar.markdown("---")

if page == "Overview":

    # ==========================================
    # JN CAPITAL OFFICIAL LOGO
    # ==========================================

    logo_path = os.path.join(
        BASE_DIR,
        "jn_capital_banner.png"
    )

    if os.path.exists(logo_path):

        left, center, right = st.columns([1, 2, 1])

        with center:

            st.image(
                logo_path,
                width=190
            )

    st.markdown("---")

    # --------------------------------------------------
    # LOAD ECONOMIC DATA
    # --------------------------------------------------

    data = load_dashboard_data()
    yield_history, yield_error = load_yield_curve_history(years=2)
    st.sidebar.markdown("---")

    if data.get("configured"):
        st.sidebar.success("FRED: Connected")
    else:
        st.sidebar.error("FRED: Not Connected")


    # --------------------------------------------------
    # HELPER FUNCTION
    # --------------------------------------------------

    def number(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


    # --------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------

    if page == "Overview":

        st.markdown("# Macro Intelligence")

        st.markdown(
            "**Cross-asset research â€¢ Economic monitoring â€¢ Macro context**"
        )

        st.caption(
            f"Dashboard refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (local)"
        )

        st.markdown("---")

        # MAIN ECONOMIC INDICATORS

        a, b, c, d = st.columns(4)

        metric_card(
            a,
            "US 10Y Treasury",
            f"{data.get('10y', 'â€”')}%",
            "FRED: DGS10"
        )

        metric_card(
            b,
            "US 2Y Treasury",
            f"{data.get('2y', 'â€”')}%",
            "FRED: DGS2"
        )

        metric_card(
            c,
            "Fed Funds Rate",
            f"{data.get('fed', 'â€”')}%",
            "FRED: FEDFUNDS"
        )

        metric_card(
            d,
            "US CPI",
            data.get("cpi", "â€”"),
            "FRED: CPIAUCSL"
        )

        st.markdown("---")

        # TREASURY YIELD SPREAD

        st.subheader("Treasury Yield Curve")

        ten_year = number(data.get("10y"))
        two_year = number(data.get("2y"))

        if ten_year is not None and two_year is not None:

            spread = ten_year - two_year

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "10Y - 2Y Yield Spread",
                    f"{spread * 100:.0f} basis points"
                )

            with col2:
                if spread > 0:
                    st.success("Yield curve: Positively sloped")
                elif spread < 0:
                    st.warning("Yield curve: Inverted")
                else:
                    st.info("Yield curve: Approximately flat")

        else:
            st.warning("Treasury spread unavailable.")

        st.markdown("---")
        # HISTORICAL TREASURY YIELD CURVE

        st.subheader("Historical Treasury Yield Curve")

        if yield_error:

            st.warning(f"Historical yield data unavailable: {yield_error}")

        elif not yield_history.empty:

            chart_data = yield_history.set_index("date")

            # Historical Treasury yields

            st.markdown("#### US 10-Year vs 2-Year Treasury Yields")

            st.line_chart(
                chart_data[["10Y", "2Y"]],
                height=350
            )

            # Historical yield spread

            st.markdown("#### Historical 10Yâ€“2Y Yield Spread")

            st.line_chart(
                chart_data[["Spread_bps"]],
                height=300
            )

            # Current curve analysis

            latest_spread = chart_data["Spread_bps"].iloc[-1]

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Current Yield Spread",
                    f"{latest_spread:.1f} bps"
                )

            with col2:

                if latest_spread > 0:
                    st.success("Curve: Positively sloped")

                elif latest_spread < 0:
                    st.error("Curve: Inverted")

                else:
                    st.info("Curve: Flat")

            with col3:

                if len(chart_data) >= 6:

                    previous = chart_data.iloc[-6]
                    latest = chart_data.iloc[-1]

                    change_10y = (latest["10Y"] - previous["10Y"]) * 100
                    change_2y = (latest["2Y"] - previous["2Y"]) * 100

                    movement = latest_spread - previous["Spread_bps"]

                    if movement > 1:

                        st.success("Curve: Steepening")

                        if change_10y > 0 and change_10y > change_2y:
                            st.write("Classification: Bear steepening")

                        elif change_2y < 0 and change_2y < change_10y:
                            st.write("Classification: Bull steepening")

                        else:
                            st.write("Classification: Mixed steepening")

                    elif movement < -1:

                        st.warning("Curve: Flattening")

                        if change_2y > 0 and change_2y > change_10y:
                            st.write("Classification: Bear flattening")

                        elif change_10y < 0 and change_10y < change_2y:
                            st.write("Classification: Bull flattening")

                        else:
                            st.write("Classification: Mixed flattening")

                    else:

                        st.info("Curve: Relatively unchanged")

                else:

                    st.info("Insufficient historical observations")





            st.caption(
                "Steepening/flattening compares the latest spread "
                "with its level five trading observations earlier."
            )

        else:

            st.warning("No historical Treasury observations available.")

        st.markdown("---")
        # ECONOMIC OBSERVATIONS

        st.subheader("Latest Economic Observations")

        table = data.get("table", [])

        if table:
            st.dataframe(
                table,
                width="stretch",
                hide_index=True
            )
        else:
            st.warning("No economic observations available.")

        st.markdown("---")

        # RESEARCH WORKFLOW

        left, right = st.columns([1.5, 1])

        with left:

            st.subheader("Macro Research Framework")

            st.markdown("""
            1. Review the latest economic data and publication dates.
            2. Identify the direction and momentum of macro indicators.
            3. Assess potential transmission to yields, FX, commodities and equities.
            4. Develop market scenarios and identify invalidation conditions.
            """)

        with right:

            st.subheader("Research Coverage")

            st.markdown("""
            - **Rates:** Treasury curve and policy rates
            - **Inflation:** CPI and PCE
            - **Labour:** Payrolls and unemployment
            - **Positioning:** CFTC Commitment of Traders
            - **Commodities:** Gold, energy and metals
            - **Currencies:** USD and major forex pairs
            """)


# --------------------------------------------------
# ECONOMIC DATA
# --------------------------------------------------

elif page == "Economic Data":

    data = load_dashboard_data()

    st.markdown("# Economic Data")

    st.caption("Federal Reserve Economic Data â€¢ FRED")

    st.markdown("---")

    st.subheader("Latest Available Observations")

    table = data.get("table", [])
    if table:

        st.dataframe(
            table,
            width="stretch",
            hide_index=True
        )

    else:

        st.warning("Economic data is currently unavailable.")

    st.info(
        "Observation dates represent the periods measured, "
        "not necessarily the dates on which the data was published."
    )


# --------------------------------------------------
# RESEARCH AND SOURCES
# --------------------------------------------------
elif page == "USD & Currency Intelligence":

    st.markdown("# USD & Currency Intelligence")

    st.caption("FOREX â€¢ CURRENCY STRENGTH â€¢ CROSS-ASSET ANALYSIS")

    st.markdown("---")

    st.info(
        "Monitor major currency pairs, currency crosses, "
        "the US Dollar Index, gold and silver."
    )

    st.markdown("---")

    st.subheader("Major Currency Strength Overview")

    st.caption(
        "Relative currency performance across eight major currencies."
    )

    strength_period = st.selectbox(
        "Strength Measurement Period",
        ["1 Week", "1 Month", "3 Months"],
        index=1
    )

    strength_data = calculate_currency_strength(strength_period)

    if not strength_data.empty:

        st.dataframe(
            strength_data.style.format({
                "Strength (%)": "{:+.2f}%"
            }),
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")

        st.subheader("Currency Strength Comparison")

        chart_data = strength_data.set_index("Currency")

        st.bar_chart(
            chart_data,
            y="Strength (%)",
            horizontal=True
        )


    else:

        st.warning(
            "Currency strength data is currently unavailable."
        )

    st.markdown("---")

    st.subheader("Market Coverage")

    st.markdown("### Major USD Pairs")

    major_pairs = [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
        "USDCAD", "AUDUSD", "NZDUSD"
    ]

    st.write(", ".join(major_pairs))

    st.markdown("### EUR Crosses")

    eur_crosses = [
        "EURGBP", "EURJPY", "EURCHF",
        "EURAUD", "EURCAD", "EURNZD"
    ]

    st.write(", ".join(eur_crosses))

    st.markdown("### GBP Crosses")

    gbp_crosses = [
        "GBPJPY", "GBPCHF", "GBPAUD",
        "GBPCAD", "GBPNZD"
    ]

    st.write(", ".join(gbp_crosses))

    st.markdown("### Other Currency Crosses")

    other_crosses = [
        "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF",
        "NZDJPY", "NZDCAD", "NZDCHF",
        "CADJPY", "CADCHF", "CHFJPY"
    ]

    st.write(", ".join(other_crosses))

    st.markdown("### Other Markets")

    st.write("DXY â€¢ XAUUSD â€¢ XAGUSD")

    st.markdown("---")

elif page == "Federal Reserve Intelligence":

    st.markdown("# Federal Reserve Intelligence")

    st.caption(
        "OFFICIAL FEDERAL RESERVE UPDATES â€¢ MONETARY POLICY â€¢ FOMC"
    )

    st.markdown("---")

    st.info(
        "Monitoring official Federal Reserve monetary-policy "
        "announcements and FOMC publications."
    )
    st.subheader("Federal Reserve Visual Gallery")

    st.components.v1.html(
        """
        <div style="position:relative;width:100%;height:360px;overflow:hidden;border-radius:12px;">

            <img src="https://www.federalreserve.gov/aboutthefed/aroundtheboard/DSC_2627-pw.jpg"
            class="fedslide">

            <img src="https://www.federalreserve.gov/aboutthefed/aroundtheboard/DSC_1029-pw.jpg"
            class="fedslide">

            <style>
            .fedslide {
                position:absolute;
                width:100%;
                height:100%;
                object-fit:cover;
                opacity:0;
                animation: slideshow 10s infinite;
            }

            .fedslide:nth-child(1) {
                animation-delay:0s;
            }

            .fedslide:nth-child(2) {
                animation-delay:5s;
            }

            @keyframes slideshow {
                0%, 45% {opacity:1;}
                50%, 95% {opacity:0;}
                100% {opacity:1;}
            }
            </style>

        </div>
        """,
        height=370
    )
    st.subheader("Latest Federal Reserve Publications")

    fed_data = load_fed_monetary_policy_feed()

    if not fed_data.empty:

        st.caption(
            f"{len(fed_data)} publications retrieved from the official "
            "Federal Reserve RSS feed."
        )

        for _, row in fed_data.iterrows():

            st.markdown(f"### {row['Title']}")

            st.caption(row["Date"])

            st.write(row["Description"])

            if row["Link"]:
                st.markdown(f"[Read official publication]({row['Link']})")

            st.markdown("---")

    else:

        st.warning(
            "Federal Reserve updates are currently unavailable. "
            "Please check your internet connection."
        )

        st.markdown("---")

    st.subheader("Official FOMC Rate Decisions")

    fomc_history = load_fomc_statement_history()

    if not fomc_history.empty:

        st.dataframe(
            fomc_history[
                ["Date", "Decision", "Decision Details"]
            ],
            hide_index=True,
            width="stretch"
        )

    else:

        st.warning("Official FOMC decision history is unavailable.")
    st.markdown("---")

    st.subheader("Historical Federal Funds Target Rate Decisions")

    policy_history = load_fed_policy_history()

    if not policy_history.empty:

        st.dataframe(
            policy_history,
            hide_index=True,
            width="stretch"
        )

    else:

        st.warning("Historical Fed policy data is currently unavailable.")
    st.subheader("Official Federal Reserve Resources")

    st.link_button(
        "FOMC Meeting Calendar",
        "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    )

    st.link_button(
        "FOMC Statements and Minutes",
        "https://www.federalreserve.gov/monetarypolicy/materials/"
    )

    st.markdown("---")
elif page == "Asset Scorecard":

    st.markdown("# JN Capital Asset Scorecard")

    st.caption(
        "MACROECONOMICS â€¢ TECHNICAL ANALYSIS â€¢ INSTITUTIONAL POSITIONING"
    )

    st.markdown("---")

    st.info(
        "Evaluate market conditions across multiple asset classes "
        "using fundamental, sentiment and technical analysis."
    )

    st.markdown("---")

    st.subheader("Select Market")

    asset = st.selectbox(
        "Choose an asset",
        [
            "XAUUSD",
            "XAGUSD",
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "USDCHF",
            "USDCAD",
            "AUDUSD",
            "NZDUSD",
            "US30",
            "NAS100",
            "SPX500",
            "BTCUSD"
        ]
    )

    st.markdown(f"### Analysis: {asset}")

    st.subheader("Fundamental Economic Indicators")

    fundamental_data = calculate_fundamental_score()

    fundamental_data["Fundamental Bias"] = fundamental_data.apply(
        lambda row: classify_fundamental_indicator(
            row["Indicator"],
            row["Latest Value"],
            "USD" if asset not in ["XAUUSD", "XAGUSD"] else "XAUUSD"
        ),
        axis=1
    )

    def color_fundamental_bias(value):

        if value == "Bullish":
            return "background-color: #198754; color: white"

        elif value == "Bearish":
            return "background-color: #dc3545; color: white"

        else:
            return "background-color: #0d6efd; color: white"


    styled_fundamental_data = fundamental_data.style.map(
        color_fundamental_bias,
        subset=["Fundamental Bias"]
    )

    st.dataframe(
        styled_fundamental_data,
        hide_index=True,
        width="stretch"
    )
    st.markdown("---")

    st.subheader("Federal Reserve Policy Bias")

    policy_asset = (
        "XAUUSD" if asset == "XAUUSD" else "USD"
    )

    fed_bias = calculate_fed_policy_bias(policy_asset)

    st.metric(
        "Latest Fed Policy Influence",
        fed_bias
    )
    st.markdown("---")
    # JN CAPITAL ASSETMETER

    st.markdown("---")

    st.subheader("JN CAPITAL ASSETMETER")

    st.caption(
        "MULTI-FACTOR MARKET BIAS & STRENGTH"
    )

    st.markdown("---")

       # -----------------------------------------

    # -----------------------------------------
    # -----------------------------------------
    # JN CAPITAL MULTI-TIMEFRAME ANALYSIS
    # -----------------------------------------

    from modules.data import calculate_multi_timeframe_analysis

    technical_result = calculate_multi_timeframe_analysis(
        symbol=asset
    )

    # -----------------------------------------
    # ASSETMETER COMPONENTS
    # -----------------------------------------

    assetmeter_components = st.columns(3)

    with assetmeter_components[0]:

        fundamental_meter = st.slider(
            "Macroeconomics",
            0, 100, 50,
            key="am_macro"
        )

    with assetmeter_components[1]:

        if technical_result is not None:

            technical_meter = technical_result["score"]

            st.metric(
                "Technical Analysis",
                f"{technical_meter}/100"
            )

            st.caption(
                f"Market Bias: {technical_result['bias']}"
            )

            st.caption(
                f"Alignment: {technical_result['alignment']}"
            )

            timeframe_results = technical_result["timeframes"]

            st.caption(
                f"D1: {timeframe_results['Daily']['score']}/100"
                f" | H4: {timeframe_results['H4']['score']}/100"
                f" | H1: {timeframe_results['H1']['score']}/100"
            )

            st.caption(
                f"RSI â€” D1: {timeframe_results['Daily']['rsi_condition']}"
                f" | H4: {timeframe_results['H4']['rsi_condition']}"
                f" | H1: {timeframe_results['H1']['rsi_condition']}"
            )

            st.caption(
                "Latest candles (UTC): "
                f"D1 {timeframe_results['Daily']['timestamp'].strftime('%d %b %H:%M')}"
                f" | H4 {timeframe_results['H4']['timestamp'].strftime('%d %b %H:%M')}"
                f" | H1 {timeframe_results['H1']['timestamp'].strftime('%d %b %H:%M')}"
            )

        else:

            technical_meter = None

            st.metric(
                "Technical Analysis",
                "Unavailable"
            )

            st.caption(
                "Insufficient market data for multi-timeframe analysis."
            )

    with assetmeter_components[2]:

        institutional_meter = st.slider(
            "Institutional Positioning",
            0, 100, 50,
            key="am_institutional"
        )

    # -----------------------------------------
    # OVERALL ASSETMETER CALCULATION
    # -----------------------------------------

    if technical_meter is not None:

        assetmeter_score = int(
            (
                fundamental_meter
                + technical_meter
                + institutional_meter
            ) / 3
        )

        if assetmeter_score >= 80:
            assetmeter_bias = "VERY BULLISH"

        elif assetmeter_score >= 60:
            assetmeter_bias = "BULLISH"

        elif assetmeter_score >= 41:
            assetmeter_bias = "NEUTRAL"

        elif assetmeter_score >= 21:
            assetmeter_bias = "BEARISH"

        else:
            assetmeter_bias = "VERY BEARISH"

        st.markdown(
            f"### OVERALL MARKET BIAS: {assetmeter_bias}"
        )

        st.metric(
            "JN CAPITAL ASSETMETER SCORE",
            f"{assetmeter_score}/100"
        )

    else:

        st.warning(
            "Assetmeter score unavailable because technical data "
            "could not be retrieved."
        )
    # -----------------------------------------
    # OVERALL ASSETMETER CALCULATION
    # -----------------------------------------

    if technical_meter is not None:

        assetmeter_score = int(
            (
                fundamental_meter
                + technical_meter
                + institutional_meter
            ) / 3
        )

        if assetmeter_score >= 80:
            assetmeter_bias = "VERY BULLISH"

        elif assetmeter_score >= 60:
            assetmeter_bias = "BULLISH"

        elif assetmeter_score >= 41:
            assetmeter_bias = "NEUTRAL"

        elif assetmeter_score >= 21:
            assetmeter_bias = "BEARISH"

        else:
            assetmeter_bias = "VERY BEARISH"

        st.markdown(
            f"### OVERALL MARKET BIAS: {assetmeter_bias}"
        )

        st.metric(
            "JN CAPITAL ASSETMETER SCORE",
            f"{assetmeter_score}/100"
        )

    else:

        st.warning(
            "Assetmeter score unavailable because technical market data "
            "could not be retrieved. No substitute score has been assumed."
        )

        # ASSETMETER CIRCULAR GAUGE

    gauge_color = (
        "#16C784" if assetmeter_score >= 61
        else "#D4AF37" if assetmeter_score >= 50
        else "#EA3943"
    )

    circumference = 440
    progress_value = assetmeter_score * 4.4

    st.components.v1.html(
        textwrap.dedent(
            f"""
        <div style="
            display:flex;
            justify-content:center;
            padding:20px;
        ">
            <div style="position:relative;width:190px;height:190px;">

                <svg width="190" height="190"
                     viewBox="0 0 190 190">

                    <circle
                        cx="95" cy="95" r="70"
                        stroke="#26364a"
                        stroke-width="13"
                        fill="none"
                    />

                    <circle
                        cx="95" cy="95" r="70"
                        stroke="{gauge_color}"
                        stroke-width="13"
                        fill="none"
                        stroke-linecap="round"
                        stroke-dasharray="{progress_value} {circumference}"
                        transform="rotate(-90 95 95)"
                    />

                </svg>

                <div style="
                    position:absolute;
                    top:50%;
                    left:50%;
                    transform:translate(-50%,-50%);
                    text-align:center;
                ">
                    <div style="
                        font-size:36px;
                        font-weight:700;
                        color:#ffffff;
                    ">{assetmeter_score}</div>

                    <div style="
                        font-size:12px;
                        color:#aab8c9;
                    ">/ 100</div>
                </div>
            </div>
        </div>
                """),
        height=220
    )

    st.caption(
        "0 â€” VERY BEARISH | 50 â€” NEUTRAL | 100 â€” VERY BULLISH"
    )

    st.markdown("---")
    st.markdown("""
<style>
.cot-header {
    background: linear-gradient(110deg, #101827, #1c2940);
    border-left: 5px solid #D4AF37;
    border-radius: 10px;
    padding: 20px 24px;
    margin: 12px 0 18px 0;
}

.cot-header h2 {
    color: #D4AF37;
    font-size: 25px;
    margin: 0;
    font-weight: 700;
}

.cot-header p {
    color: #b8c3d6;
    font-size: 12px;
    letter-spacing: 2px;
    margin: 8px 0 0 0;
}
</style>

<div class="cot-header">
    <h2>JN CAPITAL | Institutional Positioning</h2>
    <p>COMMITMENT OF TRADERS â€¢ MARKET SENTIMENT â€¢ POSITIONING INTELLIGENCE</p>
</div>
""", unsafe_allow_html=True)

    st.caption(
        "CFTC â€¢ COMMITMENT OF TRADERS â€¢ MANAGED MONEY"
    )

    if asset in ["XAUUSD", "XAGUSD"]:

        cot_keyword = "GOLD" if asset == "XAUUSD" else "SILVER"

        cot_data = load_cot_market_data(
            "72hh-3qpy",
            cot_keyword
        )

        cot_result = calculate_cot_positioning(cot_data)

        if cot_result:

            st.markdown(
                f"### {cot_keyword} Futures Positioning"
            )

            st.caption(
                f"Reporting date: {cot_result['Report Date']}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(145deg, #142337, #1c3048);
                    border: 1px solid #286b55;
                    border-radius: 12px;
                    padding: 20px;
                    min-height: 125px;
                ">
                    <div style="color:#aab8c9;font-size:13px;">
                        MANAGED MONEY LONG
                    </div>
                    <div style="color:#20c997;font-size:29px;
                                font-weight:700;margin-top:12px;">
                        {cot_result['Managed Money Long']:,}
                    </div>
                    <div style="color:#20c997;font-size:11px;">
                        LONG CONTRACTS
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(145deg, #142337, #1c3048);
                    border: 1px solid #853d48;
                    border-radius: 12px;
                    padding: 20px;
                    min-height: 125px;
                ">
                    <div style="color:#aab8c9;font-size:13px;">
                        MANAGED MONEY SHORT
                    </div>
                    <div style="color:#ff6474;font-size:29px;
                                font-weight:700;margin-top:12px;">
                        {cot_result['Managed Money Short']:,}
                    </div>
                    <div style="color:#ff6474;font-size:11px;">
                        SHORT CONTRACTS
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                net_position = cot_result['Net Position']

                net_color = (
                    "#20c997" if net_position > 0
                    else "#ff6474" if net_position < 0
                    else "#D4AF37"
                )

                st.markdown(f"""
                <div style="
                    background: linear-gradient(145deg, #142337, #1c3048);
                    border: 1px solid {net_color};
                    border-radius: 12px;
                    padding: 20px;
                    min-height: 125px;
                ">
                    <div style="color:#aab8c9;font-size:13px;">
                        NET POSITION
                    </div>
                    <div style="color:{net_color};font-size:29px;
                                font-weight:700;margin-top:12px;">
                        {net_position:+,}
                    </div>
                    <div style="color:{net_color};font-size:11px;">
                        NET CONTRACTS
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.metric(
                    "Managed Money Short",
                    f"{cot_result['Managed Money Short']:,}"
                )

            with col3:
                st.metric(
                    "Net Position",
                    f"{cot_result['Net Position']:+,}"
                )

            st.markdown("---")

            col4, col5 = st.columns(2)

            with col4:
                st.metric(
                    "Weekly Position Change",
                    (
                        f"{cot_result['Weekly Change']:+,}"
                        if cot_result["Weekly Change"] is not None
                        else "Unavailable"
                    )
                )

            with col5:
                st.metric(
                    "52-Week COT Index",
                    (
                        f"{cot_result['COT Index']:.1f}/100"
                        if cot_result["COT Index"] is not None
                        else "Insufficient data"
                    )
                )

            if cot_result["COT Index"] is not None:

                cot_index = cot_result["COT Index"]

                gauge_color = (
                    "#ff6474" if cot_index <= 40
                    else "#20c997" if cot_index >= 60
                    else "#D4AF37"
                )

                st.progress(cot_index / 100)

                st.caption(
                    f"POSITIONING STRENGTH: {cot_index:.1f}/100"
                )

                st.caption(
                    "0 â€” LOW        50 â€” MIDPOINT        100 â€” HIGH"
                )

            bias = cot_result["Institutional Bias"]

            if bias == "Bullish":
                st.success(
                    "INSTITUTIONAL POSITIONING: BULLISH"
                )

            elif bias == "Bearish":
                st.error(
                    "INSTITUTIONAL POSITIONING: BEARISH"
                )

            else:
                st.warning(
                    f"INSTITUTIONAL POSITIONING: {bias.upper()}"
                )

            st.markdown("#### Historical Institutional Positioning")

            history = cot_result["History"].set_index(
                "Report Date"
            )

            st.line_chart(
                history,
                height=300
            )

        else:
            st.warning(
                "No CFTC positioning data is currently available."
            )

    else:

        st.info(
            "CFTC positioning integration for this asset "
            "will be added in the next development stage."
        )

    st.caption(
        "Source: U.S. Commodity Futures Trading Commission (CFTC). "
        "Positions are reported weekly and are not live market data."
    )
elif page == "Research & Sources":
    st.markdown("# Research & Sources")

    st.markdown("""
    ### Data Source Principles

    - Prefer primary and official sources.
    - Preserve observation dates and measurement units.
    - Distinguish economic observations from market commentary.
    - Never fabricate consensus estimates or market prices.

    ### Integrated Providers

    - FRED â€“ Federal Reserve Economic Data

    ### Planned Integrations

    - BLS â€“ Bureau of Labor Statistics
    - BEA â€“ Bureau of Economic Analysis
    - CFTC â€“ Commitment of Traders
    - EIA â€“ Energy Information Administration
    - ECB â€“ European Central Bank
    - Other central banks
    """)


# --------------------------------------------------
# SYSTEM STATUS
# --------------------------------------------------

elif page == "Inflation Dashboard":

    import pandas as pd

    st.markdown("# Inflation Dashboard")

    st.caption("US INFLATION MONITOR â€¢ FRED DATA")

    st.markdown("---")

    # =====================================================
    # INFLATION DATA
    # =====================================================

    inflation_series = {
        "Headline CPI": "CPIAUCSL",
        "Core CPI": "CPILFESL",
        "Headline PCE": "PCEPI",
        "Core PCE": "PCEPILFE"
    }

    inflation_data = {}

    for name, series_id in inflation_series.items():

        inflation_data[name] = calculate_yoy_inflation(
            series_id,
            years=5
        )

    # =====================================================
    # LATEST INFLATION READINGS
    # =====================================================

    st.subheader("Latest Year-over-Year Inflation")

    columns = st.columns(4)

    for column, (name, df) in zip(columns, inflation_data.items()):

        with column:

            if not df.empty:

                latest = df["YoY Inflation (%)"].iloc[-1]

                previous = (
                    df["YoY Inflation (%)"].iloc[-2]
                    if len(df) >= 2 else None
                )

                delta = (
                    latest - previous
                    if previous is not None else None
                )

                st.metric(
                    label=name,
                    value=f"{latest:.2f}%",
                    delta=(
                        f"{delta:+.2f} percentage points"
                        if delta is not None else None
                    )
                )

            else:

                st.metric(
                    label=name,
                    value="Unavailable"
                )

    st.markdown("---")

    # =====================================================
    # COMBINED HISTORICAL INFLATION LINE GRAPH
    # =====================================================

    st.subheader("Historical Inflation Trends")

    st.caption(
        "Five-year comparison of headline and core inflation "
        "across CPI and PCE."
    )

    historical_chart = None

    for name, df in inflation_data.items():

        if not df.empty:

            chart_data = df[
                ["Date", "YoY Inflation (%)"]
            ].rename(
                columns={
                    "YoY Inflation (%)": name
                }
            )

            if historical_chart is None:

                historical_chart = chart_data

            else:

                historical_chart = historical_chart.merge(
                    chart_data,
                    on="Date",
                    how="outer"
                )

    if historical_chart is not None:

        historical_chart["Date"] = pd.to_datetime(
            historical_chart["Date"]
        )

        historical_chart = historical_chart.sort_values("Date")

        st.line_chart(
            historical_chart.set_index("Date"),
            x_label="Date",
            y_label="Year-over-Year Inflation (%)",
            height=450
        )

    else:

        st.warning("Historical inflation data is unavailable.")

    st.markdown("---")

    # =====================================================
    # CURRENT VS PREVIOUS INFLATION BAR CHART
    # =====================================================

    st.subheader("Current vs Previous Inflation")

    st.caption(
        "Compare the latest year-over-year inflation reading "
        "with the preceding monthly reading."
    )

    comparison_rows = []

    for name, df in inflation_data.items():

        if len(df) >= 2:

            latest = df.iloc[-1]

            previous = df.iloc[-2]

            comparison_rows.append({

                "Inflation Measure": name,

                "Current": round(
                    float(latest["YoY Inflation (%)"]), 2
                ),

                "Previous": round(
                    float(previous["YoY Inflation (%)"]), 2
                ),

                "Current Date": str(latest["Date"]),

                "Previous Date": str(previous["Date"]),

                "Change": round(
                    float(latest["YoY Inflation (%)"])
                    - float(previous["YoY Inflation (%)"]),
                    2
                )

            })

    if comparison_rows:

        comparison_df = pd.DataFrame(comparison_rows)

        bar_chart = comparison_df.set_index(
            "Inflation Measure"
        )[["Current", "Previous"]]

        st.bar_chart(
            bar_chart,
            stack=False,
            y_label="Inflation (%)",
            height=400
        )

        # -------------------------------------------------
        # DETAILED COMPARISON TABLE
        # -------------------------------------------------

        st.markdown("### Inflation Comparison Details")

        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "Not enough historical observations "
            "to calculate current versus previous inflation."
        )

    st.markdown("---")

    # =====================================================
    # INFLATION EXPLANATION
    # =====================================================

    st.info(
        "CPI measures consumer price inflation. PCE is the "
        "Federal Reserve's preferred inflation measure. "
        "Core CPI and Core PCE exclude food and energy. "
        "The charts use year-over-year inflation percentages, "
        "not raw price index values."
    )

elif page == "Economic Calendar":

    import requests
    import pandas as pd
    import re
    from datetime import datetime
    from zoneinfo import ZoneInfo

    st.markdown("# Economic Calendar")

    st.caption(
        "GLOBAL ECONOMIC RELEASES & MARKET INTELLIGENCE"
    )

    st.markdown("---")

    # ==========================================
    # SHOWMYTRADES LIVE ECONOMIC CALENDAR
    # ==========================================

    @st.cache_data(ttl=900)
    def load_economic_calendar():

        url = "https://showmytrades.com/api/public/calendar/v1"

        params = {
            "days": 30,
            "impact": "high,medium,low"
        }

        try:

            response = requests.get(
                url,
                params=params,
                timeout=25
            )

            response.raise_for_status()

            data = response.json()

            return data.get("events", []), None

        except Exception as e:

            return [], str(e)

    calendar_events, calendar_error = load_economic_calendar()

    # ==========================================
    # CONNECTION STATUS
    # ==========================================

    if calendar_error:

        st.error(
            "Economic Calendar connection failed."
        )

        st.code(calendar_error)

    elif calendar_events:

        st.success(
            f"Economic Calendar connected successfully â€” "
            f"{len(calendar_events)} events retrieved."
        )

    else:

        st.warning(
            "The calendar connected, but no events were returned."
        )

    # ==========================================
    # PROCESS LIVE EVENTS
    # ==========================================

    processed_events = []

    for event in calendar_events:

        try:

            utc_time = datetime.fromisoformat(
                event["time"].replace("Z", "+00:00")
            )

            local_time = utc_time.astimezone(
                ZoneInfo("Africa/Kampala")
            )

            actual = event.get("actual") or "Not released"

            forecast = event.get("forecast") or "Not available"

            previous = event.get("previous") or "Not available"

            status = event.get("status") or "Unknown"

            if actual != "Not released":

                status = "Released"

            processed_events.append({

                "Timestamp": utc_time,

                "Release Date (EAT)": local_time.strftime(
                    "%d %b %Y"
                ),

                "Release Time (EAT)": local_time.strftime(
                    "%H:%M"
                ),

                "Currency": event.get("currency", "N/A"),

                "Economic Event": event.get("title", "Unknown"),

                "Impact": str(
                    event.get("impact", "Unknown")
                ).upper(),

                "Forecast": forecast,

                "Previous": previous,

                "Actual": actual,

                "Status": status.replace("_", " ").title(),

                "Data Confidence": str(
                    event.get("confidence", "Not specified")
                ).replace("_", " ").title()

            })

        except Exception:

            continue

    # ==========================================
    # CALENDAR DASHBOARD
    # ==========================================

    if processed_events:

        df_calendar = pd.DataFrame(processed_events)

        df_calendar = df_calendar.sort_values(
            by="Timestamp"
        ).reset_index(drop=True)

        st.markdown("---")

        st.subheader("Economic Calendar Overview")

        total_events = len(df_calendar)

        high_events = len(
            df_calendar[
                df_calendar["Impact"] == "HIGH"
            ]
        )

        usd_events = len(
            df_calendar[
                df_calendar["Currency"] == "USD"
            ]
        )

        released_events = len(
            df_calendar[
                df_calendar["Status"] == "Released"
            ]
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Events",
            total_events
        )

        col2.metric(
            "High Impact",
            high_events
        )

        col3.metric(
            "USD Events",
            usd_events
        )

        col4.metric(
            "Released Events",
            released_events
        )

        st.markdown("---")

        # ==========================================
        # FILTERS
        # ==========================================

        st.subheader("Calendar Filters")

        col1, col2 = st.columns(2)

        available_currencies = sorted(
            df_calendar["Currency"].unique().tolist()
        )

        available_impacts = [
            impact
            for impact in ["HIGH", "MEDIUM", "LOW"]
            if impact in df_calendar["Impact"].unique()
        ]

        with col1:

            selected_currencies = st.multiselect(
                "Select Currencies",
                options=available_currencies,
                default=available_currencies
            )

        with col2:

            selected_impacts = st.multiselect(
                "Select Impact Levels",
                options=available_impacts,
                default=available_impacts
            )

        usd_only = st.checkbox(
            "Show USD events only",
            value=False
        )

        show_released = st.checkbox(
            "Include already released events",
            value=True
        )

        # ==========================================
        # APPLY FILTERS
        # ==========================================

        filtered_df = df_calendar[
            df_calendar["Currency"].isin(
                selected_currencies
            )
            &
            df_calendar["Impact"].isin(
                selected_impacts
            )
        ].copy()

        if usd_only:

            filtered_df = filtered_df[
                filtered_df["Currency"] == "USD"
            ]

        if not show_released:

            filtered_df = filtered_df[
                filtered_df["Status"] != "Released"
            ]

        # ==========================================
        # DISPLAY LIVE CALENDAR
        # ==========================================

        st.markdown("---")

        st.subheader("Live Economic Events")

        st.caption(
            "All release times are displayed in East Africa Time (UTC+3)."
        )

        if not filtered_df.empty:

            display_df = filtered_df.drop(
                columns=["Timestamp"]
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=550
            )

            st.caption(
                f"Showing {len(filtered_df)} economic events."
            )

        else:

            st.info(
                "No events match the selected filters."
            )

        # ==========================================
        # HIGH IMPACT EVENTS
        # ==========================================

        st.markdown("---")

        st.subheader("High Impact Economic Releases")

        high_impact_df = filtered_df[
            filtered_df["Impact"] == "HIGH"
        ]

        if not high_impact_df.empty:

            st.dataframe(
                high_impact_df.drop(
                    columns=["Timestamp"]
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No high-impact events match the current filters."
            )
        # ==========================================
        # JN CAPITAL ECONOMIC SURPRISE ANALYSIS
        # ==========================================

        st.markdown("---")

        st.subheader("JN Capital Economic Surprise Analysis")

        st.caption(
            "USD ECONOMIC RELEASES | ACTUAL VS MARKET FORECAST"
        )

        st.info(
            """
            This analysis compares actual economic releases
            against market forecasts to identify economic surprises.
            """
        )

        # ==========================================
        # NUMERICAL VALUE EXTRACTION
        # ==========================================

        def parse_economic_value(value):

            if value is None:
                return None

            value = str(value).strip()

            if value.lower() in [
                "", "not available", "not released", "n/a", "-"
            ]:
                return None

            match = re.search(
                r"[-+]?\d+(?:\.\d+)?",
                value.replace(",", "")
            )

            if not match:
                return None

            return {
                "number": float(match.group()),
                "is_percent": "%" in value,
                "unit": value.replace(match.group(), "").strip()
            }

        # ==========================================
        # EVENT CLASSIFICATION
        # ==========================================

        def classify_economic_event(title):

            title = title.lower()

            if any(word in title for word in [
                "unemployment rate",
                "jobless claims",
                "initial claims",
                "continuing claims"
            ]):
                return "labour_weakness"

            if any(word in title for word in [
                "consumer price", "cpi", "pce",
                "ppi", "producer price", "inflation"
            ]):
                return "inflation"

            if any(word in title for word in [
                "nonfarm payroll", "non-farm payroll",
                "employment change", "payrolls",
                "average hourly earnings"
            ]):
                return "labour_strength"

            if any(word in title for word in [
                "gdp", "retail sales", "manufacturing pmi",
                "services pmi", "composite pmi",
                "ism", "industrial production",
                "durable goods", "consumer confidence"
            ]):
                return "economic_growth"

            return "unclassified"

        # ==========================================
        # MARKET INTERPRETATION
        # ==========================================

        def interpret_surprise(category, direction):

            if direction == 0:
                return (
                    "Neutral",
                    "Neutral",
                    "Neutral"
                )

            higher = direction > 0

            if category == "inflation":

                if higher:
                    return (
                        "Potentially USD supportive",
                        "Potential gold headwind",
                        "Potential equity pressure"
                    )

                return (
                    "Potentially USD negative",
                    "Potential gold support",
                    "Potential equity support"
                )

            if category == "labour_weakness":

                if higher:
                    return (
                        "Potentially USD negative",
                        "Potential gold support",
                        "Mixed: growth concerns"
                    )

                return (
                    "Potentially USD supportive",
                    "Potential gold headwind",
                    "Mixed: employment strength"
                )

            if category in [
                "labour_strength",
                "economic_growth"
            ]:

                if higher:
                    return (
                        "Potentially USD supportive",
                        "Potential gold headwind",
                        "Mixed: growth support versus yields"
                    )

                return (
                    "Potentially USD negative",
                    "Potential gold support",
                    "Mixed: growth concerns versus yields"
                )

            return (
                "Not classified",
                "Not classified",
                "Not classified"
            )

        # ==========================================
        # SURPRISE CALCULATION
        # ==========================================

        surprise_results = []

        usd_releases = df_calendar[
            df_calendar["Currency"] == "USD"
        ]

        for _, row in usd_releases.iterrows():

            actual = parse_economic_value(row["Actual"])
            forecast = parse_economic_value(row["Forecast"])

            if actual is None or forecast is None:
                continue

            if actual["is_percent"] != forecast["is_percent"]:
                continue

            difference = actual["number"] - forecast["number"]

            if difference > 0:
                direction = 1
                result = "ABOVE EXPECTATIONS"

            elif difference < 0:
                direction = -1
                result = "BELOW EXPECTATIONS"

            else:
                direction = 0
                result = "IN LINE WITH EXPECTATIONS"

            category = classify_economic_event(
                row["Economic Event"]
            )

            usd_view, gold_view, indices_view = (
                interpret_surprise(category, direction)
            )

            surprise_results.append({

                "Release Date": row["Release Date (EAT)"],
                "Economic Event": row["Economic Event"],
                "Impact": row["Impact"],
                "Forecast": row["Forecast"],
                "Actual": row["Actual"],
                "Surprise": round(difference, 4),
                "Result": result,
                "USD Interpretation": usd_view,
                "Gold Interpretation": gold_view,
                "US30 / NAS100": indices_view

            })

        # ==========================================
        # DISPLAY RESULTS
        # ==========================================

        if surprise_results:

            surprise_df = pd.DataFrame(surprise_results)

            st.success(
                f"{len(surprise_df)} USD releases analysed."
            )

            st.dataframe(
                surprise_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.warning(
                """
                No USD releases currently have both actual and
                forecast figures available for comparison.

                Analysis will appear when releases are published.
                """
            )

        st.caption(
            "JN Capital Economic Surprise Engine | "
            "Actual versus forecast analysis | "
            "Not a standalone trading signal"
        )
        # ==========================================

        # DATA SOURCE
        # ==========================================

        st.markdown("---")

        st.subheader("Data Source & Reliability")

        st.write(
            "**Primary calendar provider:** ShowMyTrades"
        )

        st.write(
            "**Coverage:** USD, EUR, GBP, JPY, CHF, "
            "CAD, AUD, NZD and CNY."
        )

        st.write(
            "**Refresh interval:** Every 15 minutes."
        )

        st.write(
            "**Timezone:** East Africa Time (UTC+3)."
        )

        st.info(
            """
            **Data interpretation**

            - Forecast: Market expectation before the release.
            - Previous: Previously reported economic figure.
            - Actual: Reported figure after publication.
            - Impact: Provider-assigned event importance.
            - Data Confidence: Provider's indication of source agreement.

            Missing figures are displayed as unavailable rather than
            estimated or invented.

            Economic releases can be revised after publication.
            """
        )

        st.caption(
            "Economic calendar data provided by ShowMyTrades."
        )

    else:

        st.info(
            "Calendar events will appear here when data becomes available."
        )

    st.markdown("---")
elif page == "Live News & Market Intelligence":

    import requests
    import xml.etree.ElementTree as ET
    import pandas as pd
    import re
    import html
    from datetime import datetime
    from email.utils import parsedate_to_datetime
    from zoneinfo import ZoneInfo

    # ==========================================
    # JN CAPITAL LIVE NEWS CENTRE
    # ==========================================

    st.markdown("# Live News & Market Intelligence")

    st.caption(
        "GLOBAL FINANCIAL NEWS | ECONOMIC DEVELOPMENTS | MARKET INTELLIGENCE"
    )

    st.markdown("---")

    # ==========================================
    # NEWS CATEGORIES
    # ==========================================

    news_categories = {

        "Breaking Financial News":
            "financial markets OR breaking financial news",

        "US Economic News":
            "US economy OR US inflation OR US employment OR US GDP",

        "Central Bank News":
            "Federal Reserve OR ECB OR Bank of England OR Bank of Japan",

        "Forex & Dollar News":
            "US dollar OR DXY OR forex markets OR currency markets",

        "Gold & Commodities":
            "gold prices OR silver prices OR crude oil OR commodities",

        "Stock Market News":
            "Dow Jones OR Nasdaq OR S&P 500 OR Wall Street",

        "Geopolitical News":
            "geopolitics OR international trade OR sanctions OR global conflicts"
    }

    # ==========================================
    # NEWS FETCHING ENGINE
    # ==========================================

    @st.cache_data(ttl=300)

    def fetch_live_news(category):

        query = news_categories[category] + " when:1d"

        url = "https://news.google.com/rss/search"

        params = {
            "q": query,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en"
        }

        try:

            response = requests.get(
                url,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
                timeout=20
            )

            response.raise_for_status()

            root = ET.fromstring(response.content)

            news_items = []

            for item in root.findall(".//item"):

                title = item.findtext("title", "No title")

                link = item.findtext("link", "")

                published = item.findtext("pubDate", "")

                source_element = item.find("source")

                source = (
                    source_element.text
                    if source_element is not None
                    else "Google News"
                )

                description = item.findtext(
                    "description",
                    ""
                )

                description = re.sub(
                    r"<[^>]+>",
                    "",
                    description
                )

                description = html.unescape(
                    description
                ).strip()

                try:

                    published_date = parsedate_to_datetime(
                        published
                    )

                    published_date = published_date.astimezone(
                        ZoneInfo("Africa/Kampala")
                    )

                    published_text = published_date.strftime(
                        "%d %b %Y | %H:%M EAT"
                    )

                except Exception:

                    published_text = published

                news_items.append({

                    "Headline": html.unescape(title),

                    "Source": source,

                    "Published": published_text,

                    "Description": description,

                    "Link": link

                })

            return news_items, None

        except Exception as error:

            return [], str(error)

    # ==========================================
    # JN CAPITAL MARKET IMPACT ANALYSIS ENGINE
    # ==========================================

    def analyse_market_impact(headline):

        title = headline.lower()

        result = {
            "importance": "LOW",
            "topic": "General Financial News",
            "explanation": "This headline may contain relevant financial information. Further verification is required.",
            "usd": "No clear directional implication established.",
            "gold": "No clear directional implication established.",
            "indices": "No clear directional implication established.",
            "monitor": "Watch for further details and market reaction."
        }

        # FEDERAL RESERVE

        if any(x in title for x in [
            "federal reserve", "fed rate",
            "interest rate decision", "rate cut",
            "rate hike", "powell"
        ]):

            result.update({
                "importance": "HIGH",
                "topic": "Federal Reserve & Monetary Policy",
                "explanation": "Developments involving US monetary policy can influence interest-rate expectations, Treasury yields and the US dollar.",
                "usd": "Monitor dollar reaction and interest-rate expectations.",
                "gold": "Monitor real yields and the opportunity cost of holding gold.",
                "indices": "Monitor borrowing costs, valuations and equity sentiment.",
                "monitor": "Watch Treasury yields, Fed commentary and rate expectations."
            })

        # INFLATION

        elif any(x in title for x in [
            "inflation", "consumer price index",
            "cpi", "producer price index",
            "ppi", "pce prices"
        ]):

            result.update({
                "importance": "HIGH",
                "topic": "US & Global Inflation",
                "explanation": "Inflation developments can influence expectations about future interest rates and purchasing power.",
                "usd": "Watch how inflation changes expectations for US interest rates.",
                "gold": "Monitor real yields, inflation expectations and the dollar.",
                "indices": "Watch bond yields and their potential effect on equity valuations.",
                "monitor": "Compare reported inflation with market expectations."
            })

        # EMPLOYMENT

        elif any(x in title for x in [
            "nonfarm payroll", "non-farm payroll",
            "unemployment", "jobless claims",
            "employment report", "jobs report",
            "average hourly earnings"
        ]):

            result.update({
                "importance": "HIGH",
                "topic": "Employment & Labour Market",
                "explanation": "Labour market developments influence assessments of economic strength and potential monetary policy decisions.",
                "usd": "Monitor employment strength and interest-rate expectations.",
                "gold": "Watch Treasury yields and the dollar following the release.",
                "indices": "Assess employment strength against recession and interest-rate concerns.",
                "monitor": "Check actual figures against forecasts and previous readings."
            })

        # GDP & ECONOMIC GROWTH

        elif any(x in title for x in [
            "gross domestic product", "gdp",
            "economic growth", "recession",
            "manufacturing pmi", "services pmi",
            "ism manufacturing", "ism services"
        ]):

            result.update({
                "importance": "HIGH",
                "topic": "Economic Growth & Activity",
                "explanation": "Growth developments help investors assess economic momentum and corporate earnings prospects.",
                "usd": "Monitor relative economic strength and interest-rate expectations.",
                "gold": "Assess whether growth developments change demand for safe-haven assets.",
                "indices": "Monitor implications for corporate earnings and economic confidence.",
                "monitor": "Look for confirmation from other economic indicators."
            })

        # GEOPOLITICAL DEVELOPMENTS

        elif any(x in title for x in [
            "war", "military", "sanctions",
            "invasion", "conflict", "missile",
            "tariff", "trade war", "trade dispute"
        ]):

            result.update({
                "importance": "HIGH",
                "topic": "Geopolitical & Trade Risk",
                "explanation": "Geopolitical and trade developments can affect risk appetite, supply chains, commodity prices and safe-haven demand.",
                "usd": "Monitor safe-haven demand and changes in global risk sentiment.",
                "gold": "Monitor safe-haven demand and potential supply disruptions.",
                "indices": "Assess potential effects on risk appetite, trade and corporate earnings.",
                "monitor": "Verify the development and watch for official responses."
            })

        # GOLD & COMMODITIES

        elif any(x in title for x in [
            "gold price", "gold rises", "gold falls",
            "silver price", "oil price",
            "crude oil", "opec", "commodity prices"
        ]):

            result.update({
                "importance": "MEDIUM",
                "topic": "Commodities",
                "explanation": "Commodity price developments can influence inflation expectations, supply conditions and market sentiment.",
                "usd": "Monitor commodity-related inflation and currency effects.",
                "gold": "Monitor gold demand, dollar movements and real yields.",
                "indices": "Watch energy costs, inflation expectations and sector exposure.",
                "monitor": "Check commodity prices and related market developments."
            })

        # FINANCIAL MARKETS

        elif any(x in title for x in [
            "stock market", "wall street",
            "nasdaq", "dow jones",
            "s&p 500", "equities",
            "bond yields", "treasury yields"
        ]):

            result.update({
                "importance": "MEDIUM",
                "topic": "Financial Markets",
                "explanation": "Market developments can reveal changes in investor positioning, risk appetite and financial conditions.",
                "usd": "Monitor dollar movements and Treasury yields.",
                "gold": "Watch real yields and broader risk sentiment.",
                "indices": "Monitor market breadth, volatility and sector performance.",
                "monitor": "Look for confirmation across related markets."
            })

        return result
    # ==========================================
    # NEWS FILTER
    # ==========================================

    selected_category = st.selectbox(
        "SELECT NEWS CATEGORY",
        list(news_categories.keys())
    )

    col1, col2 = st.columns([3, 1])

    with col1:

        st.caption(
            "News coverage: Global financial and economic developments."
        )

    with col2:

        if st.button("Refresh News"):

            fetch_live_news.clear()

            st.rerun()

    st.markdown("---")

    # ==========================================
    # LOAD NEWS
    # ==========================================

    with st.spinner("Retrieving financial news..."):

        news_items, news_error = fetch_live_news(
            selected_category
        )
            # ==========================================
    # JN CAPITAL BREAKING NEWS INTELLIGENCE
    # ==========================================

    # Remove duplicate headlines

    unique_news = []

    seen_headlines = set()

    for article in news_items:

        normalized_title = re.sub(
            r"[^a-z0-9]",
            "",
            article["Headline"].lower()
        )

        if normalized_title in seen_headlines:
            continue

        seen_headlines.add(normalized_title)

        # Analyse headline importance

        analysis = analyse_market_impact(
            article["Headline"]
        )

        article["JN Importance"] = analysis["importance"]

        # Identify breaking or developing headlines

        headline_lower = article["Headline"].lower()

        article["Breaking"] = any(
            phrase in headline_lower
            for phrase in [
                "breaking:",
                "breaking news",
                "developing:",
                "just in:",
                "urgent:"
            ]
        )

        unique_news.append(article)

    # Put important stories first

    importance_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2
    }

    news_items = sorted(
        unique_news,
        key=lambda article: importance_order.get(
            article["JN Importance"],
            3
        )
    )

    # News intelligence metrics

    high_count = sum(
        1 for article in news_items
        if article["JN Importance"] == "HIGH"
    )

    breaking_count = sum(
        1 for article in news_items
        if article["Breaking"]
    )

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "TOTAL HEADLINES",
        len(news_items)
    )

    metric2.metric(
        "HIGH IMPORTANCE",
        high_count
    )

    metric3.metric(
        "BREAKING / DEVELOPING",
        breaking_count
    )

    # ==========================================
    # DISPLAY NEWS
    # ==========================================

    st.subheader(selected_category)

    if news_items:

        st.success(
            f"{len(news_items)} news articles retrieved."
        )

        for article in news_items:

            if article["Breaking"]:

                st.error("BREAKING / DEVELOPING")

            elif article["JN Importance"] == "HIGH":

                st.warning("HIGH IMPORTANCE")

            st.markdown(
                f"### [{article['Headline']}]({article['Link']})"
            )

            st.caption(
                f"SOURCE: {article['Source']}  |  "
                f"PUBLISHED: {article['Published']}"
            )
                        # JN CAPITAL MARKET IMPACT ANALYSIS

            analysis = analyse_market_impact(
                article["Headline"]
            )

            st.markdown(
                f"**IMPORTANCE: {analysis['importance']}**"
                f"  |  **TOPIC: {analysis['topic']}**"
            )

            with st.expander("JN Capital Market Impact Analysis"):

                st.markdown("**WHY THIS NEWS MATTERS**")

                st.write(analysis["explanation"])

                st.markdown("**POTENTIAL MARKET IMPLICATIONS**")

                st.write(
                    f"**USD:** {analysis['usd']}"
                )

                st.write(
                    f"**XAUUSD (Gold):** {analysis['gold']}"
                )

                st.write(
                    f"**US30 / NAS100:** {analysis['indices']}"
                )

                st.markdown("**WHAT TO MONITOR NEXT**")

                st.info(analysis["monitor"])

            if article["Description"]:

                st.write(
                    article["Description"]
                )

            st.markdown("---")

    else:

        st.warning(
            "No news articles were returned for this category."
        )

        if news_error:

            st.error(
                f"News connection error: {news_error}"
            )

    # ==========================================
    # DATA SOURCE & RELIABILITY
    # ==========================================

    st.markdown("---")

    st.subheader("News Sources & Reliability")

    st.write(
        """
        **News aggregator:** Google News RSS

        **News publishers:** Original publishers identified
        alongside each headline.

        **Coverage:** Global financial markets, economic data,
        central banks, currencies, commodities and geopolitics.

        **Refresh interval:** Cached for 5 minutes.

        **Timezone:** East Africa Time (EAT).

        **Important:** Headlines and available descriptions are
        displayed from their publishers. Full articles may require
        access to the original publisher's website.
        """
    )

    st.caption(
        "JN CAPITAL | LIVE NEWS & MARKET INTELLIGENCE"
    )
elif page == "Labour Market Dashboard":

    st.markdown("# Labour Market Dashboard")

    st.caption("US EMPLOYMENT & LABOUR MARKET INTELLIGENCE")

    st.markdown("---")
    st.subheader("Latest Labour Market Indicators")

    labour_indicators = {
        "Unemployment Rate": "UNRATE",
        "Nonfarm Payrolls": "PAYEMS",
        "Initial Jobless Claims": "ICSA"
    }

    labour_data = {}

    for name, series_id in labour_indicators.items():

        df = fred_historical(series_id, years=5)

        if not df.empty:

            if name == "Nonfarm Payrolls":

                df = df.copy()

                df["Value"] = df["Value"].diff()

                df = df.dropna()

                df["3-Month Average"] = df["Value"].rolling(window=3).mean()

                labour_data["Monthly Nonfarm Payroll Change"] = df

            else:

                labour_data[name] = df
    col1, col2, col3 = st.columns(3)

    for col, (name, df) in zip(
        [col1, col2, col3],
        labour_data.items()
    ):

        latest_value = df["Value"].iloc[-1]
        latest_date = df["Date"].iloc[-1].strftime("%b %Y")

        with col:
            st.metric(
                label=name,
                value=f"{latest_value:,.2f}",
                help=f"Latest observation: {latest_date}"
            )
    st.markdown("---")

    view_type = st.radio(
        "CHART DISPLAY",
        ["Line View", "Bar View"],
        horizontal=True
    )

    st.markdown("---")

    st.subheader("Labour Market Historical Trends")

    for name, df in labour_data.items():

        st.markdown(f"### {name}")

        chart_data = df.set_index("Date")

        if name == "Monthly Nonfarm Payroll Change":

            if view_type == "Line View":

                st.line_chart(
                    chart_data[["Value", "3-Month Average"]],
                    height=300
                )

            else:

                st.bar_chart(
                    chart_data[["Value", "3-Month Average"]],
                    height=300
                )

        else:

            if view_type == "Line View":

                st.line_chart(
                    chart_data,
                    y="Value",
                    height=300
                )

            else:

                st.bar_chart(
                    chart_data,
                    y="Value",
                    height=300
                )
    st.markdown("---")

    st.subheader("Labour Market Interpretation")

    st.markdown("### 1. Stronger Labour Market")

    st.success(
        """
        **US Dollar:** Potentially bullish. Strong employment can reduce
        expectations of interest rate cuts.

        **Gold (XAUUSD):** Potentially bearish if stronger employment
        pushes Treasury yields and the US dollar higher.

        **Stock Indices (US30, NAS100, S&P 500):** Mixed. Strong employment
        supports economic growth, but higher interest rate expectations
        can pressure stock valuations.
        """
    )

    st.markdown("### 2. Weaker Labour Market")

    st.warning(
        """
        **US Dollar:** Potentially bearish if weaker employment increases
        expectations of interest rate cuts.

        **Gold (XAUUSD):** Potentially bullish if Treasury yields and the
        US dollar decline.

        **Stock Indices (US30, NAS100, S&P 500):** Mixed. Lower interest
        rate expectations can support stocks, but serious employment
        deterioration can raise recession concerns.
        """
    )

    st.markdown("### 3. Important Indicators")

    st.info(
        """
        - **Nonfarm Payrolls:** Higher-than-expected growth generally
          indicates stronger employment.
        - **Unemployment Rate:** A rising rate can indicate labour market
          weakness.
        - **Initial Jobless Claims:** Rising claims can indicate increasing
          layoffs.

        Always compare reported figures with market expectations and
        consider Treasury yields, the Federal Reserve outlook and the
        wider economic environment.
        """
    )
    st.info(
        "Monitor US employment conditions through unemployment, "
        "Nonfarm Payrolls and initial jobless claims."
    )

    st.markdown("---")
elif page == "System Status":

    from modules.data import load_dashboard_data

    # Retrieve FRED connection and data information
    data = load_dashboard_data()

    st.markdown("# System Status")

    st.markdown("---")

    st.subheader("Data Connections")

    if data.get("configured"):

        st.success("FRED API: Successfully configured")

    else:

        st.error("FRED API: Not configured")

    st.write(
        "Connection status:",
        data.get("status", "Unknown")
    )

    st.write(
        "Economic observations retrieved:",
        len(data.get("table", []))
    )

    st.write(
        "Data provider:",
        "Federal Reserve Economic Data (FRED)"
    )

    st.markdown("---")

    st.subheader("System Information")

    st.write("Application: JN Capital Macro Intelligence")
    st.write("Version: 1.0")
    st.write("Environment: Local Python")
    st.write("Data architecture: Free-source integration")

    st.caption(data.get("note", ""))

    st.markdown("---")

    st.caption(
        "API credentials are stored in .env and must never "
        "be exposed in source code."
    )
