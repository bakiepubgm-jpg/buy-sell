import streamlit as st
import pandas as pd

# Set page title
st.set_page_config(page_title="HH/LL Buy & Resistance Calculator", layout="centered")
st.title("📊 HH / LL Structure Calculator")

# Input fields
hh = st.number_input("Enter Higher High (HH)", format="%.2f")
ll = st.number_input("Enter Lower Low (LL)", format="%.2f")

# Perform calculation
if hh > ll:
    dif = hh - ll
    idm = dif / 2
    factor = 1.4  # 140%

    # Buy levels
    buy1 = hh - (factor * idm)
    buy2 = buy1 - (factor * idm)
    buy3 = buy2 - (factor * idm)

    # Resistance levels
    res1 = hh + (factor * idm)
    res2 = res1 + (factor * idm)
    res3 = res2 + (factor * idm)

    # Display in table
    results = {
        "Metric": [
            "DIF (HH - LL)",
            "IDM (DIF / 2)",
            "Buy 1", "Buy 2", "Buy 3",
            "Resistance 1", "Resistance 2", "Resistance 3"
        ],
        "Value": [
            f"{dif:.2f}", f"{idm:.2f}",
            f"{buy1:.2f}", f"{buy2:.2f}", f"{buy3:.2f}",
            f"{res1:.2f}", f"{res2:.2f}", f"{res3:.2f}"
        ]
    }

    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ Please ensure HH is greater than LL to calculate.")
