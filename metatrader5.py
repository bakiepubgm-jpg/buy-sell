if MT5_AVAILABLE:
    st.success("✅ Using MetaTrader5 (local mode)")
    # your MT5 code here
else:
    st.warning("⚠️ MT5 not available. Using Yahoo Finance (cloud mode)")
