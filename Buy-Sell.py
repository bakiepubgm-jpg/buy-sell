import streamlit as st
import requests
from datetime import datetime

# Set up Streamlit page
st.set_page_config(page_title="XAU/USD HL Structure", layout="centered")
st.title("📊 Gold HL Structure Calculator")

# === GoldAPI settings ===
GOLD_API_KEY = "goldapi-aled0dsmewedm0p-io"
HEADERS = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}

# === Fetch real-time gold spot price ===
def get_real_time_price():
    url = "https://www.goldapi.io/api/XAU/USD"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["price"], data["high_price"], data["low_price"], data["open_price"]
        else:
            st.warning(f"API Error: {response.status_code} - {response.text}")
            return None, None, None, None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None, None, None, None

# === HL logic functions ===
def swept_logic(hh, prev_high, ll):
    dif = (hh - ll) / 2
    hl_idm = hh - dif
    dif2 = hh - prev_high

    if dif2 <= 0:
        return None, "❌ HH must be greater than Previous High for 'swept' logic."

    buy_areas = [ll - i * dif2 for i in range(1, 4)]
    t1 = ll - buy_areas[0]
    resistances = [hh + i * t1 for i in range(1, 5)]

    # Trend identification
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

# === Display real-time price ===
st.subheader("💰 Real-Time XAU/USD Spot Price")
price, high_price, low_price, open_price = get_real_time_price()

if price:
    st.metric(label="Current XAU/USD", value=f"${price:.2f}")
    st.caption(f"High: {high_price}, Low: {low_price}, Open: {open_price}")
else:
    st.stop()

# === Input section ===
st.subheader("📥 Price Input")

use_auto = st.checkbox("Auto-fill values from GoldAPI", value=True)

if use_auto and high_price and low_price and open_price:
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
    else:
        result, error = broken_logic(hh, prev_high, ll)

    if error:
        st.error(error)
    else:
        st.success(f"📈 Market Trend: {result['Trend']}")

        if hl_status == "swept":
            st.subheader("🔽 Buy Zones")
            for i, price in enumerate(result["Buy Areas"], 1):
                st.write(f"Buy Area {i}: **{price:.2f}**")

            st.subheader("🔼 Resistances")
            for i, res in enumerate(result["Resistances"], 1):
                st.write(f"Resistance {i}: **{res:.2f}**")

            st.markdown(f"**HL/IDM**: `{result['HL/IDM']:.2f}`  |  **Dif2**: `{result['Dif2']:.2f}`")
        else:
            st.subheader("🔼 Sell Zones")
            for i, price in enumerate(result["Sell Areas"], 1):
                st.write(f"Sell Area {i}: **{price:.2f}**")

            st.subheader("🔽 Supports")
            for i, sup in enumerate(result["Supports"], 1):
                st.write(f"Support {i}: **{sup:.2f}**")

            st.markdown(f"**HL Break Zone**: `{result['HL Break Zone']:.2f}`")
