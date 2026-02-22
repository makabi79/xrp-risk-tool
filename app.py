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
mmr_pct = st.sidebar.number_input("Maintenance margin % (MMR)", min_value=0.0, value=0.50, step=0.05)

if st.sidebar.button("Calculate"):

    # --- Validate ---
    if entry <= 0 or lev <= 0 or balance <= 0:
        st.error("Entry, Leverage, and Balance must be > 0.")
        st.stop()

    if side == "Long":
        if stop >= entry:
            st.error("LONG: Stop-loss must be below Entry.")
            st.stop()
        if take <= entry:
            st.error("LONG: Take-profit must be above Entry.")
            st.stop()
        risk_per_unit = entry - stop
        reward_per_unit = take - entry
    else:
        if stop <= entry:
            st.error("SHORT: Stop-loss must be above Entry.")
            st.stop()
        if take >= entry:
            st.error("SHORT: Take-profit must be below Entry.")
            st.stop()
        risk_per_unit = stop - entry
        reward_per_unit = entry - take

    if risk_per_unit <= 0:
        st.error("Invalid risk distance. Check Entry/Stop.")
        st.stop()

    # --- Core sizing ---
    risk_usdt = balance * (risk_pct / 100)
    qty = risk_usdt / risk_per_unit
    notional = qty * entry
    margin = notional / lev

    # --- Fees (simple estimate: entry+exit taker) ---
    fee_rate = fee_pct / 100
    fees_total = notional * fee_rate * 2

    # --- PnL to SL/TP with fee impact (approx) ---
    loss = qty * risk_per_unit + fees_total
    profit = qty * reward_per_unit - fees_total

    rr = profit / loss if loss != 0 else 0
    breakeven = 1 / (1 + rr) if rr != 0 else 1

    # --- Advanced liquidation (approx) ---
    # Uses: balance, margin, qty, maintenance margin
    maintenance_margin_rate = mmr_pct / 100

    # Avoid division issues
    if qty <= 0:
        st.error("Quantity is 0. Check inputs.")
        st.stop()

    # This is a simplified equity-based approximation:
    # liq happens when remaining equity approaches maintenance margin.
    if side == "Long":
        liq_price = entry - ((balance - margin) / qty) - (entry * maintenance_margin_rate)
    else:
        liq_price = entry + ((balance - margin) / qty) + (entry * maintenance_margin_rate)

    # --- UI output ---
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
    st.metric("Approx Liquidation Price (Advanced)", f"{liq_price:.4f}")

    st.divider()
    st.caption("Liquidation formula here is an approximation and may differ per exchange due to tiered MMR, funding, fees, and position size rules.")
