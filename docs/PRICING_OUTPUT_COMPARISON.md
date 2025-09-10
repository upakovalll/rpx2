PRI# RPX Backend 2026 - Pricing Output Format Comparison

This document provides a comprehensive comparison between the expected pricing output format (as defined in the pricing schema) and what our current system actually provides.

## Executive Summary

The current API endpoints are functional and return data from database views, but there are significant structural differences between the expected output format and what's currently provided:

1. **Field Organization**: Current endpoints return flat structures, while the expected format groups related fields into nested objects
2. **Missing Fields**: Many computed fields, percentages, and portfolio-level aggregations are not implemented
3. **Naming Conventions**: Inconsistencies in field naming (e.g., market_yield vs market_yield_decimal)
4. **Portfolio Summaries**: Limited to basic aggregates without sector/status breakdowns

## Endpoint-by-Endpoint Comparison

### 1. Pricing Output Endpoint (`/api/v1/valuation/pricing-output`)

**Current Output Structure:**
```json
{
  "metadata": {
    "source": "mv_pricing_engine_output_complete",
    "total_loans": 76,
    "analysis_date": "2025-07-23",
    "description": "Loan pricing engine output from database view"
  },
  "pricing_results": [
    {
      "loan_id": 6,
      "loan_name": "Loan Name 100010006",
      "price": 100.0,
      "fair_value": 12074190.98,
      "market_yield": 5.88,
      "benchmark_yield": 4.13,
      "current_balance": 12074190.98,
      "property_sector": "Multifamily",
      "wal_years": 0.0,
      "spread_adjustments": {
        "sasb_premium_bps": 0,
        "adjusted_spread_bps": 175.0,
        "effective_spread_bps": 185.0,
        // ... other adjustments
      }
    }
  ]
}
```

**Expected Output Structure:**
```json
{
  "metadata": { /* same */ },
  "pricing_results": [
    {
      "rp_system_id": "6",  // Primary key
      "loan_id": 6,
      "loan_name": "Loan Name 100010006",
      
      "pricing_metrics": {
        "benchmark_type": "UST",
        "benchmark_yield": 0.0413,
        "benchmark_yield_percentage": 4.13,
        "credit_spread": 1.85,
        "credit_spread_decimal": 0.0185,
        "credit_spread_bps": 185,
        "market_yield": 5.88,
        "market_yield_decimal": 0.0588,
        "price": 100.0,
        "fair_value": 12074190.98,
        "wal_years": 0.0,
        "modified_duration_years": 0.0,
        "convexity": 0.0
      },
      
      "spread_adjustments": { /* same structure */ },
      
      "risk_metrics": {
        "pd": 0.0,
        "pd_percentage": 0.0,
        "lgd": 0.0,
        "lgd_percentage": 0.0,
        "ead": 1.0,
        "ead_amount": 12074190.98,
        "expected_loss": 0.0,
        "expected_loss_amount": 0.0,
        "default_date": null,
        "days_to_default": null,
        "lag_to_recovery": 0,
        "loss_scenario": "No Loss",
        "loss_scenario_formatted": "N",
        "default_scenario": "N"
      },
      
      // Plus all loan characteristics fields...
    }
  ]
}
```

**Key Differences:**
- ❌ Missing `rp_system_id` (primary key)
- ❌ No grouped `pricing_metrics` object
- ❌ No `risk_metrics` object
- ❌ Missing multiple representation formats (decimal vs percentage vs basis points)
- ❌ Missing loan characteristic fields
- ✅ Has `spread_adjustments` as nested object (correct)

### 2. Loan Pricing Endpoint (`/api/v1/valuation/loan-pricing`)

