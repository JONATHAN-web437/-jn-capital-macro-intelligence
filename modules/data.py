import os
from datetime import datetime
import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

load_dotenv()

FRED_KEY = os.getenv("FRED_API_KEY", "").strip()


SERIES = {

    # INTEREST RATES
    "10y": ("DGS10", "10-Year Treasury Yield", "%"),
    "2y": ("DGS2", "2-Year Treasury Yield", "%"),
    "fed": ("FEDFUNDS", "Federal Funds Rate", "%"),

    # INFLATION
    "cpi": ("CPIAUCSL", "Consumer Price Index", "index"),
    "core_cpi": ("CPILFESL", "Core Consumer Price Index", "index"),
    "pce": ("PCEPI", "Personal Consumption Expenditures Price Index", "index"),
    "core_pce": ("PCEPILFE", "Core PCE Price Index", "index"),

    # EMPLOYMENT
    "unemployment": ("UNRATE", "Unemployment Rate", "%"),
    "payrolls": ("PAYEMS", "Nonfarm Payroll Employment", "thousands"),
    "jobless_claims": ("ICSA", "Initial Jobless Claims", "claims"),

    # ECONOMIC GROWTH
    "gdp": ("GDPC1", "Real Gross Domestic Product", "billions of dollars"),
    "industrial": ("INDPRO", "Industrial Production Index", "index"),

    # CONSUMER ACTIVITY
    "retail_sales": ("RRSFS", "Real Retail and Food Services Sales", "millions of dollars"),

}


def fred_latest(series_id):

    if not FRED_KEY:
        return None, "No FRED API key configured"

    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id": series_id,
        "api_key": FRED_KEY,
        "file_type": "json",
        "limit": 10,
        "sort_order": "desc"
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()

        obs = r.json().get("observations", [])

        for row in obs:
            if row.get("value") not in (None, "", "."):
                return {
                    "value": row["value"],
                    "date": row["date"]
                }, None

        return None, "No valid observations returned"

    except Exception as e:
        return None, str(e)
    # -----------------------------------------
# JN CAPITAL FRED HISTORICAL DATA
# -----------------------------------------

def fred_history(series_id, limit=36):

    if not FRED_KEY:
        return [], "No FRED API key configured"

    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id": series_id,
        "api_key": FRED_KEY,
        "file_type": "json",
        "limit": limit,
        "sort_order": "desc"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        observations = response.json().get(
            "observations", []
        )

        history = []

        for row in observations:

            value = row.get("value")

            if value not in (None, "", "."):

                history.append({
                    "date": row["date"],
                    "value": float(value)
                })

        # Arrange observations from oldest to newest
        history.reverse()

        return history, None

    except Exception as e:

        return [], str(e)
    # =====================================================
# JN CAPITAL AUTOMATED MACROECONOMIC SCORING ENGINE
# =====================================================
# =====================================================
# JN CAPITAL ECONOMIC INTERPRETATION ENGINE
# =====================================================

def interpret_economic_momentum(
    value,
    positive_message,
    negative_message,
    threshold=0.15
):

    if value is None:

        return "Insufficient data for interpretation"

    if value > threshold:

        return positive_message

    elif value < -threshold:

        return negative_message

    else:

        return "Relatively stable / little change"


def macro_signal_score(change, higher_supports_gold=True, scale=1.0):

    if change is None:
        return None

    direction = 1 if higher_supports_gold else -1

    score = 50 + direction * (change / scale) * 25

    return round(max(0, min(100, score)))


# -----------------------------------------------------
# CALCULATE YEAR-ON-YEAR GROWTH ACCELERATION
# -----------------------------------------------------

def calculate_yoy_acceleration(history, periods=12):

    if len(history) < (periods * 2 + 1):
        return None

    values = [item["value"] for item in history]

    latest = values[-1]
    one_year_ago = values[-1 - periods]
    two_years_ago = values[-1 - periods * 2]

    if two_years_ago == 0 or one_year_ago == 0:
        return None

    current_growth = (
        (latest / one_year_ago) - 1
    ) * 100

    previous_growth = (
        (one_year_ago / two_years_ago) - 1
    ) * 100

    acceleration = current_growth - previous_growth

    return round(acceleration, 4)


# -----------------------------------------------------
# MAIN MACROECONOMIC ENGINE
# -----------------------------------------------------

