import streamlit as st

st.set_page_config(page_title="XRP Futures Risk Tool", page_icon="📈", layout="centered")

st.title("📈 XRP Futures Risk & Profit Tool")
st.caption("Enter your trade details to calculate position size, margin, R:R, and break-even win rate.")

def calc(balance, risk_pct, entry, stop, take, lev, fee_pct, side):
    if min(balance, risk_pct, entry, stop, take, lev) <= 0:
        return {"error": "All values must be > 0."}

    side = side.lower()
    if side not in ("long", "short"):
        return {"error": "Side must be long or short."}

    if side == "long":
        if stop >= entry:
            return {"error": "For LONG, stop-loss must be below entry."}
        if take <= entry:
            return {"error": "For LONG, take-profit must be above entry."}
        risk_per_unit = entry - stop
        reward_per_unit = take - entry
    else:
        if stop <= entry:
            return {"error": "For SHORT, stop-loss must be above entry."}
        if take >= entry:
            return {"error": "For SHORT, take-profit must be below entry."}
        risk_per_unit = stop - entry
        reward_per_unit = entry - take

    risk_usdt = balance * (risk_pct / 100.0)

    qty_xrp = risk_usdt / risk_per_unit
    notional = qty_xrp * entry
    margin_required = notional / lev

    fee_rate = (fee_pct / 100.0)
    fees_total = notional * fee_rate * 2  # entry + exit (estimate)

    loss_to_sl = qty_xrp * risk_per_unit + fees_total
    profit_to_tp = qty_xrp * reward_per_unit - fees_total

    rr = profit_to_tp / loss_to_sl if loss_to_sl > 0 else 0
    breakeven = 1.0 / (1.0 + rr) if rr > 0 else 1.0

    distance_pct = (risk_per_unit / entry) * 100.0

    return {
        "risk_usdt": risk_usdt,
        "distance_pct": distance_pct,
        "qty_xrp": qty_xrp,
        "notional": notional,
        "margin_required": margin_required,
        "fees_total": fees_total,
        "loss_to_sl": loss_to_sl,
        "profit_to_tp": profit_to_tp,
        "rr": rr,
        "breakeven": breakeven
    }

with st.form("trade_form"):
    col1, col2 = st.columns(2)
    with col1:
        balance = st.number_input("Account balance (USDT)", min_value=0.0, value=100.0, step=10.0)
        risk_pct = st.number_input("Risk %", min_value=0.0, value=1.0, step=0.1)
        lev = st.number_input("Leverage (x)", min_value=1.0, value=10.0, step=1.0)
        side = st.selectbox("Side", ["Long", "Short"])
    with col2:
        entry = st.number_input("Entry price (XRP)", min_value=0.0, value=0.5200, step=0.0001, format="%.4f")
        stop = st.number_input("Stop-loss price (XRP)", min_value=0.0, value=0.5100, step=0.0001, format="%.4f")
        take = st.number_input("Take-profit price (XRP)", min_value=0.0, value=0.5500, step=0.0001, format="%.4f")
        fee_pct = st.number_input("Fee % per trade (e.g. 0.06)", min_value=0.0, value=0.06, step=0.01)

    submitted = st.form_submit_button("Calculate")

if submitted:
    res = calc(balance, risk_pct, entry, stop, take, lev, fee_pct, side)
    if "error" in res:
        st.error(res["error"])
    else:
        st.success("Done ✅")
        st.metric("Risk ($)", f"{res['risk_usdt']:.2f} USDT")
        st.metric("Entry→SL distance", f"{res['distance_pct']:.4f}%")

        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Quantity", f"{res['qty_xrp']:.2f} XRP")
        c2.metric("Position Notional", f"{res['notional']:.2f} USDT")
        c3.metric("Margin Required", f"{res['margin_required']:.2f} USDT")

        st.divider()
        c4, c5, c6 = st.columns(3)
        c4.metric("Total Fees (est.)", f"{res['fees_total']:.4f} USDT")
        c5.metric("Loss to SL (with fees)", f"{res['loss_to_sl']:.2f} USDT")
        c6.metric("Profit to TP (with fees)", f"{res['profit_to_tp']:.2f} USDT")

        st.divider()
        c7, c8 = st.columns(2)
        c7.metric("Reward:Risk (R:R)", f"{res['rr']:.2f}")
        c8.metric("Break-even win rate", f"{res['breakeven']*100:.2f}%")

        if res["margin_required"] > balance:
            st.warning("⚠️ Margin required is higher than balance. Increase leverage or reduce position/risk.")
        if res["profit_to_tp"] <= 0:
            st.warning("⚠️ Fees may be eating your profit. Consider larger TP or lower fees.")
