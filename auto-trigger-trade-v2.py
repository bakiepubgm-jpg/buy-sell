# streamlit_mt5_dashboard.py
import streamlit as st
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime
import pytz
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import time

# -----------------------
# Initialize MT5
# -----------------------
if not mt5.initialize():
    st.error("❌ MT5 initialization failed. Make sure MetaTrader5 terminal is running and logged in.")
    st.stop()

tz = pytz.timezone("Asia/Karachi")

# -----------------------
# Page config & header
# -----------------------
st.set_page_config(page_title="MT5 Dashboard (Tabs per Symbol)", layout="wide")
st.title("📊 MT5 Dashboard — Tabs per Symbol")

# -----------------------
# Fetch available symbols
# -----------------------
all_symbols = [s.name for s in mt5.symbols_get()]
if not all_symbols:
    st.error("⚠️ No symbols returned from MT5. Check the terminal and Market Watch.")
    st.stop()

# -----------------------
# Top control panel (first page)
# -----------------------
with st.sidebar:
    st.header("App Controls")
    refresh_seconds = st.number_input("Auto-refresh interval (seconds)", min_value=2, max_value=60, value=6)
    lot_size = st.number_input("Default Lot Size", min_value=0.01, step=0.01, value=0.1)
    default_sl_points = st.number_input("Default SL (points, 0 = no SL)", min_value=0, value=0, step=1)
    default_tp_points = st.number_input("Default TP (points, 0 = auto from levels)", min_value=0, value=0, step=1)
    st.markdown("---")
    st.write("Symbols are loaded from your MT5 terminal (Market Watch).")
    st.write("Test with demo account. Auto-trade will place live orders when enabled.")

# controls on top area
col1, col2 = st.columns([2, 1])
with col1:
    timeframe_map = {
        "1 Minute": mt5.TIMEFRAME_M1,
        "5 Minutes": mt5.TIMEFRAME_M5,
        "15 Minutes": mt5.TIMEFRAME_M15,
        "1 Hour": mt5.TIMEFRAME_H1,
        "4 Hours": mt5.TIMEFRAME_H4,
        "1 Day": mt5.TIMEFRAME_D1
    }
    timeframe_choice = st.selectbox("Timeframe", list(timeframe_map.keys()), index=0)
    timeframe = timeframe_map[timeframe_choice]

    num_candles = st.slider("Number of candles to fetch", 50, 800, 200)
    selected_symbols = st.multiselect("Select symbols to analyze (choose from MT5 Market Watch)", options=all_symbols,
                                      default=[s for s in ["XAUUSDm", "USTECm", "BTCUSDm"] if s in all_symbols])
with col2:
    # show total open positions count
    positions_all = mt5.positions_get()
    total_open = len(positions_all) if positions_all is not None else 0
    st.metric("Open Positions (total)", total_open)

# autorefresh
st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresher")

# -----------------------
# Helper functions
# -----------------------
def safe_symbol_info(symbol):
    info = mt5.symbol_info(symbol)
    return info

def analyze_symbol(symbol, timeframe, num_candles):
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

    # buy/sell logic used previously
    dif = HH - LL
    idm = dif / 2
    factor = 1.4
    Buy1 = HH - (factor * idm)
    Buy2 = Buy1 - (factor * idm)
    Buy3 = Buy2 - (factor * idm)
    Resistance1 = HH + (factor * idm)
    Resistance2 = Resistance1 + (factor * idm)
    Resistance3 = Resistance2 + (factor * idm)

    # Sell levels (if PLL and RLL exist)
    if (PLL is not None) and (RLL is not None):
        dif_sell = PLL - RLL
        Sell1 = HH + dif_sell
        Sell2 = Sell1 + dif_sell
        Sell3 = Sell2 + dif_sell
    else:
        Sell1 = Sell2 = Sell3 = None

    levels = {
        "HH": HH, "LL": LL, "HL": HL, "PHH": PHH, "PLL": PLL, "RLL": RLL,
        "Buy1": Buy1, "Buy2": Buy2, "Buy3": Buy3,
        "Resistance1": Resistance1, "Resistance2": Resistance2, "Resistance3": Resistance3,
        "Sell1": Sell1, "Sell2": Sell2, "Sell3": Sell3
    }
    return levels, df

def get_positions_df():
    positions = mt5.positions_get()
    if not positions:
        return pd.DataFrame()
    pos_list = [p._asdict() for p in positions]
    df_pos = pd.DataFrame(pos_list)
    return df_pos

def get_positions_for_symbol(symbol):
    df_pos = get_positions_df()
    if df_pos.empty:
        return df_pos
    # filter by symbol column if exists
    col_sym = "symbol" if "symbol" in df_pos.columns else None
    if col_sym:
        df_sym = df_pos[df_pos["symbol"] == symbol].copy()
        # keep only existing columns of interest
        cols_of_interest = [c for c in ["ticket","symbol","volume","type","price_open","sl","tp","price_current","profit"] if c in df_sym.columns]
        df_sym = df_sym[cols_of_interest]
        if "type" in df_sym.columns:
            df_sym["type"] = df_sym["type"].map({0: "BUY", 1: "SELL"}).fillna(df_sym["type"])
        return df_sym
    return pd.DataFrame()