def calculate_macro_score(asset="XAUUSD"):

    if asset != "XAUUSD":

        return {
            "available": False,
            "message": (
                "The current macroeconomic model is configured "
                "for XAUUSD only."
            )
        }

    # Retrieve historical economic observations

    series_keys = [
        "cpi",
        "core_cpi",
        "pce",
        "core_pce",
        "unemployment",
        "payrolls",
        "jobless_claims",
        "gdp",
        "industrial",
        "retail_sales"
    ]

    histories = {}
    latest_dates = {}
    errors = []

    for key in series_keys:

        sid = SERIES[key][0]

        history, error = fred_history(sid, 36)

        histories[key] = history

        if history:

            latest_dates[key] = history[-1]["date"]

        else:

            errors.append(
                f"{key}: {error or 'No observations'}"
            )

    # -------------------------------------------------
    # 1. INFLATION
    # -------------------------------------------------

    inflation_signals = {}

    for key in [
        "cpi",
        "core_cpi",
        "pce",
        "core_pce"
    ]:

        acceleration = calculate_yoy_acceleration(
            histories[key],
            12
        )

        inflation_signals[key] = macro_signal_score(
            acceleration,
            higher_supports_gold=True,
            scale=1.0
        )

    valid_inflation = [
        value
        for value in inflation_signals.values()
        if value is not None
    ]

    inflation_score = (
        round(sum(valid_inflation) / len(valid_inflation))
        if valid_inflation else None
    )

    # -------------------------------------------------
    # 2. EMPLOYMENT
    # -------------------------------------------------

    employment_signals = {}

    # Unemployment: rising unemployment supports gold
    # in this initial defensive-economic-conditions model.

    unemployment_history = histories["unemployment"]

    unemployment_change = None

    if len(unemployment_history) >= 4:

        unemployment_change = (
            unemployment_history[-1]["value"]
            - unemployment_history[-4]["value"]
        )

    employment_signals["unemployment"] = macro_signal_score(
        unemployment_change,
        higher_supports_gold=True,
        scale=0.5
    )

    # Payrolls: slowing employment growth supports gold.

    payroll_history = histories["payrolls"]

    payroll_acceleration = None

    if len(payroll_history) >= 7:

        current_three_month = (
            payroll_history[-1]["value"]
            - payroll_history[-4]["value"]
        )

        previous_three_month = (
            payroll_history[-4]["value"]
            - payroll_history[-7]["value"]
        )

        payroll_acceleration = (
            current_three_month - previous_three_month
        )

    employment_signals["payrolls"] = macro_signal_score(
        payroll_acceleration,
        higher_supports_gold=False,
        scale=300
    )

    # Jobless claims: rising claims support gold.

    claims_history = histories["jobless_claims"]

    claims_change = None

    if len(claims_history) >= 8:

        latest_four = [
            item["value"]
            for item in claims_history[-4:]
        ]

        previous_four = [
            item["value"]
            for item in claims_history[-8:-4]
        ]

        latest_average = sum(latest_four) / 4
        previous_average = sum(previous_four) / 4

        if previous_average != 0:

            claims_change = (
                (latest_average / previous_average) - 1
            ) * 100

    employment_signals["jobless_claims"] = macro_signal_score(
        claims_change,
        higher_supports_gold=True,
        scale=10
    )

    valid_employment = [
        value
        for value in employment_signals.values()
        if value is not None
    ]

    employment_score = (
        round(sum(valid_employment) / len(valid_employment))
        if valid_employment else None
    )

    # -------------------------------------------------
    # 3. ECONOMIC GROWTH
    # -------------------------------------------------

    growth_signals = {}

    # GDP: slowing growth supports gold.

    gdp_acceleration = calculate_yoy_acceleration(
        histories["gdp"],
        4
    )

    growth_signals["gdp"] = macro_signal_score(
        gdp_acceleration,
        higher_supports_gold=False,
        scale=1.5
    )

    # Industrial production: slowing growth supports gold.

    industrial_acceleration = calculate_yoy_acceleration(
        histories["industrial"],
        12
    )

    growth_signals["industrial"] = macro_signal_score(
        industrial_acceleration,
        higher_supports_gold=False,
        scale=2.0
    )

    valid_growth = [
        value
        for value in growth_signals.values()
        if value is not None
    ]

    growth_score = (
        round(sum(valid_growth) / len(valid_growth))
        if valid_growth else None
    )

    # -------------------------------------------------
    # 4. CONSUMER ACTIVITY
    # -------------------------------------------------

    retail_acceleration = calculate_yoy_acceleration(
        histories["retail_sales"],
        12
    )

    consumer_score = macro_signal_score(
        retail_acceleration,
        higher_supports_gold=False,
        scale=2.0
    )

    # -------------------------------------------------
    # OVERALL MACROECONOMIC SCORE
    # -------------------------------------------------

    components = {
        "Inflation": inflation_score,
        "Employment": employment_score,
        "Economic Growth": growth_score,
        "Consumer Activity": consumer_score
    }

    weights = {
        "Inflation": 30,
        "Employment": 25,
        "Economic Growth": 25,
        "Consumer Activity": 20
    }

    available_components = {
        name: score
        for name, score in components.items()
        if score is not None
    }

    # Require at least three available categories.

    if len(available_components) < 3:

        return {
            "available": False,
            "message": (
                "Insufficient economic data to calculate "
                "a reliable macroeconomic score."
            ),
            "components": components,
            "errors": errors
        }

    total_weight = sum(
        weights[name]
        for name in available_components
    )

    overall_score = sum(
        available_components[name] * weights[name]
        for name in available_components
    ) / total_weight

    overall_score = round(overall_score)

    # -------------------------------------------------
    # MARKET BIAS
    # -------------------------------------------------

    if overall_score >= 80:

        bias = "VERY SUPPORTIVE OF GOLD"

    elif overall_score >= 60:

        bias = "SUPPORTIVE OF GOLD"

    elif overall_score >= 41:

        bias = "MIXED / NEUTRAL"

    elif overall_score >= 21:

        bias = "UNFAVOURABLE TO GOLD"

    else:

        bias = "VERY UNFAVOURABLE TO GOLD"
    # -------------------------------------------------
    # ECONOMIC INTERPRETATIONS
    # -------------------------------------------------

    # Inflation momentum

    inflation_accelerations = []

    for key in [
        "cpi",
        "core_cpi",
        "pce",
        "core_pce"
    ]:

        value = calculate_yoy_acceleration(
            histories[key],
            12
        )

        if value is not None:

            inflation_accelerations.append(value)

    average_inflation_acceleration = (
        sum(inflation_accelerations)
        / len(inflation_accelerations)
        if inflation_accelerations else None
    )

    interpretations = {

        "Inflation": interpret_economic_momentum(
            average_inflation_acceleration,
            "Inflation pressure is accelerating.",
            "Inflation pressure is cooling.",
            0.15
        ),

        "Unemployment": interpret_economic_momentum(
            unemployment_change,
            "Unemployment is rising; labour conditions are weakening.",
            "Unemployment is falling; labour conditions are improving.",
            0.1
        ),

        "Payrolls": interpret_economic_momentum(
            payroll_acceleration,
            "Employment growth is accelerating.",
            "Employment growth is slowing.",
            50
        ),

        "Jobless Claims": interpret_economic_momentum(
            claims_change,
            "Jobless claims are increasing; labour conditions may be weakening.",
            "Jobless claims are declining; labour conditions may be improving.",
            1
        ),

        "GDP": interpret_economic_momentum(
            gdp_acceleration,
            "GDP growth momentum is improving.",
            "GDP growth momentum is weakening.",
            0.15
        ),

        "Industrial Production": interpret_economic_momentum(
            industrial_acceleration,
            "Industrial activity is strengthening.",
            "Industrial activity is weakening.",
            0.15
        ),

        "Consumer Activity": interpret_economic_momentum(
            retail_acceleration,
            "Real consumer spending growth is strengthening.",
            "Real consumer spending growth is weakening.",
            0.15
        )

    }
    return {

        "available": True,

        "asset": asset,

        "score": overall_score,

        "bias": bias,

        "components": components,

        "interpretations": interpretations,

        "weights": weights,

        "inflation_details": inflation_signals,

        "employment_details": employment_signals,

        "growth_details": growth_signals,

        "latest_dates": latest_dates,

        "data_errors": errors,

        "message": (
            "Rule-based macroeconomic assessment using "
            "historical FRED economic observations."
        )

    }


