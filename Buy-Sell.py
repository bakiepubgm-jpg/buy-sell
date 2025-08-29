import streamlit as st
import requests
from datetime import datetime, time, timedelta
import pytz
import pandas as pd

from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 15 seconds
count = st_autorefresh(interval=120 * 1000, limit=None, key="gold_autorefresh")

# -------------------------------
# App Config
# -------------------------------
st.set_page_config(page_title="XAU/USD Structure", layout="centered")
st.title("📈 Gold (XAU/USD) HL Structure Calculator")

# -------------------------------
# Footer (your signature)
# -------------------------------
def footer():
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f0f2f6;
            color: #333;
            text-align: center;
            padding: 10px 0;
            font-weight: bold;
            font-family: 'Courier New', Courier, monospace;
        }
        </style>
        <div class="footer">© All Rights Reserved to Umer Farid</div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------
# GoldAPI Key & Headers
# -------------------------------
GOLD_API_KEY = "goldapi-aled0dsmewedm0p-io"  # replace with your key if needed
HEADERS = {
    "x-access-token": GOLD_API_KEY,
    "Content-Type": "application/json"
}

# -------------------------------
# Get Real-Time Gold Price
# -------------------------------
@st.cache_data(ttl=1)  # refresh every 60 seconds
def get_gold_price():
    url = "https://www.goldapi.io/api/XAU/USD"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        return {
            "price": data["price"],
            "high": data["high_price"],
            "low": data["low_price"],
            "open": data["open_price"]
        }
    except Exception as e:
        st.error(f"Error fetching gold price: {e}")
        return None

# -------------------------------
# HL Swept Logic
# -------------------------------
def swept_logic(hh, prev_high, ll):
    dif = (hh - ll) / 2
    hl_idm = hh - dif
    dif2 = hh - prev_high

    if dif2 <= 0:
        return None, "❌ HH must be greater than Previous High."

    buy_areas = [ll - i * dif2 for i in range(1, 4)]
    t1 = ll - buy_areas[0]
    resistances = [hh + i * t1 for i in range(1, 5)]

    if hh > prev_high and ll > prev_high:
        trend = "Strong Uptrend"
    elif hh > prev_high:
        trend = "Moderate Uptrend"
    elif hh < prev_high and ll < prev_high:
        trend = "Downtrend"
    else:
        trend = "Ranging / Unclear"

    return {
        "Trend": trend,
        "HL/IDM": hl_idm,
        "Dif2": dif2,
        "Buy Areas": buy_areas,
        "t1": t1,
        "Resistances": resistances
    }, None

# -------------------------------
# HL Broken Logic
# -------------------------------
def broken_logic(hh, prev_high, ll):
    dif = (hh - ll) / 2
    hl_break = ll + dif
    sell_areas = [hh + i * dif for i in range(1, 4)]
    t1 = sell_areas[0] - hh
    supports = [ll - i * t1 for i in range(1, 4)]

    if hh < prev_high and ll < prev_high:
        trend = "Downtrend (HL broken)"
    elif hh > prev_high and ll < prev_high:
        trend = "Potential Reversal"
    else:
        trend = "Unclear / Choppy"

    return {
        "Trend": trend,
        "HL Break Zone": hl_break,
        "Sell Areas": sell_areas,
        "t1": t1,
        "Supports": supports
    }, None

# -------------------------------
# Session definitions in UTC
# -------------------------------
SESSIONS_UTC = {
    "Asia": {"start": time(0, 0), "end": time(9, 0)},       # 00:00 - 09:00 UTC
    "London": {"start": time(7, 0), "end": time(16, 0)},   # 07:00 - 16:00 UTC
    "New York": {"start": time(12, 0), "end": time(21, 0)} # 12:00 - 21:00 UTC
}

# -------------------------------
# Timezone options
# -------------------------------
TIMEZONES = {
    "Karachi (UTC+5)": "Asia/Karachi",
    "London (UTC+1 BST)": "Europe/London",
    "New York (UTC-4 EDT)": "America/New_York"
}

# -------------------------------
# Utility: Format time to 12-hour in user tz
# -------------------------------
def format_time(dt_utc, user_tz):
    dt_local = dt_utc.astimezone(user_tz)
    return dt_local.strftime("%I:%M %p")

# -------------------------------
# Detect current session based on UTC now
# -------------------------------
def get_current_session(now_utc):
    for sess_name, times in SESSIONS_UTC.items():
        start_dt = datetime.combine(now_utc.date(), times["start"], tzinfo=pytz.UTC)
        end_dt = datetime.combine(now_utc.date(), times["end"], tzinfo=pytz.UTC)
        # handle overnight session crossing midnight
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        if start_dt <= now_utc < end_dt:
            return sess_name, start_dt, end_dt
    return "Closed", None, None

# -------------------------------
# Main app
# -------------------------------

# Timezone selector
st.sidebar.title("Settings")
tz_name = st.sidebar.selectbox("Select Timezone", options=list(TIMEZONES.keys()), index=0)
tz = pytz.timezone(TIMEZONES[tz_name])