**Current Output Structure:**
```json
[
  {
    "loan_id": 6,
    "pricing_scenario": "RPX Pricing",
    "maturity_assumption": "Maturity",
    "client_loan_number": "100010006",
    "loan_name": "Loan Name 100010006",
    "property_sector": "Multifamily",
    // ... all fields at same level
    "market_yield": 5.88,
    "market_yield_decimal": 0.0588,
    "credit_spread": 1.85,
    "credit_spread_decimal": 0.0185,
    "effective_spread_bps": 185.0,
    "adjusted_spread_bps": 175.0,
    "matrix_spread_bps": 115.0,
    // ... spread adjustments at same level
    "pd": 0,
    "lgd": 100,
    "ead": 100,
    "expected_loss": null,
    // ... risk metrics at same level
  }
]
```

**Expected Output Structure:**
```json
{
  "loans": [
    {
      "rp_system_id": "6",
      "loan_id": 6,
      // ... basic fields
      
      "pricing_metrics": {
        // All yield/spread/valuation fields grouped
      },
      
      "spread_adjustments": {
        // All adjustment fields grouped
      },
      
      "risk_metrics": {
        // All risk fields grouped with computed values
      }
    }
  ],
  "total_count": 76
}
```

**Key Differences:**
- ❌ Flat structure instead of grouped objects
- ❌ Missing wrapper object with total_count
- ❌ Inconsistent field naming
- ✅ Has most required fields (just not organized)
- ✅ Has rp_system_id in some records

### 3. Loan Risk Metrics Endpoint (`/api/v1/valuation/loan-risk-metrics`)

**Current Output Structure:**
```json
[
  {
    "rp_system_id": "8",
    "loan_name": "Loan Name 100010008",
    "property_sector": "Multifamily",
    "loan_status": "Performing",
    "credit_spread": 0.02881,
    "market_yield": null,
    "loss_scenario": "No Loss",
    "pd": null,
    "lgd": null,
    "ead": null,
    "expected_loss": null,
    "default_date": null,
    "days_to_default": null
  }
]
```

**Expected Output Structure:**
```json
[
  {
    "rp_system_id": "8",
    "loan_name": "Loan Name 100010008",
    "property_sector": "Multifamily",
    "loan_status": "Performing",
    
    "risk_metrics": {
      "pd": 0.0,
      "pd_percentage": 0.0,
      "lgd": 0.0,
      "lgd_percentage": 0.0,
      "ead": 1.0,
      "ead_amount": 10658077.95,
      "expected_loss": 0.0,
      "expected_loss_amount": 0.0,
      "default_date": null,
      "days_to_default": null,
      "lag_to_recovery": 0,
      "loss_scenario": "No Loss",
      "loss_scenario_formatted": "N",
      "default_scenario": "N",
      "credit_spread": 2.881,
      "credit_spread_decimal": 0.02881,
      "credit_spread_bps": 288.1
    }
  }
]
```

**Key Differences:**
- ❌ No nested `risk_metrics` object
- ❌ Missing percentage and amount representations
- ❌ Missing computed fields
- ❌ Credit spread at top level instead of in risk_metrics
- ✅ Uses correct `rp_system_id` primary key

### 4. Pricing Summary Endpoint (`/api/v1/valuation/pricing-summary`)

**Current Output Structure:**
```json
[
  {
    "total_loans": 76,
    "property_sectors": 8,
    "total_balance": 1788970548.54,
    "total_fair_value": 1611207458.58,
    "avg_market_yield": 9.48,
    "avg_price": 91.29,
    "total_unrealized_gl": -177763089.96
  }
]
```