@st.cache_data(ttl=900)
def load_dashboard_data():

    result = {
        "configured": bool(FRED_KEY),
        "status": "No key configured",
        "note": "Add a FRED API key to .env to retrieve observations.",
        "table": []
    }

    if not FRED_KEY:
        result.update({k: "â€”" for k in SERIES})
        return result

    table = []
    errors = []

    for key, (sid, label, unit) in SERIES.items():

        observation, error = fred_latest(sid)

        if observation:

            result[key] = observation["value"]

            table.append({
                "Indicator": label,
                "Value": observation["value"],
                "Unit": unit,
                "Observation date": observation["date"],
                "Series": sid,
                "Source": "FRED"
            })

        else:

            result[key] = "â€”"
            errors.append(f"{sid}: {error}")

    result["table"] = table

    result["status"] = "Connected" if table else "Connection/data issue"

    result["note"] = (
        "; ".join(errors)
        if errors
        else "Latest available observations retrieved. Series publication dates may differ."
    )

    return result


@st.cache_data(ttl=900)
def load_yield_curve_history(years=2):

    """
    Retrieve historical US 10-Year and 2-Year Treasury yields
    and calculate their spread in basis points.
    """

    if not FRED_KEY:
        return pd.DataFrame(), "FRED API key not configured"

    start_date = (
        datetime.now() - pd.Timedelta(days=years * 365)
    ).strftime("%Y-%m-%d")

    series_ids = {
        "DGS10": "10Y",
        "DGS2": "2Y"
    }

    frames = []

    url = "https://api.stlouisfed.org/fred/series/observations"

    try:

        for series_id, column_name in series_ids.items():

            params = {
                "series_id": series_id,
                "api_key": FRED_KEY,
                "file_type": "json",
                "observation_start": start_date,
                "sort_order": "asc"
            }

            response = requests.get(
                url,
                params=params,
                timeout=20
            )

            response.raise_for_status()

            observations = response.json().get("observations", [])

            frame = pd.DataFrame(observations)

            if frame.empty:
                return pd.DataFrame(), f"No historical data for {series_id}"

            frame = frame[["date", "value"]]

            frame["value"] = pd.to_numeric(
                frame["value"],
                errors="coerce"
            )

            frame = frame.rename(
                columns={"value": column_name}
            )

            frames.append(frame)

        history = pd.merge(
            frames[0],
            frames[1],
            on="date",
            how="inner"
        )

        history = history.dropna()

        history["Spread"] = history["10Y"] - history["2Y"]

        history["Spread_bps"] = history["Spread"] * 100

        return history, None

    except Exception as error:

        return pd.DataFrame(), str(error)



@st.cache_data(ttl=900)
def fred_historical(series_id, years=5):

    """
    Retrieve historical economic observations from FRED.
    """

    if not FRED_KEY:
        return pd.DataFrame()

    url = "https://api.stlouisfed.org/fred/series/observations"

    start_date = (
        datetime.now() - pd.Timedelta(days=years * 365)
    ).strftime("%Y-%m-%d")

    params = {
        "series_id": series_id,
        "api_key": FRED_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "sort_order": "asc"
    }

    for attempt in range(3):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=(10, 45)
            )

            response.raise_for_status()

            observations = response.json().get("observations", [])

            records = []

            for item in observations:

                if item["value"] != ".":

                    records.append({
                        "Date": item["date"],
                        "Value": float(item["value"])
                    })

            df = pd.DataFrame(records)

            if not df.empty:

                df["Date"] = pd.to_datetime(df["Date"])
                df = df.sort_values("Date")

            return df

        except requests.exceptions.RequestException:

            if attempt == 2:
                return pd.DataFrame()

        except (ValueError, KeyError, TypeError):
            return pd.DataFrame()

def calculate_yoy_inflation(series_id, years=5):

    df = fred_historical(series_id, years)

    if df.empty or len(df) < 13:
        return pd.DataFrame()

    df = df.copy()

    df["YoY Inflation (%)"] = (
        df["Value"].pct_change(periods=12) * 100
    )

    df = df.dropna()

    return df

