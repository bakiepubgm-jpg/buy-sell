import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
# CSV file path
csv_file = "dataset.csv"

karachi_tz = pytz.timezone("Asia/Karachi")
# Columns for dataset
columns = [
    "DateTime", "Session", "Mode", "HH", "LL", "PLL", "RLL",
    "Buy1", "Buy2", "Buy3",
    "Resistance1", "Resistance2", "Resistance3",
    "Sell1", "Sell2", "Sell3",
    "Notes"
]

# Ensure file exists with headers
if not os.path.exists(csv_file):
    pd.DataFrame(columns=columns).to_csv(csv_file, index=False)


# ---------- Helper: Detect Session ----------
def detect_session():
    now = datetime.now().hour
    if 0 <= now < 8:
        return "Asia"
    elif 8 <= now < 16:
        return "London"
    else:
        return "New York"


# ---------- Sidebar Inputs ----------
st.set_page_config(page_title="USTEC / NAS100 / NASDAQ Buy & Sell Calculator", layout="centered")
st.title("📊 USTEC / NAS100 / NASDAQ")
st.markdown("<p style='font-size:12px;color:gray;'>Umer Farid</p>", unsafe_allow_html=True)
mode = st.radio("Select Mode", ["Buy", "Sell"])

# ✅ Detect session automatically
auto_session = detect_session()

# ✅ Pre-select auto_session in dropdown
session = st.selectbox(
    "Select Session (override if needed)",
    ["Asia", "London", "New York"],
    index=["Asia", "London", "New York"].index(auto_session)
)

hh = st.number_input("Enter Higher High (HH)", format="%.2f")
ll = st.number_input("Enter Lower Low (LL)", format="%.2f")

pll = rll = None
if mode == "Sell":
    pll = st.number_input("Enter Previous Lower Low (PLL)", format="%.2f")
    rll = st.number_input("Enter Recent Lower Low (RLL)", format="%.2f")

# Notes
notes = st.text_area("Add Notes (optional)")


# ---------- Calculate ----------
if st.button("Calculate"):
    if mode == "Buy" and hh > ll:
        dif = hh - ll
        idm = dif / 2
        factor = 1.4

        buy1 = hh - (factor * idm)
        buy2 = buy1 - (factor * idm)
        buy3 = buy2 - (factor * idm)

        res1 = hh + (factor * idm)
        res2 = res1 + (factor * idm)
        res3 = res2 + (factor * idm)

        sell1 = sell2 = sell3 = None

    elif mode == "Sell" and pll and rll and pll > rll:
        dif = pll - rll
        idm = None

        sell1 = hh + dif
        sell2 = sell1 + dif
        sell3 = sell2 + dif

        buy1 = buy2 = buy3 = res1 = res2 = res3 = None
    else:
        st.warning("⚠️ Invalid inputs. Please check values.")
        st.stop()
        
    # Prepare row for saving
    results_save = {
        "DateTime": datetime.now(karachi_tz).strftime("%Y-%m-%d %H:%M:%S %Z"),
        "Session": session,  # ✅ always stored
        "Mode": mode,
        "HH": hh, "LL": ll, "PLL": pll, "RLL": rll,
        "Buy1": buy1, "Buy2": buy2, "Buy3": buy3,
        "Resistance1": res1, "Resistance2": res2, "Resistance3": res3,
        "Sell1": sell1, "Sell2": sell2, "Sell3": sell3,
        "Notes": notes
    }

    # Append to CSV
    df_save = pd.DataFrame([results_save])
    df_save.to_csv(csv_file, mode="a", header=False, index=False)

    st.success("✅ Data saved successfully!")


# ---------- Tabs ----------
tab1, tab2 = st.tabs(["📊 Results", "📜 History"])

with tab1:
    if 'results_save' in locals():
        df_display = pd.DataFrame({
            "Metric": [k for k in results_save.keys() if k not in ["DateTime", "Session", "Mode"]],
            "Value": [results_save[k] for k in results_save.keys() if k not in ["DateTime", "Session", "Mode"]]
        })

        def highlight_rows(val):
            if "Buy" in str(val):
                return "color: green; font-weight: bold;"
            elif "Sell" in str(val):
                return "color: red; font-weight: bold;"
            elif "Resistance" in str(val):
                return "color: orange; font-weight: bold;"
            else:
                return ""

        st.dataframe(df_display.style.applymap(highlight_rows, subset=["Metric"]),
                     use_container_width=True, height=35 * len(df_display))


with tab2:
    try:
        df_hist = pd.read_csv(csv_file, on_bad_lines="skip")
        df_hist = df_hist.iloc[::-1].reset_index(drop=True)  # latest on top

        if not df_hist.empty:
            def highlight_latest(row):
                return ["background-color: yellow; font-weight: bold;" if row.name == 0 else "" for _ in row]

            st.dataframe(df_hist.style.apply(highlight_latest, axis=1),
                         use_container_width=True,
                         height=(35 * len(df_hist) if len(df_hist) < 30 else 800))

            # -------- Clear History Button --------
            with st.expander("🗑️ Manage History"):
                option = st.radio("Choose an option:", ["Do Nothing", "Clear All", "Delete Specific Row by DateTime"])

                if option == "Clear All":
                    if st.button("Confirm Clear All"):
                        pd.DataFrame(columns=columns).to_csv(csv_file, index=False)
                        st.success("✅ All history cleared!")
                        st.stop()

                elif option == "Delete Specific Row by DateTime":
                    if "DateTime" in df_hist.columns:
                        date_to_delete = st.selectbox("Select DateTime to Delete", df_hist["DateTime"].tolist())
                        if st.button("Confirm Delete Row"):
                            df_hist = df_hist[df_hist["DateTime"] != date_to_delete]
                            df_hist.to_csv(csv_file, index=False)
                            st.success(f"✅ Row with DateTime {date_to_delete} deleted!")
                            st.stop()
        else:
            st.info("No history yet.")

    except Exception as e:
        st.error(f"Error reading history: {e}")





