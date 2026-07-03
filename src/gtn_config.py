"""
gtn_config.py
=============
Configuration dataclasses for the Gross-to-Net Rolling Model.

The GTN waterfall has five deduction layers applied to WAC revenue:
    1. Mandatory rebates  - legally required by statute
    2. Contractual rebates - negotiated with PBMs and payers
    3. Chargebacks        - distribution channel discounts
    4. Patient assistance - copay cards and PAP programs
    5. Admin overhead     - GTN tracking and compliance costs

All rates expressed as fractions (0.15 = 15%).

Author: Siva Annapareddy
Domain: Market Access and Pricing Analytics
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class GTNConfig:
    """
    Master configuration for a single GTN scenario.

    WHY A DATACLASS
    ---------------
    GTN models have 20+ parameters. A dataclass lets us define
    defaults once and override only what changes per scenario.
    Three scenarios (Tier 2, Tier 3, favorable mix) share 90%
    of parameters — only payer mix and rebate rates differ.
    """

    # ── Base pricing ──────────────────────────────────────────────
    wac_per_unit: float = 1000.0
    units_per_month: int = 50_000

    # ── Payer mix (must sum to 1.0) ───────────────────────────────
    # This drives which rebate rates apply to how many units
    commercial_share:   float = 0.45
    medicare_part_d:    float = 0.30
    medicaid_share:     float = 0.15
    uninsured_share:    float = 0.05
    va_federal_share:   float = 0.05

    # ── Mandatory rebates ─────────────────────────────────────────
    # These are required by law regardless of negotiation
    medicaid_statutory_pct:     float = 0.2318  # AMP-based minimum
    medicaid_inflation_penalty: float = 0.05    # triggers if price > CPI
    part_d_coverage_gap_pct:    float = 0.70    # manufacturer discount in gap
    va_fss_discount_pct:        float = 0.24    # Federal Supply Schedule

    # ── Contractual rebates ───────────────────────────────────────
    # Negotiated with PBMs and Part D plans for formulary access
    commercial_pbm_tier2_pct:   float = 0.12
    commercial_pbm_tier3_pct:   float = 0.05
    part_d_plan_rebate_pct:     float = 0.18
    formulary_tier: str = "tier2"

    # ── Chargebacks ───────────────────────────────────────────────
    # Distribution channel discounts paid to specialty pharmacies and GPOs
    specialty_pharmacy_pct:     float = 0.03
    gpo_chargeback_pct:         float = 0.02

    # ── Patient assistance ────────────────────────────────────────
    copay_card_utilization:     float = 0.35
    copay_card_value_per_unit:  float = 50.0
    pap_utilization:            float = 0.10
    pap_discount_pct:           float = 1.00   # PAP = free drug

    # ── Growth assumptions ────────────────────────────────────────
    monthly_volume_growth:      float = 0.02   # 2% monthly unit growth
    annual_wac_increase:        float = 0.05   # 5% annual WAC increase


@dataclass
class GTNResult:
    """
    Output of a single month GTN calculation.
    Stores every line item in the waterfall for full traceability.
    """
    month:               int
    wac_revenue:         float
    mandatory_rebates:   float
    contractual_rebates: float
    chargebacks:         float
    patient_assistance:  float
    net_revenue:         float
    net_price_per_unit:  float
    gtn_discount_pct:    float
    best_price:          float
    payer_breakdown:     Dict[str, float] = field(default_factory=dict)