@st.cache_data(ttl=900)
def load_currency_history(base="USD", days=365):

    from datetime import timedelta

    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=days)

    url = "https://api.frankfurter.dev/v2/rates"

    params = {
        "base": base,
        "from": start_date.isoformat(),
        "to": end_date.isoformat()
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        df = pd.DataFrame(data)

        if df.empty:
            return pd.DataFrame()

        df["date"] = pd.to_datetime(df["date"])

        return df.sort_values("date")

    except Exception as e:

        print(f"Currency data error: {e}")

        return pd.DataFrame()


def calculate_currency_strength(period="1 Month"):

    from math import log

    periods = {
        "1 Week": 5,
        "1 Month": 21,
        "3 Months": 63
    }

    if period not in periods:
        return pd.DataFrame()

    lookback = periods[period]

    calendar_days = {
        "1 Week": 14,
        "1 Month": 45,
        "3 Months": 120
    }

    df = load_currency_history(
        base="USD",
        days=calendar_days[period]
    )

    if df.empty:
        return pd.DataFrame()

    currencies = [
        "USD", "EUR", "GBP", "JPY",
        "CHF", "CAD", "AUD", "NZD"
    ]

    foreign_currencies = [
        currency for currency in currencies
        if currency != "USD"
    ]

    df = df[df["quote"].isin(foreign_currencies)]

    rates = df.pivot(
        index="date",
        columns="quote",
        values="rate"
    ).sort_index()

    rates = rates.dropna(
        subset=foreign_currencies
    )

    if len(rates) <= lookback:
        return pd.DataFrame()

    latest = rates.iloc[-1]
    previous = rates.iloc[-(lookback + 1)]

    # Calculate logarithmic relative returns
    strengths = {"USD": 0.0}

    for currency in foreign_currencies:

        change = log(
            float(latest[currency]) /
            float(previous[currency])
        ) * 100

        strengths[currency] = -change

    # Centre all currency scores around zero
    average_strength = sum(
        strengths.values()
    ) / len(strengths)

    strengths = {
        currency: value - average_strength
        for currency, value in strengths.items()
    }

    # Rank strongest to weakest
    result = pd.DataFrame({
        "Currency": currencies,
        "Strength (%)": [
            strengths[currency]
            for currency in currencies
        ]
    })

    result = result.sort_values(
        "Strength (%)",
        ascending=False
    ).reset_index(drop=True)

    result.insert(
        0,
        "Rank",
        range(1, len(result) + 1)
    )

    return result


def calculate_fundamental_score():

    indicators = {
        "10-Year Treasury Yield": ("DGS10", "rate"),
        "2-Year Treasury Yield": ("DGS2", "rate"),
        "Federal Funds Rate": ("FEDFUNDS", "rate"),
        "Unemployment Rate": ("UNRATE", "rate"),
        "Headline CPI Inflation (YoY)": ("CPIAUCSL", "inflation"),
        "Core CPI Inflation (YoY)": ("CPILFESL", "inflation")
    }

    results = []

    for name, (series_id, data_type) in indicators.items():

        if data_type == "inflation":

            df = calculate_yoy_inflation(series_id)

            if not df.empty:

                latest = df.iloc[-1]

                results.append({
                    "Indicator": name,
                    "Latest Value": float(latest["YoY Inflation (%)"]),
                    "Date": latest["Date"].strftime("%Y-%m-%d"),
                    "Status": "Available"
                })

            else:

                results.append({
                    "Indicator": name,
                    "Latest Value": None,
                    "Date": "Unavailable",
                    "Status": "No inflation data available"
                })

        else:

            data, error = fred_latest(series_id)

            if data:

                results.append({
                    "Indicator": name,
                    "Latest Value": float(data["value"]),
                    "Date": data["date"],
                    "Status": "Available"
                })

            else:

                results.append({
                    "Indicator": name,
                    "Latest Value": None,
                    "Date": "Unavailable",
                    "Status": error
                })

    return pd.DataFrame(results)



    if value is None:
        return "Neutral"
def classify_fundamental_indicator(indicator, value, asset):
    rules = {

        "XAUUSD": {
            "10-Year Treasury Yield": (4.0, "lower"),
            "2-Year Treasury Yield": (4.0, "lower"),
            "Federal Funds Rate": (4.0, "lower"),
            "Headline CPI Inflation (YoY)": (3.0, "higher"),
            "Core CPI Inflation (YoY)": (3.0, "higher"),
            "Unemployment Rate": (4.5, "higher")
        },

        "USD": {
            "10-Year Treasury Yield": (4.0, "higher"),
            "2-Year Treasury Yield": (4.0, "higher"),
            "Federal Funds Rate": (4.0, "higher"),
            "Headline CPI Inflation (YoY)": (3.0, "higher"),
            "Core CPI Inflation (YoY)": (3.0, "higher"),
            "Unemployment Rate": (4.5, "lower")
        }
    }

    if asset not in rules or indicator not in rules[asset]:
        return "Neutral"

    threshold, direction = rules[asset][indicator]

    if direction == "higher":

        if value > threshold:
            return "Bullish"

        elif value < threshold:
            return "Bearish"

    elif direction == "lower":

        if value < threshold:
            return "Bullish"

        elif value > threshold:
            return "Bearish"

    return "Neutral"

@st.cache_data(ttl=900)
def load_fed_monetary_policy_feed():

    url = "https://www.federalreserve.gov/feeds/press_monetary.xml"

    try:

        response = requests.get(url, timeout=20)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        articles = []

        for item in root.findall(".//item"):

            articles.append({
                "Title": item.findtext("title", default=""),
                "Date": item.findtext("pubDate", default=""),
                "Description": item.findtext("description", default=""),
                "Link": item.findtext("link", default="")
            })

        return pd.DataFrame(articles)

    except Exception as e:

        print(f"Federal Reserve feed error: {e}")

        return pd.DataFrame()

class FedStatementParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.text_content = []

    def handle_data(self, data):
        text = data.strip()

        if text:
            self.text_content.append(text)

    def get_text(self):
        return " ".join(self.text_content)


def load_fed_statement_text(url):
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        parser = FedStatementParser()
        parser.feed(response.text)

        return parser.get_text()

    except Exception as e:
        print(f"Fed statement retrieval error: {e}")
        return ""
def calculate_fed_rate_trend():

    df = fred_historical("FEDFUNDS", years=3)

    if df.empty or len(df) < 2:
        return {
            "Current Rate": None,
            "Previous Rate": None,
            "Change": None,
            "Direction": "Unavailable"
        }

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    current_rate = float(latest["Value"])
    previous_rate = float(previous["Value"])

    change = current_rate - previous_rate

    if change > 0:
        direction = "Rising"
    elif change < 0:
        direction = "Falling"
    else:
        direction = "Unchanged"

    return {
        "Current Rate": current_rate,
        "Previous Rate": previous_rate,
        "Change": change,
        "Direction": direction,
        "Latest Date": latest["Date"]
    }

def calculate_fed_target_range():

    upper = fred_historical("DFEDTARU", years=3)
    lower = fred_historical("DFEDTARL", years=3)

    if upper.empty or lower.empty:
        return {
            "Lower Bound": None,
            "Upper Bound": None,
            "Midpoint": None,
            "Status": "Unavailable"
        }

    upper_latest = upper.iloc[-1]
    lower_latest = lower.iloc[-1]

    if upper_latest["Date"] != lower_latest["Date"]:
        return {
            "Lower Bound": None,
            "Upper Bound": None,
            "Midpoint": None,
            "Status": "Dates do not match"
        }

    lower_rate = float(lower_latest["Value"])
    upper_rate = float(upper_latest["Value"])

    return {
        "Lower Bound": lower_rate,
        "Upper Bound": upper_rate,
        "Midpoint": (lower_rate + upper_rate) / 2,
        "Date": upper_latest["Date"],
        "Status": "Available"
    }

def analyze_fed_rate_position():

    target = calculate_fed_target_range()
    effective = fred_latest("FEDFUNDS")[0]

    if target["Status"] != "Available" or effective is None:

        return {
            "Position": "Unavailable",
            "Explanation": "Required rate data is unavailable."
        }

    effective_rate = float(effective["value"])

    lower = target["Lower Bound"]
    upper = target["Upper Bound"]

    if lower <= effective_rate <= upper:

        position = "Inside Target Range"
        explanation = (
            "The effective Federal Funds Rate is within "
            "the official target range."
        )

    elif effective_rate < lower:

        position = "Below Target Range"
        explanation = (
            "The effective Federal Funds Rate is below "
            "the official target range."
        )

    else:

        position = "Above Target Range"
        explanation = (
            "The effective Federal Funds Rate is above "
            "the official target range."
        )

    return {
        "Effective Rate": effective_rate,
        "Lower Bound": lower,
        "Upper Bound": upper,
        "Position": position,
        "Explanation": explanation
    }

@st.cache_data(ttl=3600)
def load_fed_policy_history():

    upper = fred_historical("DFEDTARU", years=5)
    lower = fred_historical("DFEDTARL", years=5)

    if upper.empty or lower.empty:
        return pd.DataFrame()

    upper = upper.rename(columns={"Value": "Upper"})
    lower = lower.rename(columns={"Value": "Lower"})

    history = pd.merge(
        lower[["Date", "Lower"]],
        upper[["Date", "Upper"]],
        on="Date",
        how="inner"
    )

    history = history.sort_values("Date").reset_index(drop=True)

    history["Previous Lower"] = history["Lower"].shift(1)
    history["Previous Upper"] = history["Upper"].shift(1)

    changes = history[
        (history["Lower"] != history["Previous Lower"]) |
        (history["Upper"] != history["Previous Upper"])
    ].dropna(
        subset=["Previous Lower", "Previous Upper"]
    ).copy()

    changes["Decision"] = "Target Range Adjustment"

    changes.loc[
        changes["Lower"] > changes["Previous Lower"],
        "Decision"
    ] = "Rate Hike"

    changes.loc[
        changes["Lower"] < changes["Previous Lower"],
        "Decision"
    ] = "Rate Cut"

    changes["Previous Range"] = changes.apply(
        lambda row: (
            f"{row['Previous Lower']:.2f}% - "
            f"{row['Previous Upper']:.2f}%"
        ),
        axis=1
    )

    changes["New Range"] = changes.apply(
        lambda row: (
            f"{row['Lower']:.2f}% - "
            f"{row['Upper']:.2f}%"
        ),
        axis=1
    )

    return changes[
        ["Date", "Decision", "Previous Range", "New Range"]
    ].tail(15).iloc[::-1].reset_index(drop=True)

@st.cache_data(ttl=3600)
def load_fomc_statement_history(years=5):

    from html.parser import HTMLParser
    from datetime import datetime
    import re
    import html

    class FOMCParser(HTMLParser):

        def __init__(self):
            super().__init__()
            self.current_date = ""
            self.current_link = ""
            self.current_title = ""
            self.results = []
            self.capture_title = False

        def handle_starttag(self, tag, attrs):

            attrs = dict(attrs)

            if tag == "time":
                self.current_date = ""

            if tag == "a" and "href" in attrs:

                href = attrs["href"]

                if "monetary" in href and href.endswith(".htm"):
                    self.current_link = href
                    self.capture_title = True
                    self.current_title = ""

        def handle_data(self, data):

            if self.current_date == "":
                self.current_date = data.strip()

            if self.capture_title:
                self.current_title += data

        def handle_endtag(self, tag):

            if tag == "a" and self.capture_title:

                title = self.current_title.strip()

                if "FOMC statement" in title:

                    self.results.append({
                        "Date": self.current_date,
                        "Title": title,
                        "Link": self.current_link
                    })

                self.capture_title = False

    results = []

    current_year = datetime.now().year

    for year in range(current_year, current_year - years, -1):

        url = (
            f"https://www.federalreserve.gov/"
            f"newsevents/pressreleases/{year}-press-fomc.htm"
        )

        try:

            response = requests.get(url, timeout=20)
            response.raise_for_status()

            parser = FOMCParser()
            parser.feed(response.text)

            for item in parser.results:

                link = (
                    "https://www.federalreserve.gov"
                    + item["Link"]
                )

                try:

                    statement_response = requests.get(
                        link,
                        timeout=20
                    )

                    statement_response.raise_for_status()

                    text = html.unescape(
                        re.sub(
                            r"\s+",
                            " ",
                            re.sub(
                                r"<[^>]+>",
                                " ",
                                statement_response.text
                            )
                        )
                    )

                    sentences = re.findall(
                        r"[^.]*target range for the federal funds rate[^.]*\.",
                        text,
                        re.IGNORECASE
                    )

                    decision_text = (
                        sentences[0].strip()
                        if sentences
                        else "Decision wording unavailable"
                    )

                    decision_lower = decision_text.lower()

                    if "raise the target range" in decision_lower:
                        decision = "Rate Hike"

                    elif "lower the target range" in decision_lower:
                        decision = "Rate Cut"

                    elif (
                        "maintain the target range" in decision_lower
                        or "keep the target range" in decision_lower
                    ):
                        decision = "Rate Hold"

                    else:
                        decision = "Unclassified"

                    results.append({
                        "Date": item["Date"],
                        "Decision": decision,
                        "Decision Details": decision_text,
                        "Title": item["Title"],
                        "Link": link
                    })

                except Exception as e:

                    print(
                        f"Statement retrieval error for {link}: {e}"
                    )

        except Exception as e:

            print(f"FOMC archive error for {year}: {e}")

    return pd.DataFrame(results)

def calculate_fed_policy_bias(asset):

    history = load_fomc_statement_history(years=1)

    if history.empty:
        return "Neutral"

    latest_decision = history.iloc[0]["Decision"]

    if asset == "USD":

        if latest_decision == "Rate Hike":
            return "Bullish"

        elif latest_decision == "Rate Cut":
            return "Bearish"

    elif asset == "XAUUSD":

        if latest_decision == "Rate Hike":
            return "Bearish"

        elif latest_decision == "Rate Cut":
            return "Bullish"

    return "Neutral"

@st.cache_data(ttl=3600)
@st.cache_data(ttl=3600)
def load_cot_market_data(dataset_id, market_keyword):

    url = (
        f"https://publicreporting.cftc.gov/resource/"
        f"{dataset_id}.json"
    )

    params = {
        "$where": (
            f"upper(market_and_exchange_names) "
            f"like '%{market_keyword.upper()}%'"
        ),
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 100
    }

    headers = {
        "User-Agent": "JN-Capital-Research/1.0"
    }

    for attempt in range(3):

        try:

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=60
            )

            response.raise_for_status()

            data = response.json()

            if not data:
                return pd.DataFrame()

            return pd.DataFrame(data)

        except requests.exceptions.RequestException:

            if attempt == 2:
                st.warning(
                    "CFTC server temporarily unavailable. "
                    "Please try again later."
                )

    return pd.DataFrame()