**Expected Output Structure:**
```json
{
  "metadata": {
    "source": "v_portfolio_summary",
    "analysis_date": "2025-07-23",
    "total_loans": 76
  },
  
  "summary_metrics": {
    "total_loans": 76,
    "total_balance": 1788970548.54,
    "total_fair_value": 1611207458.58,
    "weighted_avg_price": 91.29,
    "weighted_avg_yield": 9.48,
    "weighted_avg_spread": 4.35,
    "weighted_avg_wal": 2.15,
    "weighted_avg_ltv": 0.58,
    "weighted_avg_dscr": 1.45,
    "total_expected_loss": 125000.00,
    "expected_loss_rate": 0.007,
    "loans_in_default": 5,
    "balance_in_default": 105750000.00,
    
    "sector_breakdown": {
      "Office": {"count": 15, "balance": 350000000, "avg_yield": 8.5},
      "Retail": {"count": 10, "balance": 250000000, "avg_yield": 7.2},
      "Multifamily": {"count": 35, "balance": 750000000, "avg_yield": 6.8}
    },
    
    "status_breakdown": {
      "Performing": {"count": 65, "balance": 1500000000, "avg_yield": 6.5},
      "Default": {"count": 5, "balance": 105750000, "avg_yield": 15.2},
      "REO": {"count": 1, "balance": 43358241, "avg_yield": 20.5}
    }
  },
  
  "loans": [
    // Array of individual loan pricing details
  ]
}
```

**Key Differences:**
- ❌ Returns array instead of object
- ❌ No metadata wrapper
- ❌ No summary_metrics wrapper
- ❌ Missing weighted average metrics (spread, WAL, LTV, DSCR)
- ❌ Missing risk metrics aggregation
- ❌ No sector breakdown
- ❌ No status breakdown
- ❌ No individual loan details

## Implementation Recommendations

### 1. Quick Wins (Minimal Changes)
- Add wrapper objects to endpoints returning arrays
- Include metadata in all responses
- Add `rp_system_id` where missing
- Ensure consistent date formatting

### 2. Field Transformations (Moderate Effort)
- Create transformation functions to group related fields
- Add computed fields (percentages, basis points)
- Implement consistent naming conventions
- Add missing fields that can be calculated

### 3. Database View Enhancements (Higher Effort)
- Create new views for sector/status breakdowns
- Add weighted average calculations
- Include risk metric aggregations
- Join additional tables for missing loan characteristics

### 4. Endpoint Restructuring (Full Implementation)
```python
# Example transformation for pricing-output endpoint
def transform_pricing_output(raw_data):
    return {
        "metadata": {...},
        "pricing_results": [
            transform_loan_pricing(loan) for loan in raw_data
        ]
    }

def transform_loan_pricing(loan):
    return {
        "rp_system_id": loan.get("rp_system_id"),
        "loan_id": loan.get("loan_id"),
        
        "pricing_metrics": {
            "market_yield": loan.get("market_yield"),
            "market_yield_decimal": loan.get("market_yield") / 100,
            "credit_spread": loan.get("credit_spread"),
            "credit_spread_decimal": loan.get("credit_spread") / 100,
            "credit_spread_bps": loan.get("credit_spread") * 100,
            # ... other metrics
        },
        
        "spread_adjustments": loan.get("spread_adjustments", {}),
        
        "risk_metrics": {
            "pd": loan.get("pd", 0),
            "pd_percentage": loan.get("pd", 0) * 100,
            # ... other risk metrics
        }
    }
```

## Database Views Available

Current views being used:
- `mv_pricing_engine_output_complete` - Main pricing data (materialized view, ~1200x faster)
- `v_loan_pricing` - Detailed pricing fields
- `v_loan_valuation` - Valuation data
- `v_loan_risk_metrics` - Risk metrics
- `v_portfolio_summary` - Portfolio summary
- `v_benchmark_current` - Current benchmark rates
- `v_current_pricing_spreads` - Active credit spreads

Missing views needed:
- Portfolio breakdown by sector
- Portfolio breakdown by status  
- Weighted average calculations
- Complete risk aggregations

## Priority Action Items

1. **Immediate**: Fix imports and schema dependencies to ensure server stability
2. **Short-term**: Add transformation layer to restructure current outputs
3. **Medium-term**: Enhance database views with missing calculations
4. **Long-term**: Fully implement expected schema structure with all fields

## Testing Coverage

The `test_new_endpoints.sh` script provides comprehensive testing for:
- Endpoint availability
- JSON response validation
- Sample output inspection
- Expected vs actual structure comparison

All endpoints are currently returning valid JSON responses, but the structure needs alignment with the expected format defined in the pricing schema.