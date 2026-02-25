import streamlit as st

st.set_page_config(
    page_title="XRP Risk Tool (Basic)",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("# 🧮 XRP Futures Risk Tool (Basic)")
st.caption("Simple position sizing, margin check, R:R, break-even win rate, and simple liquidation estimate.")

st.sidebar.header("⚙️ Trade Inputs")

balance = st.sidebar.number_input("Account balance (USDT)", min_value=0.0, value=100.0, step=10.0)
risk_pct = st.sidebar.number_input("Risk % per trade", min_value=0.0, value=1.0, step=0.5)

side = st.sidebar.selectbox("Side", ["Long", "Short"])
lev = st.sidebar.number_input("Leverage (x)", min_value=1.0, value=10.0, step=1.0)

entry = st.sidebar.number_input("Entry price (XRP)", min_value=0.0, value=0.5200, format="%.4f")
stop  = st.sidebar.number_input("Stop-loss price (XRP)", min_value=0.0, value=0.5100, format="%.4f")
take  = st.sidebar.number_input("Take-profit price (XRP)", min_value=0.0, value=0.5500, format="%.4f")

fee_pct = st.sidebar.number_input("Fee % per trade (e.g. 0.06)", min_value=0.0, value=0.06, step=0.01)

if st.sidebar.button("Calculate"):
    if entry <= 0 or lev <= 0:
        st.error("Entry and Leverage must be > 0.")
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

    risk_usdt = balance * (risk_pct / 100.0)
    qty = risk_usdt / risk_per_unit if risk_per_unit > 0 else 0.0

    notional = qty * entry
    margin = notional / lev

    loss = qty * risk_per_unit
    profit = qty * reward_per_unit

    fee_rate = fee_pct / 100.0
    fees_est = notional * fee_rate * 2  # entry+exit estimate

    rr = profit / loss if loss > 0 else 0
    eff_profit = max(profit - fees_est, 0.0)
    eff_loss = loss + fees_est
    rr_eff = eff_profit / eff_loss if eff_loss > 0 else 0
    breakeven = 1 / (1 + rr_eff) if rr_eff > 0 else 1.0

    # Simple liquidation estimate (very rough)
    if side == "Long":
        liq_price = entry * (1 - (1 / lev))
        liq_distance_pct = ((entry - liq_price) / entry) * 100
    else:
        liq_price = entry * (1 + (1 / lev))
        liq_distance_pct = ((liq_price - entry) / entry) * 100

    a, b, c, d = st.columns(4)
    a.metric("Position Size (XRP)", f"{qty:,.2f}")
    b.metric("Margin Required (USDT)", f"{margin:,.2f}")
    c.metric("Loss to SL (USDT)", f"{loss:,.2f}")
    d.metric("Profit to TP (USDT)", f"{profit:,.2f}")

    st.divider()

    x, y, z = st.columns(3)
    x.metric("Fees (est.)", f"{fees_est:,.2f} USDT")
    y.metric("Break-even win rate", f"{breakeven*100:.2f}%")
    z.metric("Simple Liquidation (approx)", f"{liq_price:.4f} XRP")

    st.caption(f"Liquidation distance (approx): **{liq_distance_pct:.2f}%** from entry")

    if rr >= 2:
        st.success(f"Reward:Risk = {rr:.2f} ✅ Strong setup")
    elif rr >= 1:
        st.warning(f"Reward:Risk = {rr:.2f} ⚠️ Moderate")
    else:
        st.error(f"Reward:Risk = {rr:.2f} ❌ Weak")

    st.info("Disclaimer: Liquidation is a rough estimate. Real liquidation depends on exchange MMR, mark price, fees, funding, and tiers.")
else:
    st.info("Enter values in the sidebar and click **Calculate**.")
