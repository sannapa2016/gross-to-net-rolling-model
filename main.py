"""
main.py
=======
Single entry point for the Gross-to-Net Rolling Model.

Runs three analyses:
    1. Rolling 24-month GTN waterfall
    2. Scenario comparison across three formulary configurations
    3. Month 12 GTN waterfall breakdown

Author: Siva Annapareddy
Domain: Market Access and Pricing Analytics
"""

import os
import pandas as pd
from src.gtn_config import GTNConfig
from src.gtn_engine import GTNModel
from src.scenarios import run_scenario_analysis, gtn_waterfall_summary

os.makedirs("outputs", exist_ok=True)


def main():
    print("=" * 65)
    print("GROSS-TO-NET ROLLING MODEL")
    print("Author: Siva Annapareddy | Amrak Pharma Analytics")
    print("=" * 65)

    # ── Analysis 1: Rolling 24-month model ───────────────────────
    print("\n[1] ROLLING 24-MONTH GTN SUMMARY\n")
    cfg = GTNConfig()
    model = GTNModel(cfg)
    df = model.run_rolling_model(n_months=24)

    print(df[[
        "month", "wac_revenue", "net_revenue",
        "gtn_discount_pct", "net_price_per_unit", "best_price"
    ]].to_string(index=False))

    yr1 = df[df["month"] <= 12]
    yr2 = df[df["month"] > 12]
    print(f"\n  Year 1 WAC revenue:    ${yr1['wac_revenue'].sum():>14,.0f}")
    print(f"  Year 1 net revenue:    ${yr1['net_revenue'].sum():>14,.0f}")
    print(f"  Year 2 WAC revenue:    ${yr2['wac_revenue'].sum():>14,.0f}")
    print(f"  Year 2 net revenue:    ${yr2['net_revenue'].sum():>14,.0f}")
    print(f"  Avg GTN discount:      {df['gtn_discount_pct'].mean():.1f}%")
    print(f"  Best price exposure:   ${df.iloc[11]['best_price']:,.2f}")

    # ── Analysis 2: Scenario comparison ──────────────────────────
    print("\n[2] SCENARIO COMPARISON\n")
    sc = run_scenario_analysis()
    print(sc[[
        "scenario", "yr1_net_revenue",
        "avg_gtn_discount", "net_vs_wac_pct", "revenue_gap"
    ]].to_string(index=False))

    best = sc["yr1_net_revenue"].max()
    worst = sc["yr1_net_revenue"].min()
    print(f"\n  >>> Revenue at risk from formulary tier: ${best - worst:,.0f}")

    # ── Analysis 3: GTN waterfall breakdown ───────────────────────
    print("\n[3] GTN WATERFALL — Month 12 (Tier 2 baseline)\n")
    wf = gtn_waterfall_summary(model, month=12)
    print(wf.to_string(index=False))

    # ── Export ────────────────────────────────────────────────────
    df.to_csv("outputs/gtn_rolling_model.csv", index=False)
    sc.to_csv("outputs/gtn_scenario_comparison.csv", index=False)
    wf.to_csv("outputs/gtn_waterfall_month12.csv", index=False)

    print("\n[OK] Results saved to outputs/")
    print("=" * 65)


if __name__ == "__main__":
    main()