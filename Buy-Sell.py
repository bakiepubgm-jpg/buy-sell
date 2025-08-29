import streamlit as st
import requests
from datetime import datetime

# -------------------------------
# App Config
# -------------------------------
st.set_page_config(page_title="XAU/USD Structure", layout="centered")
st.title("📈 Gold (XAU/USD) HL Structure Calculator")

# -------------------------------
# GoldAPI Key
# -------------------------------
GOLD_API_KEY = "goldapi-aled0dsmewedm0p-io"
HEADERS = {
    "x-access-token": GOLD_API_KEY,
    "Content-Type": "application/json"
}

# -------------------------------
# Get Real-Time Gold Price
# -------------------------------
@st.cache_data(ttl=300)
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
# Display Real-Time Price
# -------------------------------
st.subheader("💰 Live Gold Price")
gold_data = get_gold_price()

if not gold_data:
    st.stop()

price = gold_data["price"]
high_price = gold_data["high"]
low_price = gold_data["low"]
open_price = gold_data["open"]

st.metric("Current XAU/USD", f"${price:.2f}")
st.caption(f"High: ${high_price:.2f} | Low: ${low_price:.2f} | Open: ${open_price:.2f}")

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

hl_status = st.selectbox("HL Status", ["swept", "broken"])
if st.button("🔍 Calculate"):

    if hl_status == "swept":
        result, error = swept_logic(hh, prev_high, ll)
        if error:
            st.error(error)
        else:
            st.success(f"📈 Market Trend: {result['Trend']}")
            st.markdown(f"**HL/IDM**: `{result['HL/IDM']:.2f}`")
            st.markdown(f"**Dif2**: `{result['Dif2']:.2f}`")
            st.subheader("🔽 Buy Zones")
            for i, val in enumerate(result["Buy Areas"], 1):
                st.write(f"Buy Area {i}: **{val:.2f}**")
            st.subheader("🔼 Resistances")
            for i, val in enumerate(result["Resistances"], 1):
                st.write(f"Resistance {i}: **{val:.2f}**")
    else:
        result, error = broken_logic(hh, prev_high, ll)
        if error:
            st.error(error)
        else:
            st.success(f"📉 Market Trend: {result['Trend']}")
            st.markdown(f"**HL Break Zone**: `{result['HL Break Zone']:.2f}`")
            st.subheader("🔼 Sell Zones")
            for i, val in enumerate(result["Sell Areas"], 1):
                st.write(f"Sell Area {i}: **{val:.2f}**")
            st.subheader("🔽 Supports")
            for i, val in enumerate(result["Supports"], 1):
                st.write(f"Support {i}: **{val:.2f}**")
