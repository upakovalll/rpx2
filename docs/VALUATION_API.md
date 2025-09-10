# Valuation API Documentation

## Overview

The RPX Backend provides comprehensive valuation and pricing endpoints that leverage database views to calculate fair values, market yields, and risk metrics for commercial real estate loans.

## Key Valuation Views

The valuation endpoints use the following PostgreSQL views:

- `mv_pricing_engine_output_complete` - Main pricing output (materialized view, ~1200x faster)
- `mv_loan_valuation` - Loan valuation details (materialized view)
- `mv_loan_pricing` - Comprehensive pricing data (materialized view)
- `v_loan_risk_metrics` - Risk metrics (PD, LGD, expected loss)
- `v_loan_spread_breakdown` - Detailed spread adjustments
- `v_portfolio_summary` - Portfolio-level aggregates

## Main Endpoints

### GET /api/v1/valuation/pricing-output
Returns pricing engine output with fair value calculations and spread adjustments.

**Sample Response:**
```json
{
  "metadata": {
    "source": "mv_pricing_engine_output_complete",
    "total_loans": 76,
    "analysis_date": "2025-07-22"
  },
  "pricing_results": [
    {
      "loan_id": 1,
      "loan_name": "Loan Name 100010001",
      "price": 39.45,
      "fair_value": 5488848.27,
      "market_yield": 8.79,
      "benchmark_yield": 4.54,
      "current_balance": 13915041.66,
      "property_sector": "Multifamily",
      "spread_adjustments": {
        "adjusted_spread_bps": 425,
        "effective_spread_bps": 425,
        "dscr_adjustment_bps": 0,
        "ltv_factor_adjustment_bps": 0,
        "sasb_premium_bps": 0
      }
    }
  ]
}
```

### GET /api/v1/valuation/loan-pricing
Comprehensive pricing data with all calculation fields.

**Key Fields:**
- `market_yield` - Calculated market yield
- `benchmark_yield` - Reference benchmark rate
- `credit_spread` - Total credit spread
- `adjusted_spread_bps` - Base spread after adjustments
- Various adjustment factors (LTV, DSCR, SASB, etc.)

### GET /api/v1/valuation/loan-risk-metrics
Risk metrics for each loan.

**Sample Response:**
```json
{
  "rp_system_id": "8",
  "loan_name": "Loan Name 100010008",
  "property_sector": "Multifamily",
  "loan_status": "Performing",
  "credit_spread": 0.02881,
  "pd": null,
  "lgd": null,
  "ead": null,
  "expected_loss": null
}
```

### GET /api/v1/valuation/loan-spread-breakdown
Detailed breakdown of spread adjustments.

**Adjustment Types:**
- `ltv_factor_adjustment_bps` - LTV-based adjustment
- `dscr_adjustment_bps` - DSCR-based adjustment
- `sasb_premium_bps` - SASB premium
- `senior_tiering_adjustment_bps` - Seniority adjustment
- `mezzanine_adjustment_bps` - Mezzanine loan adjustment
- `loan_status_adjustment_bps` - Status-based adjustment
- `lifecycle_adjustment_bps` - Property lifecycle adjustment
- `ltv_performance_adjustment_bps` - LTV performance adjustment

### GET /api/v1/valuation/pricing-summary
Portfolio-level pricing summary.

**Sample Response:**
```json
{
  "total_loans": 76,
  "property_sectors": 8,
  "total_balance": 1788970548.54,
  "total_fair_value": 1611169963.71,
  "avg_market_yield": 9.48,
  "avg_price": 91.27,
  "total_unrealized_gl": -177800584.83
}
```

## Calculation Methodology

### Fair Value Calculation
Fair value is calculated using discounted cash flow analysis with:
- Projected cash flows based on loan terms
- Market yield as discount rate
- Adjustments for prepayment risk

### Market Yield Components
```
Market Yield = Benchmark Yield + Credit Spread + Adjustments
```

### Credit Spread Adjustments
Base credit spreads are adjusted based on:
1. **LTV Performance**: Higher LTV ratios increase spread
2. **DSCR Performance**: Lower DSCR increases spread
3. **Property Type**: Sector-specific adjustments
4. **Loan Status**: Non-performing loans have higher spreads
5. **Seniority**: Subordinate positions have higher spreads

## Additional Endpoints

### GET /api/v1/valuation/loan-benchmark
Benchmark rate assignments for each loan.

### GET /api/v1/valuation/loan-wal
Weighted Average Life calculations.

### GET /api/v1/valuation/loans-in-forbearance
Loans currently in forbearance status.

### GET /api/v1/valuation/loan-accrued
Accrued interest calculations.

### GET /api/v1/valuation/benchmark-current
Current benchmark rates from market data.

### GET /api/v1/valuation/current-pricing-spreads
Current credit spreads by property type and loan class.

## Data Freshness

- Pricing calculations are based on the latest data in the database views
- Benchmark rates are updated daily via the benchmark update endpoints
- Credit spreads are updated periodically via the spread update endpoints

## Usage Notes

1. All monetary values are in the loan's currency (typically USD)
2. Rates and yields are expressed as decimals (0.05 = 5%)
3. Basis points (bps) are integers (250 = 2.50%)
4. Decimal values in responses are automatically converted to JSON-compatible formats