def calculate_cot_positioning(data):

    if data.empty:
        return None

    df = data.copy()
    if "market_and_exchange_names" in df.columns:

        df["open_interest_all"] = pd.to_numeric(
            df["open_interest_all"], errors="coerce"
        )

        latest_date = df["report_date_as_yyyy_mm_dd"].max()

        latest_rows = df[
            df["report_date_as_yyyy_mm_dd"] == latest_date
        ]

        if not latest_rows.empty:

            main_market = (
                latest_rows.groupby("market_and_exchange_names")[
                    "open_interest_all"
                ].max().idxmax()
            )

            df = df[
                df["market_and_exchange_names"] == main_market
            ].copy()

    numeric_columns = [
        "m_money_positions_long_all",
        "m_money_positions_short_all"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

    df["Net Position"] = (
        df["m_money_positions_long_all"]
        - df["m_money_positions_short_all"]
    )

    df["Report Date"] = pd.to_datetime(
        df["report_date_as_yyyy_mm_dd"]
    )

    df = df.sort_values("Report Date")

    latest = df.iloc[-1]

    net_position = latest["Net Position"]

    weekly_change = (
        net_position - df.iloc[-2]["Net Position"]
        if len(df) >= 2 else None
    )

    history = df["Net Position"].tail(52)

    if len(history) >= 2 and history.max() != history.min():

        cot_index = (
            (net_position - history.min())
            / (history.max() - history.min())
        ) * 100

    else:
        cot_index = None

    if cot_index is None:
        bias = "Insufficient Data"

    elif cot_index >= 60:
        bias = "Bullish"

    elif cot_index <= 40:
        bias = "Bearish"

    else:
        bias = "Neutral"

    return {
        "Report Date": latest["Report Date"].strftime("%d %b %Y"),
        "Managed Money Long": int(latest["m_money_positions_long_all"]),
        "Managed Money Short": int(latest["m_money_positions_short_all"]),
        "Net Position": int(net_position),
        "Weekly Change": (
            int(weekly_change)
            if weekly_change is not None else None
        ),
        "COT Index": (
            round(cot_index, 1)
            if cot_index is not None else None
        ),
        "Institutional Bias": bias,
        "History": df[["Report Date", "Net Position"]].copy()
    }

@st.cache_data(ttl=900)
def load_market_ohlc(
    symbol="XAUUSD",
    timeframe="H1",
    days=30
):

    from datetime import timedelta

    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=days)

    url = "https://www.algospecial.com/api/ohlc.php"

    params = {
        "symbol": symbol,
        "tf": timeframe,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "format": "json"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        payload = response.json()

        df = pd.DataFrame(
            payload.get("data", [])
        )

        if df.empty:
            return pd.DataFrame()

        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"],
            errors="coerce"
        )

        for column in ["Open", "High", "Low", "Close"]:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df = df.dropna(
            subset=[
                "Timestamp",
                "Open",
                "High",
                "Low",
                "Close"
            ]
        )

        return df.sort_values(
            "Timestamp"
        ).reset_index(drop=True)

    except Exception as e:

        print(f"Market data error: {e}")

        return pd.DataFrame()