def pip_and_point(symbol):
    info = mt5.symbol_info(symbol)
    if not info:
        return None, None
    point = info.point
    # pip definition: for forex often pip = 10 * point if digits=5, pip=point if digits=4 etc.
    if info.digits >= 5:
        pip = 10 * point
    else:
        pip = point
    return point, pip

def estimate_profit_usd(symbol, tp_points, lot):
    # attempt to use trade_tick_value; fallback to approximate 1
    info = mt5.symbol_info(symbol)
    if not info:
        return 0.0
    tick_value = getattr(info, "trade_tick_value", None)
    if tick_value is None:
        # best-effort fallback:
        tick_value = 1.0
    # approximate: profit = tp_points * tick_value * lots
    return tp_points * tick_value * lot

def place_order_safe(symbol, lot, order_type, sl_points=0, tp_price=None):
    info = mt5.symbol_info(symbol)
    if not info:
        st.error("Symbol info not available.")
        return None
    
    # Safe check for trade permission
    trade_allowed = getattr(info, "trade_allowed", True)  # fallback to True if attribute missing
    if not trade_allowed:
        st.warning(f"Trading not allowed for {symbol}.")
        return None

    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if order_type == "BUY" else tick.bid

    sl = 0.0
    if sl_points and sl_points > 0:
        sl = 0.0

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp_price if tp_price is not None else 0.0,
        "deviation": 20,
        "magic": 123456,
        "comment": f"Streamlit Auto {order_type}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }
    result = mt5.order_send(request)
    return result


# -----------------------
# Session state: remember last_trade per symbol and autotrade toggles
# -----------------------
if "last_trade" not in st.session_state:
    st.session_state.last_trade = {}  # symbol -> "BUY"/"SELL"/None
if "autotrade" not in st.session_state:
    st.session_state.autotrade = {}  # symbol -> bool

# initialize default states for selected symbols
for s in selected_symbols:
    st.session_state.last_trade.setdefault(s, None)
    st.session_state.autotrade.setdefault(s, False)

# -----------------------
# Tabs per symbol
# -----------------------
if not selected_symbols:
    st.info("Select symbols above to create tabs for each symbol.")
