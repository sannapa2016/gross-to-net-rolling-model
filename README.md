# Gross-to-Net Rolling Model

**WAC to Net Price Waterfall — US Payer Channel Simulation**

---

## The Problem

A drug with a $1,000 WAC does not generate $1,000 in revenue.
By the time mandatory rebates, PBM contracts, chargebacks, and
patient assistance are deducted, the manufacturer keeps $743.

Getting GTN wrong means your revenue forecast is wrong before
launch even begins.

---

## What This Model Does

- Simulates the full WAC to net price waterfall across 5 payer channels
- Runs a rolling 24-month GTN model with volume and WAC growth
- Compares three formulary scenarios: Tier 2, Tier 3, favorable mix
- Tracks best price exposure across all channels
- Exports month-by-month waterfall with every deduction line item

---

## The Five Deduction Layers

| Layer | Components | Typical Impact |
|---|---|---|
| Mandatory rebates | Medicaid statutory 23.18%, Part D gap 70%, VA FSS 24% | 8-15% of WAC |
| Contractual rebates | PBM Tier 2 12%, Part D plan 18% | 10-20% of WAC |
| Chargebacks | Specialty pharmacy 3%, GPO 2% | 4-6% of WAC |
| Patient assistance | Copay cards, PAP free drug | 1-3% of WAC |
| Net revenue | What the manufacturer keeps | 55-75% of WAC |

---

## Key Output

Year 1 WAC revenue:         $670,600,000
Year 1 net revenue:         $498,493,863
Avg GTN discount:           25.7%
Revenue at risk (Tier 2 vs Tier 3):  $18,860,626

---

## Scenario Comparison

| Scenario | Net Revenue | GTN Discount |
|---|---|---|
| Favorable mix (high commercial) | $517M | 23.1% |
| Tier 2 preferred (baseline) | $498M | 25.7% |
| Tier 3 non-preferred | $479M | 28.4% |

Same WAC. Same volume. Different formulary tier and payer mix.
$38M revenue range from strategic decisions made before launch.

---

## Quick Start

```bash
git clone https://github.com/sannapa2016/gross-to-net-rolling-model.git
cd gross-to-net-rolling-model
pip install -r requirements.txt
pip install -e .
python main.py
```

---

## Project Structure

gross-to-net-rolling-model/
├── src/
│   ├── init.py        Makes src a Python package
│   ├── gtn_config.py      GTNConfig dataclass — all parameters in one place
│   ├── gtn_engine.py      Core waterfall calculation engine
│   └── scenarios.py       Scenario comparison and waterfall summary
├── outputs/               CSV results generated on run (not on GitHub)
├── main.py                Single entry point — runs all three analyses
├── requirements.txt       numpy, pandas
├── setup.py               Makes project installable for any user
└── README.md              This file

---

## Why This Matters

In specialty pharma, GTN discounts run 25 to 55 percent.
A $1B WAC business might only generate $550M in net revenue.

The gap is driven by:
- **Mandatory rebates** — set by law, cannot be negotiated away
- **Formulary tier** — Tier 2 vs Tier 3 changes PBM rebate rate
- **Payer mix** — Medicaid carries 28% mandatory rebate vs 12% for commercial

This model quantifies the gap before launch so pricing committees
can make informed WAC and contracting decisions.

---

## Author

**Siva Annapareddy**
Founder and AVP, Amrak Pharma Analytics
18 years in pharma commercial analytics

*Project 2 of 36 — open-source pharma analytics portfolio*

*github.com/sannapa2016*
