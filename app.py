import streamlit as st

st.set_page_config(
    page_title="XRP Futures Risk Tool",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Header
# -----------------------------
st.markdown("# 🧮 XRP Futures Risk & Profit Tool")
st.caption("Position sizing, margin check, fees impact, R:R, break-even win rate, and liquidation (approx).")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("⚙️ Trade Inputs")

balance = st.sidebar.number_input("Account balance (USDT)", min_value=0.0, value=100.0, step=10.0)
risk_pct = st.sidebar.number_input("Risk %", min_value=0.0, value=1.0, step=0.1)

side = st.sidebar.selectbox("Side", ["Long", "Short"])
lev = st.sidebar.number_input("Leverage (x)", min_value=1.0, value=10.0, step=1.0)

entry = st.sidebar.number_input("Entry price (XRP)", min_value=0.0, value=0.5200, step=0.0001, format="%.4f")
stop  = st.sidebar.number_input("Stop-loss price (XRP)", min_value=0.0, value=0.5100, step=0.0001, format="%.4f")
take  = st.sidebar.number_input("Take-profit price (XRP)", min_value=0.0, value=0.5500, step=0.0001, format="%.4f")

fee_mode = st.sidebar.selectbox("Fees preset", ["Binance Futures (0.06%)", "Custom"])
fee_pct = 0.06 if fee_mode == "Binance Futures (0.06%)" else st.sidebar.number_input(
    "Fee % per trade", min_value=0.0, value=0.06, step=0.01
)

mmr_pct = st.sidebar.number_input("Maintenance margin % (MMR)", min_value=0.0, value=0.50, step=0.05)

calc_btn = st.sidebar.button("✅ Calculate", use_container_width=True)

# -----------------------------
# Calculation
# -----------------------------
def calculate(balance, risk_pct, entry, stop, take, lev, fee_pct, mmr_pct, side):
    if balance <= 0 or entry <= 0 or lev <= 0:
        return {"error": "Balance, Entry, and Leverage must be > 0."}

    side = side.lower()

    # Validate direction logic
    if side == "long":
        if stop >= entry:
            return {"error": "LONG: Stop-loss must be below Entry."}
        if take <= entry:
            return {"error": "LONG: Take-profit must be above Entry."}
        risk_per_unit = entry - stop
        reward_per_unit = take - entry
    else:
        if stop <= entry:
            return {"error": "SHORT: Stop-loss must be above Entry."}
        if take >= entry:
            return {"error": "SHORT: Take-profit must be below Entry."}
        risk_per_unit = stop - entry
        reward_per_unit = entry - take

    if risk_per_unit <= 0:
        return {"error": "Invalid risk distance. Check Entry/Stop."}

    # Risk target in USDT
    risk_usdt_target = balance * (risk_pct / 100.0)

    # Quantity XRP based on SL risk
    qty_xrp = risk_usdt_target / risk_per_unit

    # Notional & margin
    notional = qty_xrp * entry
    margin_required = notional / lev

    # Fees estimate (entry + exit)
    fee_rate = fee_pct / 100.0
    fees_total = notional * fee_rate * 2

    # PnL to SL/TP including fee impact
    loss_to_sl = qty_xrp * risk_per_unit + fees_total
    profit_to_tp = qty_xrp * reward_per_unit - fees_total

    rr = profit_to_tp / loss_to_sl if loss_to_sl > 0 else 0
    breakeven = 1.0 / (1.0 + rr) if rr > 0 else 1.0

    # Advanced liquidation (approx)
    # Simplified equity-based approach: depends on remaining equity and maintenance margin.
    maintenance_margin_rate = mmr_pct / 100.0

    if qty_xrp <= 0:
        return {"error": "Quantity is 0. Check inputs."}

    if side == "long":
        liq_price = entry - ((balance - margin_required) / qty_xrp) - (entry * maintenance_margin_rate)
    else:
        liq_price = entry + ((balance - margin_required) / qty_xrp) + (entry * maintenance_margin_rate)

    # Liquidation distance %
    liq_distance_pct = abs((entry - liq_price) / entry) * 100.0 if entry > 0 else 0

    # Danger zone rating (simple)
    # If liquidation is close (<3%) it's dangerous; 3–7 moderate; >7 safer
    if liq_distance_pct < 3:
        danger = "HIGH"
    elif liq_distance_pct < 7:
        danger = "MEDIUM"
    else:
        danger = "LOW"

    return {
        "risk_target": risk_usdt_target,
        "qty_xrp": qty_xrp,
        "notional": notional,
        "margin": margin_required,
        "fees": fees_total,
        "loss": loss_to_sl,
        "profit": profit_to_tp,
        "rr": rr,
        "breakeven": breakeven,
        "liq_price": liq_price,
        "liq_distance_pct": liq_distance_pct,
        "danger": danger,
    }

# -----------------------------
# UI Output
# -----------------------------
if not calc_btn:
    st.info("👈 Enter values in the sidebar, then click **Calculate**.")
else:
    res = calculate(balance, risk_pct, entry, stop, take, lev, fee_pct, mmr_pct, side)

    if "error" in res:
        st.error(res["error"])
    else:
        # Top metrics
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Risk target ($)", f"{res['risk_target']:.2f} USDT")
        t2.metric("Position size", f"{res['qty_xrp']:.2f} XRP")
        t3.metric("Notional", f"{res['notional']:.2f} USDT")
        t4.metric("Margin required", f"{res['margin']:.2f} USDT")

        st.divider()

        # PnL + Fees
        c1, c2, c3 = st.columns(3)
        c1.metric("Fees (est.)", f"{res['fees']:.2f} USDT")
        c2.metric("Loss to SL (fees incl.)", f"{res['loss']:.2f} USDT")
        c3.metric("Profit to TP (fees incl.)", f"{res['profit']:.2f} USDT")

        st.divider()

        # RR + breakeven
        left, right = st.columns([1, 1])
        rr = res["rr"]

        if rr >= 2:
            left.success(f"Reward:Risk (R:R) = **{rr:.2f}** ✅ Strong setup")
        elif rr >= 1:
            left.warning(f"Reward:Risk (R:R) = **{rr:.2f}** ⚠️ Moderate")
        else:
            left.error(f"Reward:Risk (R:R) = **{rr:.2f}** ❌ Weak")

        right.metric("Break-even win rate", f"{res['breakeven']*100:.2f}%")

        st.divider()

        # Liquidation block
        l1, l2, l3 = st.columns(3)
        l1.metric("Liquidation (Advanced, approx)", f"{res['liq_price']:.4f} XRP")
        l2.metric("Liq distance from entry", f"{res['liq_distance_pct']:.2f}%")

        if res["danger"] == "HIGH":
            l3.error("Danger: HIGH ⚠️")
        elif res["danger"] == "MEDIUM":
            l3.warning("Danger: MEDIUM ⚠️")
        else:
            l3.success("Danger: LOW ✅")

        st.divider()

        # Warnings
        if res["margin"] > balance:
            st.error("⚠️ Not enough margin. Increase leverage or reduce risk / position size.")
        if risk_pct > 3:
            st.warning("⚠️ Risk > 3% is aggressive. Consider 0.5%–2% for safer trading.")
        if res["profit"] <= 0:
            st.warning("⚠️ Fees are eating profit. Consider larger TP or lower fees (maker).")

        st.caption("Educational tool only. Liquidation is approximate and can differ by exchange rules (tiered MMR, funding, fees, etc.).")
