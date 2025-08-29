import streamlit as st
from datetime import datetime

st.set_page_config(page_title="HL Structure Calculator", layout="centered")

st.title("📈 HL Market Structure Calculator")
st.markdown("Supports both **Swept** and **Broken** HL logic")

# --- User Inputs ---
hl_status = st.selectbox("HL Status", ["swept", "broken"])
hh = st.number_input("Enter Higher High (HH)", min_value=0.0, format="%.2f")
prev_high = st.number_input("Enter Previous High", min_value=0.0, format="%.2f")
ll = st.number_input("Enter Lower Low (LL)", min_value=0.0, format="%.2f")

calculate = st.button("🔍 Calculate")

def swept_logic(hh, prev_high, ll):
    dif = (hh - ll) / 2
    hl_idm = hh - abs(dif)
    dif2 = hh - prev_high
    if dif2 <= 0:
        return None, "❌ HH must be greater than Previous High for 'swept' logic."

    buy_area1 = ll - dif2
    buy_area2 = buy_area1 - dif2
    buy_area3 = buy_area2 - dif2
    t1 = ll - buy_area1
    res1 = hh + t1
    res2 = res1 + t1
    res3 = res2 + t1
    res4 = res3 + t1

    # Trend
    if hh > prev_high and ll > prev_high:
        trend = "Strong Uptrend"
    elif hh > prev_high and ll > 0:
        trend = "Uptrend"
    elif hh < prev_high and ll < prev_high:
        trend = "Downtrend"
    else:
        trend = "Ranging / Unclear"

    return {
        "Trend": trend,
        "HL/IDM": hl_idm,
        "Dif": dif,
        "Dif2": dif2,
        "Buy Areas": [buy_area1, buy_area2, buy_area3],
        "t1": t1,
        "Resistances": [res1, res2, res3, res4]
    }, None

def broken_logic(hh, prev_high, ll):
    dif = (hh - ll) / 2
    hl_break = ll + dif
    sell_area1 = hh + dif
    sell_area2 = sell_area1 + dif
    sell_area3 = sell_area2 + dif
    t1 = sell_area1 - hh
    sup1 = ll - t1
    sup2 = sup1 - t1
    sup3 = sup2 - t1

    # Trend
    if hh < prev_high and ll < prev_high:
        trend = "Downtrend (HL broken)"
    elif hh > prev_high and ll < prev_high:
        trend = "Potential Reversal"
    else:
        trend = "Unclear / Choppy"

    return {
        "Trend": trend,
        "HL Break Zone": hl_break,
        "Dif": dif,
        "Sell Areas": [sell_area1, sell_area2, sell_area3],
        "t1": t1,
        "Supports": [sup1, sup2, sup3]
    }

# --- Run Logic ---
if calculate:
    if hl_status == "swept":
        result, error = swept_logic(hh, prev_high, ll)
        if error:
            st.error(error)
        else:
            st.success(f"📈 Trend: {result['Trend']}")
            st.markdown(f"**HL/IDM**: {result['HL/IDM']:.2f}  \n**Dif2**: {result['Dif2']:.2f}")
            st.markdown("### 🔽 Buy Areas")
            for i, val in enumerate(result["Buy Areas"], 1):
                st.markdown(f"Buy Area {i}: **{val:.2f}**")
            st.markdown("### 🔼 Resistance Levels")
            for i, val in enumerate(result["Resistances"], 1):
                st.markdown(f"Resistance {i}: **{val:.2f}**")
    else:
        result = broken_logic(hh, prev_high, ll)
        st.success(f"📉 Trend: {result['Trend']}")
        st.markdown(f"**HL Break Zone**: {result['HL Break Zone']:.2f}  \n**Dif**: {result['Dif']:.2f}")
        st.markdown("### 🔼 Sell Areas")
        for i, val in enumerate(result["Sell Areas"], 1):
            st.markdown(f"Sell Area {i}: **{val:.2f}**")
        st.markdown("### 🔽 Support Levels")
        for i, val in enumerate(result["Supports"], 1):
            st.markdown(f"Support {i}: **{val:.2f}**")