@st.cache_data(ttl=900)
def load_gold_daily_ohlc(days=30):

    from datetime import timedelta

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    url = "https://api.goldprice.dev/v1/bars"

    params = {
        "symbol": "XAU-USD-SPOT",
        "interval": "1d",
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "limit": 100
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        payload = response.json()

        df = pd.DataFrame(
            payload.get("bars", [])
        )

        if df.empty:
            return pd.DataFrame()

        df["Timestamp"] = pd.to_datetime(
            df["bar_start"],
            errors="coerce",
            utc=True
        )

        for column in ["open", "high", "low", "close"]:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df = df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close"
        })

        df = df.dropna(
            subset=[
                "Timestamp",
                "Open",
                "High",
                "Low",
                "Close"
            ]
        )

        df = df[df["is_closed"] == True]

        return df.sort_values(
            "Timestamp"
        ).reset_index(drop=True)

    except Exception as e:

        print(f"Gold daily data error: {e}")

        return pd.DataFrame()

@st.cache_data(ttl=900)
def load_biquote_ohlc(
    symbol="XAUUSD",
    timeframe="1d",
    limit=500
):

    url = f"https://biquote.io/api/{symbol}/ohlc"

    params = {
        "interval": timeframe,
        "limit": limit
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        payload = response.json()

        bars = payload.get("bars", [])

        # Exclude candles that have not closed
        bars = [
            bar for bar in bars
            if not bar.get("isOpen", False)
        ]

        df = pd.DataFrame(bars)

        if df.empty:
            return pd.DataFrame()

        df["Timestamp"] = pd.to_datetime(
            df["openTime"],
            errors="coerce",
            utc=True
        )

        for column in ["open", "high", "low", "close"]:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df = df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close"
        })

        df = df.dropna(
            subset=[
                "Timestamp",
                "Open",
                "High",
                "Low",
                "Close"
            ]
        )

        return df.sort_values(
            "Timestamp"
        ).reset_index(drop=True)

    except Exception as e:

        print(f"BiQuote market data error: {e}")

        return pd.DataFrame()


