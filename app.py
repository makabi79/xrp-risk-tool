import streamlit as st

# ✅ MUST be first Streamlit command
st.set_page_config(
    page_title="XRP Futures Risk Tool (PRO)",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# 🔐 PASSWORD PROTECTION (PRO)
# ---------------------------
PASSWORD = "XRPPRO2025"  # change anytime

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 XRP Futures Risk Tool – PRO Access")
    st.caption("Enter your access password to unlock the PRO calculator.")

    user_password = st.text_input("Access password", type="password")

    colA, colB = st.columns([1, 2])
    with colA:
        unlock = st.button("Unlock")
    with colB:
        st.info("If you purchased, your password is in your Payhip download file.")

    if unlock:
        if user_password == PASSWORD:
            st.session_state.authenticated = True
            st.success("Access Granted ✅")
            st.rerun()
        else:
            st.error("Incorrect password ❌")

    st.stop()

# ---------------------------
# ✅ APP (PRO)
# ---------------------------
st.markdown("# 🧮 XRP Futures Risk & Profit Tool (PRO)")
st.caption("Fast position sizing, margin check, R:R, break-even win rate, and liquidation (approx).")

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
    # ---- Basic validation ----
    if entry <= 0:
        st.error("Entry price must be > 0.")
        st.stop()

    if lev <= 0:
        st.error("Leverage must be > 0.")
        st.stop()

    # ---- Risk & reward per unit ----
    if side == "Long":
        risk_per_unit = entry - stop
        reward_per_unit = take - entry
    else:
        risk_per_unit = stop - entry
        reward_per_unit = entry - take

    if risk_per_unit <= 0:
        st.error("Invalid Stop-Loss for selected side. (Risk per unit must be > 0)")
        st.stop()

    # ---- Risk in USDT ----
    risk_usdt = balance * (risk_pct / 100.0)

    # ---- Position sizing ----
    qty = risk_usdt / risk_per_unit  # XRP quantity
    notional = qty * entry           # USDT
    margin = notional / lev          # USDT (isolated-like approximation)

    # ---- PnL ----
    loss = qty * risk_per_unit
    profit = qty * reward_per_unit

    # ---- Fees (approx): entry + exit ----
    fee_rate = fee_pct / 100.0
    fees_est = notional * fee_rate * 2  # pay fee on entry & exit (approx)

    # ---- R:R ----
    rr = profit / loss if loss != 0 else 0

    # ---- Break-even win rate (simple) ----
    # include fees as extra "cost" that must be recovered
    # effective profit and loss after fees:
    eff_profit = max(profit - fees_est, 0.0)
    eff_loss = loss + fees_est

    rr_eff = (eff_profit / eff_loss) if eff_loss != 0 else 0
    breakeven = 1 / (1 + rr_eff) if rr_eff > 0 else 1.0

    # ---- Approx Liquidation Price (VERY SIMPLE MODEL) ----
    # This is not exchange-accurate. Real liquidation depends on maintenance margin, fees, funding, and exchange rules.
    if side == "Long":
        liq_price = entry * (1 - (1 / lev))
        liq_distance_pct = ((entry - liq_price) / entry) * 100
    else:
        liq_price = entry * (1 + (1 / lev))
        liq_distance_pct = ((liq_price - entry) / entry) * 100

    # ---- UI Output ----
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Position Size (XRP)", f"{qty:,.2f}")
    col2.metric("Margin Required (USDT)", f"{margin:,.2f}")
    col3.metric("Loss (USDT)", f"{loss:,.2f}")
    col4.metric("Profit (USDT)", f"{profit:,.2f}")

    st.divider()

    colA, colB, colC = st.columns(3)
    colA.metric("Fees (est.)", f"{fees_est:,.2f} USDT")
    colB.metric("Break-even win rate", f"{breakeven*100:.2f}%")
    colC.metric("Approx Liquidation Price", f"{liq_price:.4f} XRP")

    st.caption(f"Liquidation distance (approx): **{liq_distance_pct:.2f}%** from entry.")

    st.divider()

    # ---- R:R badge ----
    if rr >= 2:
        st.success(f"Reward:Risk = {rr:.2f} ✅ Strong setup")
    elif rr >= 1:
        st.warning(f"Reward:Risk = {rr:.2f} ⚠️ Moderate")
    else:
        st.error(f"Reward:Risk = {rr:.2f} ❌ Weak")

    # ---- Margin/risk warnings ----
    if margin > balance:
        st.error("⚠️ Not enough balance for margin. Reduce position size or increase leverage.")
    if loss > balance * 0.03:
        st.warning("⚠️ Risk above 3% — aggressive position.")

    st.info("Disclaimer: Liquidation price is an approximation. Real liquidation depends on exchange maintenance margin, fees, and funding.")
else:
    st.info("Set inputs in the sidebar and click **Calculate**.")