else:
    tabs = st.tabs(selected_symbols)

    for i, symbol in enumerate(selected_symbols):
        with tabs[i]:
            st.header(f"{symbol}")

            # analyze
            levels, df = analyze_symbol(symbol, timeframe, num_candles)
            if levels is None:
                st.warning("No candle data for this symbol (open in Market Watch & try again).")
                continue

            last_price = float(df["close"].iloc[-1])

            # chart
            fig = go.Figure(data=[go.Candlestick(
                x=df["time"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                name=symbol
            )])
            # draw buy/sell/resistance lines
            for lvl_name in ["Buy1","Buy2","Buy3"]:
                fig.add_hline(y=levels[lvl_name], line=dict(color="green", dash="dash"), annotation_text=lvl_name, annotation_position="top left")
            for lvl_name in ["Resistance1","Resistance2","Resistance3"]:
                fig.add_hline(y=levels[lvl_name], line=dict(color="orange", dash="dot"), annotation_text=lvl_name, annotation_position="top right")
            if levels["Sell1"] is not None:
                fig.add_hline(y=levels["Sell1"], line=dict(color="red", dash="dash"), annotation_text="Sell1", annotation_position="bottom left")
            fig.add_hline(y=last_price, line=dict(color="blue", width=2), annotation_text="Last Price", annotation_position="bottom right")
            fig.update_layout(title=f"{symbol} — {timeframe_choice}", xaxis_rangeslider_visible=False, height=520)
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{symbol}_{i}")

            # calculation table
            st.subheader("Calculation Table")
            calc_df = pd.DataFrame({k: [v] for k, v in levels.items()})
            st.dataframe(calc_df.style.format(precision=5), use_container_width=True)

            # symbol-specific open positions
            st.subheader("Open Positions (this symbol)")
            df_sym_pos = get_positions_for_symbol(symbol)
            if df_sym_pos.empty:
                st.info("No open positions for this symbol.")
            else:
                st.dataframe(df_sym_pos.style.format(precision=2), use_container_width=True)

            # TP (auto) derived from levels:
            info = safe_symbol_info(symbol)
            if info:
                point = info.point
                pip = (10 * point) if info.digits >= 5 else point
            else:
                point = 1.0
                pip = 1.0

            # Choose TP source: auto from levels (Resistance1 - Buy1) or manual
            # Compute suggested TP for BUY: use Resistance1 - Buy1 (in points)
            suggested_tp_points = None
            tp_pips = None
            est_profit = None
            if levels["Resistance1"] is not None:
                # if using Buy1 as entry, TP = Resistance1 - Buy1
                suggested_tp_points = abs(levels["Resistance1"] - levels["Buy1"]) / point
                tp_pips = suggested_tp_points  # treat one point as one "point" (user asked points/pips interchangeably)
                est_profit = estimate_profit_usd(symbol, suggested_tp_points, lot_size)

            st.subheader("Trade Controls & Info")
            colA, colB, colC = st.columns([1,1,1])
            with colA:
                st.write(f"Last Price: {last_price:.5f}")
                if tp_pips is not None:
                    st.write(f"Suggested TP: {tp_pips:.1f} points (≈ {tp_pips * pip:.5f} price units)")
                    st.write(f"Est. profit (approx): ${est_profit:.2f} (lot={lot_size})")
                else:
                    st.write("Suggested TP: N/A")

            with colB:
                # Auto-trade toggle
                autotrade_toggle = st.checkbox("Enable Auto-Trade for this symbol", value=st.session_state.autotrade.get(symbol, False), key=f"autotrade_{symbol}")
                st.session_state.autotrade[symbol] = autotrade_toggle

                # Manual trade buttons
                if st.button(f"Place BUY {symbol}", key=f"manual_buy_{symbol}"):
                    # manual buy uses suggested_tp_points or default
                    tp_points_use = int(suggested_tp_points) if suggested_tp_points and suggested_tp_points > 0 else int(default_tp_points or 50)
                    tp_price = last_price + tp_points_use * point
                    res = place_order_safe(symbol, lot_size, "BUY", default_sl_points, tp_price)
                    st.write("Order result:", res)

                if st.button(f"Place SELL {symbol}", key=f"manual_sell_{symbol}"):
                    tp_points_use = int(suggested_tp_points) if suggested_tp_points and suggested_tp_points > 0 else int(default_tp_points or 50)
                    tp_price = last_price - tp_points_use * point
                    res = place_order_safe(symbol, lot_size, "SELL", default_sl_points, tp_price)
                    st.write("Order result:", res)

            with colC:
                last_trade = st.session_state.last_trade.get(symbol)
                st.write("Last executed trade (session):")
                st.info(last_trade if last_trade else "No trade executed this session for symbol")

            # -------------------
            # Auto-trade logic (signal detection + one-shot execution)
            # -------------------
            # Only run if enabled and trading allowed
            if st.session_state.autotrade.get(symbol, False):
                # detect BUY signal: price crosses above Buy1
                previous_state_key = f"prev_price_{symbol}"
                prev_price = st.session_state.get(previous_state_key, None)

                # We treat a "cross" as previous price <= level and current > level
                buy_level = levels["Buy1"]
                sell_level = levels["Sell1"]

                triggered = False
                # BUY cross
                if buy_level is not None:
                    if prev_price is not None and prev_price <= buy_level and last_price > buy_level:
                        # crossing up -> BUY
                        # check not already in last_trade BUY
                        if st.session_state.last_trade.get(symbol) != "BUY":
                            tp_points_use = int(suggested_tp_points) if suggested_tp_points and suggested_tp_points > 0 else int(default_tp_points or 50)
                            tp_price = last_price + tp_points_use * point
                            result = place_order_safe(symbol, lot_size, "BUY", default_sl_points, tp_price)
                            st.session_state.last_trade[symbol] = f"BUY @{last_price:.5f} TP={tp_points_use} pts"
                            triggered = True

                # SELL cross
                if (not triggered) and sell_level is not None:
                    if prev_price is not None and prev_price >= sell_level and last_price < sell_level:
                        if st.session_state.last_trade.get(symbol) != "SELL":
                            tp_points_use = int(suggested_tp_points) if suggested_tp_points and suggested_tp_points > 0 else int(default_tp_points or 50)
                            tp_price = last_price - tp_points_use * point
                            result = place_order_safe(symbol, lot_size, "SELL", default_sl_points, tp_price)
                            st.session_state.last_trade[symbol] = f"SELL @{last_price:.5f} TP={tp_points_use} pts"
                            triggered = True

                # update prev_price for next refresh
                st.session_state[previous_state_key] = last_price

# -----------------------
# Bottom: Global open positions (safe display of available columns)
# -----------------------
st.markdown("---")
st.subheader("All Open Positions (global)")

df_pos_all = get_positions_df()
if df_pos_all.empty:
    st.info("No open positions.")
else:
    st.write("Available position columns:", df_pos_all.columns.tolist())
    cols_to_show = [c for c in ["ticket","symbol","volume","type","price_open","sl","tp","price_current","profit"] if c in df_pos_all.columns]
    df_show = df_pos_all[cols_to_show].copy()
    if "type" in df_show.columns:
        df_show["type"] = df_show["type"].map({0:"BUY",1:"SELL"}).fillna(df_show["type"])
    st.dataframe(df_show.style.format(precision=2), use_container_width=True)

# -----------------------
# Footer
# -----------------------
st.markdown(
    "<div style='position: fixed; bottom: 0; left: 0; right: 0; text-align: center; "
    "padding: 6px; background-color: #f7f7f7; font-size: 13px; color: gray;'>"
    "© Umer Farid ™ | All Rights Reserved"
    "</div>",
    unsafe_allow_html=True
)