def calculate_technical_indicators(df):

    if df.empty or len(df) < 50:
        return None

    df = df.copy()

    # Moving averages
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA100"] = df["Close"].rolling(100).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    # RSI 14
    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/14,
        min_periods=14,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/14,
        min_periods=14,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))

    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = df["Close"].ewm(
        span=26,
        adjust=False
    ).mean()

    df["MACD"] = ema12 - ema26

    df["MACD_SIGNAL"] = df["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    df["MACD_HIST"] = (
        df["MACD"] - df["MACD_SIGNAL"]
    )

    # Price momentum
    df["MOMENTUM"] = df["Close"].pct_change(10) * 100

    return df

def calculate_technical_score(df):

    if df is None or df.empty:
        return None

    latest = df.iloc[-1]

    required = [
        "Close",
        "SMA20",
        "SMA50",
        "SMA200",
        "RSI",
        "MACD",
        "MACD_SIGNAL",
        "MACD_HIST",
        "MOMENTUM"
    ]

    if any(pd.isna(latest[column]) for column in required):
        return None

    price = latest["Close"]

    # --------------------------------
    # 1. MOVING AVERAGE STRUCTURE (35%)
    # --------------------------------

    ma_signals = [
        100 if price > latest["SMA20"] else 0,
        100 if price > latest["SMA50"] else 0,
        100 if price > latest["SMA200"] else 0
    ]

    alignment_signal = (
        100 if latest["SMA20"] > latest["SMA50"] > latest["SMA200"]
        else 0 if latest["SMA20"] < latest["SMA50"] < latest["SMA200"]
        else 50
    )

    moving_average_score = (
        sum(ma_signals) + alignment_signal
    ) / 4

    # --------------------------------
    # 2. RSI (20%)
    # --------------------------------

    rsi = latest["RSI"]

    if rsi < 20:
        rsi_score = 30
        rsi_condition = "EXTREMELY OVERSOLD"

    elif rsi < 30:
        rsi_score = 30 + (rsi - 20)
        rsi_condition = "OVERSOLD"

    elif rsi < 50:
        rsi_score = 40 + (rsi - 30) * 0.5
        rsi_condition = "BEARISH MOMENTUM"

    elif rsi <= 60:
        rsi_score = 50 + (rsi - 50)
        rsi_condition = "NEUTRAL"

    elif rsi <= 70:
        rsi_score = 60 + (rsi - 60)
        rsi_condition = "BULLISH MOMENTUM"

    else:
        rsi_score = 70
        rsi_condition = "OVERBOUGHT"

    rsi_score = max(0, min(100, rsi_score))

    macd_score = (
        (100 if latest["MACD"] > 0 else 0)
        +
        (100 if latest["MACD"] > latest["MACD_SIGNAL"] else 0)
        +
        (100 if latest["MACD_HIST"] > 0 else 0)
    ) / 3

    # --------------------------------
    # 4. PRICE MOMENTUM (20%)
    # --------------------------------

    momentum_score = max(
        0,
        min(100, 50 + latest["MOMENTUM"] * 5)
    )

    # --------------------------------
    # OVERALL TECHNICAL SCORE
    # --------------------------------

    technical_score = round(
        moving_average_score * 0.35
        + rsi_score * 0.20
        + macd_score * 0.25
        + momentum_score * 0.20
    )

    # --------------------------------
    # MARKET DIRECTION
    # --------------------------------

    if technical_score >= 80:
        technical_bias = "VERY BULLISH"

    elif technical_score >= 60:
        technical_bias = "BULLISH"

    elif technical_score >= 41:
        technical_bias = "NEUTRAL"

    elif technical_score >= 21:
        technical_bias = "BEARISH"

    else:
        technical_bias = "VERY BEARISH"

    return {
        "score": technical_score,
        "bias": technical_bias,
        "moving_average_score": round(moving_average_score),
        "rsi_score": round(rsi_score),
        "macd_score": round(macd_score),
        "momentum_score": round(momentum_score),
        "rsi": round(latest["RSI"], 2),
        "rsi_condition": rsi_condition,
        "rsi_score": round(rsi_score),
        "close": round(price, 3),
        "timestamp": latest["Timestamp"],
        "sma20": round(latest["SMA20"], 3),
        "sma50": round(latest["SMA50"], 3),
        "sma200": round(latest["SMA200"], 3)
    }

