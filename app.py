import streamlit as st

st.set_page_config(
    page_title="XRP Futures Risk Tool",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("# 🧮 XRP Futures Risk & Profit Tool")
st.caption("Fast position sizing, margin check, R:R, and break-even win rate for XRP Futures.")

st.sidebar.header("⚙️ Trade Inputs")

balance = st.sidebar.number_input("Account balance (USDT)", min_value=0.0, value=100.0)
risk_pct = st.sidebar.number_input("Risk %", min_value=0.0, value=1.0)

side = st.sidebar.selectbox("Side", ["Long", "Short"])
lev = st.sidebar.number_input("Leverage (x)", min_value=1.0, value=10.0)

entry = st.sidebar.number_input("Entry price", min_value=0.0, value=0.5200, format="%.4f")
stop  = st.sidebar.number_input("Stop-loss price", min_value=0.0, value=0.5100, format="%.4f")
take  = st.sidebar.number_input("Take-profit price", min_value=0.0, value=0.5500, format="%.4f")

fee_pct = st.sidebar.number_input("Fee % per trade", min_value=0.0, value=0.06)

if st.sidebar.button("Calculate"):

    if side == "Long":
        risk_per_unit = entry - stop
        reward_per_unit = take - entry
    else:
        risk_per_unit = stop - entry
        reward_per_unit = entry - take

    risk_usdt = balance * (risk_pct / 100)

    qty = risk_usdt / risk_per_unit if risk_per_unit != 0 else 0
    notional = qty * entry
    margin = notional / lev if lev != 0 else 0

    loss = qty * risk_per_unit
    profit = qty * reward_per_unit

    rr = profit / loss if loss != 0 else 0
    breakeven = 1 / (1 + rr) if rr != 0 else 1

    col1, col2, col3 = st.columns(3)

    col1.metric("Margin Required", f"{margin:.2f} USDT")
    col2.metric("Loss ($)", f"{loss:.2f} USDT")
    col3.metric("Profit ($)", f"{profit:.2f} USDT")

    st.divider()

    if rr >= 2:
        st.success(f"Reward:Risk = {rr:.2f} ✅ Strong setup")
    elif rr >= 1:
        st.warning(f"Reward:Risk = {rr:.2f} ⚠️ Moderate")
    else:
        st.error(f"Reward:Risk = {rr:.2f} ❌ Weak")

    st.metric("Break-even win rate", f"{breakeven*100:.2f}%")
