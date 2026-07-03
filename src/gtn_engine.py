"""
gtn_engine.py
=============
Core GTN waterfall calculation engine.

FIVE DEDUCTION LAYERS
----------------------
Layer 1 - Mandatory rebates:
    Medicaid statutory (23.18% of AMP by law)
    Medicaid inflation penalty (if WAC grows faster than CPI)
    Part D coverage gap discount (70% manufacturer contribution)
    VA Federal Supply Schedule (24% discount)

Layer 2 - Contractual rebates:
    PBM formulary rebate (12% Tier 2, 5% Tier 3)
    Part D plan rebate (18% negotiated)

Layer 3 - Chargebacks:
    Specialty pharmacy (3%)
    GPO chargeback (2%)

Layer 4 - Patient assistance:
    Copay card (35% of commercial patients, $50 value per unit)
    PAP - free drug for uninsured patients who qualify

Layer 5 - Best price tracking:
    Lowest net price across any channel
    Drives Medicaid rebate recalculation

Author: Siva Annapareddy
Domain: Market Access and Pricing Analytics
"""

from src.gtn_config import GTNConfig, GTNResult


class GTNModel:
    """
    Computes the GTN waterfall for each month in the rolling horizon.

    WHY A CLASS
    -----------
    The model holds GTNConfig as state. Every method needs access
    to cfg. A class bundles config and computation together cleanly.
    Same pattern as IRPCascadeEngine from Project 1.
    """

    def __init__(self, config: GTNConfig):
        self.cfg = config
        self._validate_payer_mix()

    def _validate_payer_mix(self):
        """
        Payer mix must sum to 1.0.
        If it does not, revenue calculations will be wrong.
        This is the kind of silent bug that corrupts a board presentation.
        Catching it at init time prevents that.
        """
        total = (
            self.cfg.commercial_share +
            self.cfg.medicare_part_d +
            self.cfg.medicaid_share +
            self.cfg.uninsured_share +
            self.cfg.va_federal_share
        )
        assert abs(total - 1.0) < 0.001, \
            f"Payer mix must sum to 1.0 (got {total:.3f})"

    def _wac_for_month(self, month: int) -> float:
        """
        Apply annual WAC increase at months 13, 25, 37 etc.
        WAC grows annually not monthly — this floors to the
        correct year using integer division.
        """
        years_elapsed = (month - 1) // 12
        return self.cfg.wac_per_unit * (
            (1 + self.cfg.annual_wac_increase) ** years_elapsed
        )

    def _units_for_month(self, month: int) -> int:
        """
        Compound monthly volume growth from base units.
        Month 1 = base. Month 2 = base * 1.02. Month 3 = base * 1.02^2.
        """
        return int(
            self.cfg.units_per_month *
            ((1 + self.cfg.monthly_volume_growth) ** (month - 1))
        )

    def compute_month(self, month: int) -> GTNResult:
        """
        Compute full GTN waterfall for a single month.

        Returns GTNResult with every line item for traceability.
        """
        cfg = self.cfg
        wac = self._wac_for_month(month)
        units = self._units_for_month(month)
        gross_revenue = wac * units

        # ── Unit splits by payer ──────────────────────────────────
        comm_units   = units * cfg.commercial_share
        part_d_units = units * cfg.medicare_part_d
        mcaid_units  = units * cfg.medicaid_share
        unins_units  = units * cfg.uninsured_share
        va_units     = units * cfg.va_federal_share

        # ── Layer 1: Mandatory rebates ────────────────────────────
        medicaid_rebate = mcaid_units * wac * (
            cfg.medicaid_statutory_pct + cfg.medicaid_inflation_penalty
        )
        part_d_gap = part_d_units * wac * cfg.part_d_coverage_gap_pct * 0.15
        va_rebate = va_units * wac * cfg.va_fss_discount_pct
        mandatory_total = medicaid_rebate + part_d_gap + va_rebate

        # ── Layer 2: Contractual rebates ──────────────────────────
        pbm_rate = (
            cfg.commercial_pbm_tier2_pct
            if cfg.formulary_tier == "tier2"
            else cfg.commercial_pbm_tier3_pct
        )
        commercial_pbm = comm_units * wac * pbm_rate
        part_d_plan    = part_d_units * wac * cfg.part_d_plan_rebate_pct
        contractual_total = commercial_pbm + part_d_plan

        # ── Layer 3: Chargebacks ──────────────────────────────────
        sp_chargeback  = units * wac * cfg.specialty_pharmacy_pct
        gpo_chargeback = units * wac * cfg.gpo_chargeback_pct
        chargeback_total = sp_chargeback + gpo_chargeback

        # ── Layer 4: Patient assistance ───────────────────────────
        copay_cost = (
            comm_units *
            cfg.copay_card_utilization *
            cfg.copay_card_value_per_unit
        )
        pap_cost = unins_units * cfg.pap_utilization * wac * cfg.pap_discount_pct
        pa_total = copay_cost + pap_cost

        # ── Net revenue ───────────────────────────────────────────
        net_revenue = (
            gross_revenue
            - mandatory_total
            - contractual_total
            - chargeback_total
            - pa_total
        )
        net_price_per_unit = net_revenue / units if units > 0 else 0
        gtn_discount = (gross_revenue - net_revenue) / gross_revenue * 100

        # ── Layer 5: Best price tracking ──────────────────────────
        # Best price = lowest price paid by any purchaser
        # Drives Medicaid rebate recalculation
        # Must be tracked separately from net revenue
        medicaid_net = wac * (
            1 - cfg.medicaid_statutory_pct - cfg.medicaid_inflation_penalty
        )
        copay_net = wac - cfg.copay_card_value_per_unit
        va_net    = wac * (1 - cfg.va_fss_discount_pct)
        best_price = min(medicaid_net, copay_net, va_net)

        payer_breakdown = {
            "commercial_net": comm_units * wac * (1 - pbm_rate) - copay_cost,
            "part_d_net":     part_d_units * wac * (1 - cfg.part_d_plan_rebate_pct),
            "medicaid_net":   mcaid_units * wac * (
                1 - cfg.medicaid_statutory_pct - cfg.medicaid_inflation_penalty
            ),
            "uninsured_net":  unins_units * wac * (1 - cfg.pap_utilization),
            "va_net":         va_units * wac * (1 - cfg.va_fss_discount_pct),
        }

        return GTNResult(
            month=month,
            wac_revenue=round(gross_revenue, 0),
            mandatory_rebates=round(mandatory_total, 0),
            contractual_rebates=round(contractual_total, 0),
            chargebacks=round(chargeback_total, 0),
            patient_assistance=round(pa_total, 0),
            net_revenue=round(net_revenue, 0),
            net_price_per_unit=round(net_price_per_unit, 2),
            gtn_discount_pct=round(gtn_discount, 1),
            best_price=round(best_price, 2),
            payer_breakdown={k: round(v, 0) for k, v in payer_breakdown.items()},
        )

    def run_rolling_model(self, n_months: int = 24):
        """
        Run the GTN waterfall for n_months and return a DataFrame.
        Each row is one month. Each column is one waterfall line item.
        """
        import pandas as pd
        rows = []
        for m in range(1, n_months + 1):
            r = self.compute_month(m)
            rows.append({
                "month":               r.month,
                "wac_revenue":         r.wac_revenue,
                "mandatory_rebates":   r.mandatory_rebates,
                "contractual_rebates": r.contractual_rebates,
                "chargebacks":         r.chargebacks,
                "patient_assistance":  r.patient_assistance,
                "net_revenue":         r.net_revenue,
                "net_price_per_unit":  r.net_price_per_unit,
                "gtn_discount_pct":    r.gtn_discount_pct,
                "best_price":          r.best_price,
            })
        return pd.DataFrame(rows)


if __name__ == "__main__":
    cfg = GTNConfig()
    model = GTNModel(cfg)
    df = model.run_rolling_model(n_months=24)
    print("GTN Rolling Model — 24 Month Output")
    print()
    print(df[[
        "month", "wac_revenue", "net_revenue",
        "gtn_discount_pct", "net_price_per_unit", "best_price"
    ]].to_string(index=False))
    print()
    print(f"Year 1 WAC revenue:  ${df[df['month'] <= 12]['wac_revenue'].sum():>14,.0f}")
    print(f"Year 1 net revenue:  ${df[df['month'] <= 12]['net_revenue'].sum():>14,.0f}")
    print(f"Avg GTN discount:    {df[df['month'] <= 12]['gtn_discount_pct'].mean():.1f}%")