# ==========================================
# JN CAPITAL MULTI-TIMEFRAME ANALYSIS
# ==========================================

def calculate_timeframe_score(df):

    if df is None or df.empty:
        return None

    latest = df.iloc[-1]

    # --------------------------------------
    # MOVING AVERAGE ANALYSIS
    # --------------------------------------

    ma_columns = [
        "SMA20",
        "SMA50",
        "SMA100",
        "SMA200"
    ]

    available_mas = [
        column for column in ma_columns
        if pd.notna(latest[column])
    ]

    if not available_mas:
        return None

    price = latest["Close"]

    ma_signals = [
        100 if price > latest[column] else 0
        for column in available_mas
    ]

    moving_average_score = sum(ma_signals) / len(ma_signals)

    # --------------------------------------
    # RSI ANALYSIS
    # --------------------------------------

    rsi = latest["RSI"]

    if pd.isna(rsi):
        return None

    if rsi < 20:
        rsi_score = 30
        rsi_condition = "EXTREMELY OVERSOLD"

    elif rsi < 30:
        rsi_score = 30 + (rsi - 20)
        rsi_condition = "OVERSOLD"

    elif rsi < 50:
        rsi_score = 40 + (rsi - 30) * 0.5
        rsi_condition = "BEARISH MOMENTUM"

    elif rsi <= 60:
        rsi_score = 50 + (rsi - 50)
        rsi_condition = "NEUTRAL"

    elif rsi <= 70:
        rsi_score = 60 + (rsi - 60)
        rsi_condition = "BULLISH MOMENTUM"

    else:
        rsi_score = 70
        rsi_condition = "OVERBOUGHT"

    # --------------------------------------
    # MACD ANALYSIS
    # --------------------------------------

    macd_score = (
        (100 if latest["MACD"] > 0 else 0)
        +
        (100 if latest["MACD"] > latest["MACD_SIGNAL"] else 0)
        +
        (100 if latest["MACD_HIST"] > 0 else 0)
    ) / 3

    # --------------------------------------
    # PRICE MOMENTUM
    # --------------------------------------

    momentum = latest["MOMENTUM"]

    if pd.isna(momentum):
        return None

    momentum_score = max(
        0,
        min(100, 50 + momentum * 5)
    )

    # --------------------------------------
    # FINAL TIMEFRAME SCORE
    # --------------------------------------

    score = round(
        moving_average_score * 0.35
        + rsi_score * 0.20
        + macd_score * 0.25
        + momentum_score * 0.20
    )

    if score >= 80:
        bias = "VERY BULLISH"

    elif score >= 60:
        bias = "BULLISH"

    elif score >= 41:
        bias = "NEUTRAL"

    elif score >= 21:
        bias = "BEARISH"

    else:
        bias = "VERY BEARISH"

    return {
        "score": score,
        "bias": bias,
        "close": round(price, 3),
        "rsi": round(rsi, 2),
        "rsi_condition": rsi_condition,
        "moving_average_score": round(moving_average_score),
        "rsi_score": round(rsi_score),
        "macd_score": round(macd_score),
        "momentum_score": round(momentum_score),
        "timestamp": latest["Timestamp"],
        "available_moving_averages": available_mas
    }


# ==========================================
# MULTI-TIMEFRAME COMBINED ANALYSIS
# ==========================================

@st.cache_data(ttl=900)
def calculate_multi_timeframe_analysis(symbol="XAUUSD"):

    timeframes = {
        "Daily": {
            "interval": "1d",
            "weight": 0.50
        },
        "H4": {
            "interval": "4h",
            "weight": 0.30
        },
        "H1": {
            "interval": "1h",
            "weight": 0.20
        }
    }

    results = {}

    for name, settings in timeframes.items():

        df = load_biquote_ohlc(
            symbol,
            settings["interval"],
            500
        )

        indicators = calculate_technical_indicators(df)

        result = calculate_timeframe_score(indicators)

        results[name] = result

    # --------------------------------------
    # CHECK DATA AVAILABILITY
    # --------------------------------------

    if any(result is None for result in results.values()):
        return None

    # --------------------------------------
    # COMBINE TIMEFRAME SCORES
    # --------------------------------------

    combined_score = round(
        results["Daily"]["score"] * 0.50
        + results["H4"]["score"] * 0.30
        + results["H1"]["score"] * 0.20
    )

    if combined_score >= 80:
        overall_bias = "VERY BULLISH"

    elif combined_score >= 60:
        overall_bias = "BULLISH"

    elif combined_score >= 41:
        overall_bias = "NEUTRAL"

    elif combined_score >= 21:
        overall_bias = "BEARISH"

    else:
        overall_bias = "VERY BEARISH"

    # --------------------------------------
    # TIMEFRAME AGREEMENT
    # --------------------------------------

    biases = [
        results["Daily"]["bias"],
        results["H4"]["bias"],
        results["H1"]["bias"]
    ]

    if all("BULLISH" in bias for bias in biases):
        alignment = "ALL TIMEFRAMES BULLISH"

    elif all("BEARISH" in bias for bias in biases):
        alignment = "ALL TIMEFRAMES BEARISH"

    else:
        alignment = "MIXED TIMEFRAME SIGNALS"

    return {
        "symbol": symbol,
        "score": combined_score,
        "bias": overall_bias,
        "alignment": alignment,
        "timeframes": results
    }