# Get live gold price
gold_data = get_gold_price()
if not gold_data:
    st.stop()

price = gold_data["price"]
high_price = gold_data["high"]
low_price = gold_data["low"]
open_price = gold_data["open"]

# Display live gold price on top with open/high/low as caption below price
st.subheader("💰 Live Gold Price (XAU/USD)")
col1, col2, col3, col4 = st.columns([2,1,1,1])
col1.markdown(
    f"""
    <div style="font-size:24px; font-weight:bold; color:#007ACC; margin-bottom:4px;">
        Current XAU/USD: ${price:.2f}
    </div>
    <div style="
        font-size:14px; 
        font-style: italic; 
        font-weight: 600;
        color: #007ACC;  
        line-height: 1.1;
        margin: 0;
    ">
        Open: <span style='color:#FF5733;'>${open_price:.2f}</span> &nbsp;&nbsp;&nbsp; 
        High: <span style='color:#28B463;'>${high_price:.2f}</span> &nbsp;&nbsp;&nbsp; 
        Low: <span style='color:#C70039;'>${low_price:.2f}</span>
    </div>
    """,
    unsafe_allow_html=True
)



col2.empty()
col3.empty()
col4.empty()

# Current time UTC now
now_utc = datetime.now(pytz.UTC)

# Get current session info
current_session, sess_start_utc, sess_end_utc = get_current_session(now_utc)

# Prepare session times data for display
session_rows = []
for sess_name, times in SESSIONS_UTC.items():
    start_dt = datetime.combine(now_utc.date(), times["start"], tzinfo=pytz.UTC)
    end_dt = datetime.combine(now_utc.date(), times["end"], tzinfo=pytz.UTC)
    # Handle overnight sessions that cross midnight
    if end_dt < start_dt:
        end_dt += timedelta(days=1)

    session_rows.append({
        "Session": sess_name,
        "Start Time": format_time(start_dt, tz),
        "End Time": format_time(end_dt, tz),
        "Current": "✅" if sess_name == current_session else ""
    })

df_sessions = pd.DataFrame(session_rows)

def highlight_current(s):
    return ['background-color: lightgreen' if v == '✅' else '' for v in s]

st.markdown(f"### Current Time: {datetime.now(tz).strftime('%I:%M %p')}")
st.markdown(f"### Session Times (Timezone: {tz_name})")
st.dataframe(df_sessions.style.apply(highlight_current, subset=['Current']), use_container_width=True)

# -------------------------------
# Input Mode
# -------------------------------
st.subheader("📥 Input Price Structure")
auto_mode = st.checkbox("Auto-fill using live market data", value=True)

if auto_mode:
    hh = st.number_input("Higher High (HH)", value=high_price, format="%.2f")
    ll = st.number_input("Lower Low (LL)", value=low_price, format="%.2f")
    prev_high = st.number_input("Previous High", value=open_price, format="%.2f")
else:
    hh = st.number_input("Higher High (HH)", value=0.0, format="%.2f")
    ll = st.number_input("Lower Low (LL)", value=0.0, format="%.2f")
    prev_high = st.number_input("Previous High", value=0.0, format="%.2f")

hl_status = st.selectbox("HL Status", ["Buy", "Sell"])

# -------------------------------
# Calculate Button
# -------------------------------
if st.button("🔍 Analyze"):

    if hl_status == "swept":
        result, error = swept_logic(hh, prev_high, ll)
        if error:
            st.error(error)
        else:
            st.success(f"📈 Market Trend: {result['Trend']}")
            data = {
                "Metric": [
                    "HL/IDM", "Dif2",
                    "Buy Area 1", "Buy Area 2", "Buy Area 3",
                    "Resistance 1", "Resistance 2", "Resistance 3", "Resistance 4"
                ],
                "Value": [
                    f"{result['HL/IDM']:.2f}", f"{result['Dif2']:.2f}",
                    f"{result['Buy Areas'][0]:.2f}", f"{result['Buy Areas'][1]:.2f}", f"{result['Buy Areas'][2]:.2f}",
                    f"{result['Resistances'][0]:.2f}", f"{result['Resistances'][1]:.2f}",
                    f"{result['Resistances'][2]:.2f}", f"{result['Resistances'][3]:.2f}"
                ]
            }
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

    else:
        result, error = broken_logic(hh, prev_high, ll)
        if error:
            st.error(error)
        else:
            st.success(f"📉 Market Trend: {result['Trend']}")
            data = {
                "Metric": [
                    "HL Break Zone",
                    "Sell Area 1", "Sell Area 2", "Sell Area 3",
                    "Support 1", "Support 2", "Support 3"
                ],
                "Value": [
                    f"{result['HL Break Zone']:.2f}",
                    f"{result['Sell Areas'][0]:.2f}", f"{result['Sell Areas'][1]:.2f}", f"{result['Sell Areas'][2]:.2f}",
                    f"{result['Supports'][0]:.2f}", f"{result['Supports'][1]:.2f}", f"{result['Supports'][2]:.2f}"
                ]
            }
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

footer()

