import streamlit as st

st.set_page_config(
    page_title="XRP Futures Risk Tool",
    page_icon="📈",
    layout="wide"
)

st.title("📈 XRP Futures Risk & Position Calculator")
st.markdown("Professional risk management tool for XRP Futures traders.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Trade Settings")

balance = st.sidebar.number_input("Account Balance (USDT)", value=100.0)
risk_pct = st.sidebar.number_input("Risk % per Trade", value=1.0)
entry = st.sidebar.number_input("Entry Price", value=0.5200, format="%.4f")
stop = st.sidebar.number_input("Stop Loss", value=0.5100, format="%.4f")
take = st.sidebar.number_input("Take Profit", value=0.5500, format="%.4f")
lev = st.sidebar.number_input("Leverage", value=10.0)
side = st.sidebar.selectbox("Position Type", ["Long", "Short"])

fee_option = st.sidebar.selectbox(
    "Fee Type",
    ["Binance Futures (0.06%)", "Custom"]
)

if fee_option == "Binance Futures (0.06%)":
    fee_pct = 0.06
else:
    fee_pct = st.sidebar.number_input("Custom Fee %", value=0.06)

# --- CALCULATION ---
if st.sidebar.button("Calculate"):

    if side == "Long":
        risk_per_unit = entry - stop
        reward_per_unit = take - entry
    else:
        risk_per_unit = stop - entry
        reward_per_unit = entry - take

    risk_usdt = balance * (risk_pct / 100)
    qty = risk_usdt / risk_per_unit
    notional = qty * entry
    margin = notional / lev

    fee_rate = fee_pct / 100
    total_fees = notional * fee_rate * 2

    loss = qty * risk_per_unit + total_fees
    profit = qty * reward_per_unit - total_fees

    rr = profit / loss
    breakeven = 1 / (1 + rr)

    col1, col2, col3 = st.columns(3)

    col1.metric("Position Size (XRP)", f"{qty:,.2f}")
    col2.metric("Margin Required", f"{margin:,.2f} USDT")
    col3.metric("Risk ($)", f"{loss:,.2f} USDT")

    st.divider()

    col4, col5 = st.columns(2)

    if rr >= 2:
        col4.success(f"Reward/Risk: {rr:.2f} 🔥 Excellent")
    elif rr >= 1:
        col4.warning(f"Reward/Risk: {rr:.2f} ⚠ Moderate")
    else:
        col4.error(f"Reward/Risk: {rr:.2f} ❌ Poor Setup")

    col5.metric("Break-even Win Rate", f"{breakeven*100:.2f}%")

    st.divider()

    if margin > balance:
        st.error("⚠ Not enough margin. Reduce position size or increase leverage.")

    if loss > balance * 0.03:
        st.warning("⚠ Risk above 3% — aggressive position.")

    st.info("Always manage risk properly. This tool is for educational purposes only.")
