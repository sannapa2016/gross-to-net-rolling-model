"""
scenarios.py
============
GTN scenario comparison across three formulary and payer mix configurations.

WHY SCENARIO ANALYSIS
----------------------
The GTN discount is not fixed. It changes based on:
    - Formulary tier (Tier 2 vs Tier 3 changes PBM rebate rate)
    - Payer mix (more commercial = lower mandatory rebates)
    - Copay card utilization (higher utilization = more patient assistance cost)

A pricing committee needs to see all three scenarios side by side
to understand the revenue range before setting WAC.

THREE SCENARIOS
---------------
1. Tier 2 preferred   - standard launch assumption
2. Tier 3             - worst case formulary access
3. Favorable mix      - high commercial share, low Medicaid

Author: Siva Annapareddy
Domain: Market Access and Pricing Analytics
"""

import pandas as pd
from src.gtn_config import GTNConfig
from src.gtn_engine import GTNModel


def run_scenario_analysis() -> pd.DataFrame:
    """
    Compare GTN outcomes across three named scenarios.
    Each scenario runs a full 12-month model and summarizes Year 1.
    """
    scenarios = {
        "Tier 2 preferred": GTNConfig(
            formulary_tier="tier2",
            copay_card_utilization=0.35
        ),
        "Tier 3 non-preferred": GTNConfig(
            formulary_tier="tier3",
            copay_card_utilization=0.50
        ),
        "Favorable mix (high commercial)": GTNConfig(
            formulary_tier="tier2",
            commercial_share=0.60,
            medicare_part_d=0.25,
            medicaid_share=0.10,
            uninsured_share=0.03,
            va_federal_share=0.02,
            copay_card_utilization=0.30
        ),
    }

    rows = []
    for label, cfg in scenarios.items():
        model = GTNModel(cfg)
        df = model.run_rolling_model(n_months=12)
        rows.append({
            "scenario":            label,
            "yr1_wac_revenue":     df["wac_revenue"].sum(),
            "yr1_net_revenue":     df["net_revenue"].sum(),
            "avg_gtn_discount":    df["gtn_discount_pct"].mean(),
            "avg_net_price":       df["net_price_per_unit"].mean(),
            "month12_gtn_pct":     df.iloc[-1]["gtn_discount_pct"],
        })

    df_out = pd.DataFrame(rows)
    df_out["net_vs_wac_pct"] = (
        df_out["yr1_net_revenue"] / df_out["yr1_wac_revenue"] * 100
    ).round(1)
    df_out["revenue_gap"] = (
        df_out["yr1_net_revenue"] - df_out["yr1_net_revenue"].iloc[0]
    ).round(0)
    return df_out


def gtn_waterfall_summary(model: GTNModel, month: int = 12) -> pd.DataFrame:
    """
    Single month waterfall showing each deduction layer clearly.
    Used for board presentations — one page, one month, full traceability.
    """
    r = model.compute_month(month)
    wac = r.wac_revenue

    steps = [
        ("WAC Revenue",           wac,                    wac),
        ("- Mandatory rebates",   -r.mandatory_rebates,   wac - r.mandatory_rebates),
        ("- Contractual rebates", -r.contractual_rebates, wac - r.mandatory_rebates - r.contractual_rebates),
        ("- Chargebacks",         -r.chargebacks,         wac - r.mandatory_rebates - r.contractual_rebates - r.chargebacks),
        ("- Patient assistance",  -r.patient_assistance,  r.net_revenue),
        ("= Net Revenue",          r.net_revenue,          r.net_revenue),
    ]

    rows = []
    for label, delta, running_total in steps:
        rows.append({
            "line_item":         label,
            "amount_usd":        round(delta, 0),
            "running_total_usd": round(running_total, 0),
            "pct_of_wac":        round(delta / wac * 100, 1),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("=" * 65)
    print("GTN SCENARIO ANALYSIS")
    print("=" * 65)

    print("\n[1] SCENARIO COMPARISON\n")
    sc = run_scenario_analysis()
    print(sc[[
        "scenario", "yr1_wac_revenue", "yr1_net_revenue",
        "avg_gtn_discount", "avg_net_price", "revenue_gap"
    ]].to_string(index=False))

    print("\n[2] GTN WATERFALL — Tier 2, Month 12\n")
    model = GTNModel(GTNConfig())
    wf = gtn_waterfall_summary(model, month=12)
    print(wf.to_string(index=False))

    print(f"\n[3] KEY INSIGHT")
    best = sc["yr1_net_revenue"].max()
    worst = sc["yr1_net_revenue"].min()
    gap = best - worst
    print(f"  Revenue range across scenarios: ${gap:,.0f}")
    print(f"  Tier 2 vs Tier 3 gap:          ${sc.iloc[0]['yr1_net_revenue'] - sc.iloc[1]['yr1_net_revenue']:,.0f}")