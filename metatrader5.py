import streamlit as st
import pandas as pd
#import MetaTrader5 as mt5
from datetime import datetime
import pytz
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    st.write(MT5_AVAILABLE)
  
except ImportError:
    MT5_AVAILABLE = False
      st.error(MT5_AVAILABL)



# --- Initialize MT5 ---
if not mt5.initialize():
    st.error("❌ MT5 initialization failed. Please ensure MetaTrader5 is running and logged in.")
    st.stop()

# --- Timezone ---
tz = pytz.timezone("Asia/Karachi")

# --- Get all available symbols from MT5 ---
all_symbols = mt5.symbols_get()
symbol_names = [s.name for s in all_symbols]

st.set_page_config(page_title="MT5 Symbol Analyzer", layout="centered")
st.title("📊 Auto Symbol Analyzer (MT5 API)")

# Show list of available symbols
with st.expander("🔎 Available Symbols in your MT5"):
    st.write(symbol_names[:100])  # show first 100 symbols (avoid overload)

# User picks symbols
symbols = st.multiselect(
    "Select symbols to analyze",
    symbol_names,
    default=symbol_names[:3] if len(symbol_names) >= 3 else symbol_names
)

# Timeframe selection
timeframe_map = {
    "1 Minute": mt5.TIMEFRAME_M1,
    "5 Minutes": mt5.TIMEFRAME_M5,
    "15 Minutes": mt5.TIMEFRAME_M15,
    "1 Hour": mt5.TIMEFRAME_H1,
    "4 Hours": mt5.TIMEFRAME_H4,
    "1 Day": mt5.TIMEFRAME_D1
}
timeframe_choice = st.selectbox("Select Timeframe", list(timeframe_map.keys()))
timeframe = timeframe_map[timeframe_choice]

# Number of candles
num_candles = st.slider("Number of candles to fetch", 50, 500, 200)

# --- Function to analyze symbol ---
def analyze_symbol(symbol):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
    if rates is None or len(rates) == 0:
        return None, None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")

    HH = df["high"].max()
    LL = df["low"].min()
    HL = df["low"].max()

    sorted_highs = df["high"].sort_values(ascending=False).values
    sorted_lows = df["low"].sort_values().values

    PHH = sorted_highs[1] if len(sorted_highs) > 1 else None
    PLL = sorted_lows[1] if len(sorted_lows) > 1 else None
    RLL = sorted_lows[0] if len(sorted_lows) > 0 else None

    return {
        "HH": HH,
        "HL": HL,
        "LL": LL,
        "PHH": PHH,
        "PLL": PLL,
        "RLL": RLL
    }, df

# --- Run analysis ---
results = {}
for symbol in symbols:
    analysis, df = analyze_symbol(symbol)
    if analysis:
        results[symbol] = analysis
    else:
        st.warning(f"⚠️ No data found for {symbol}. Check if Market Watch is open in MT5.")

# --- Display results ---
if results:
    st.write("### 📈 Symbol Analysis Results")
    df_results = pd.DataFrame(results).T
    st.dataframe(df_results.style.format("{:.2f}"), use_container_width=True)



