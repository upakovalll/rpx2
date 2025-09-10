# Pricing Output Implementation Verification

This document verifies the implementation of the complete-pricing-output endpoint against the database schema and expected output requirements.

## Database Schema Analysis

### v_loan_pricing View Columns Available:
```sql
-- Actual columns in v_loan_pricing:
loan_id                        integer
pricing_scenario               varchar
maturity_assumption           varchar
client_loan_number            varchar
loan_name                     varchar
property_sector               varchar
property_type                 varchar
property_lifecycle_financing  varchar
sponsor_borrower              varchar
original_balance              numeric
current_balance               numeric
currency                      varchar
client_percentage             numeric
pik_balance                   numeric
position_in_capital_stack     varchar
amortization_type             varchar
periodicity                   varchar
interest_day_count            varchar
loan_status                   varchar
commentary                    text
interest_type                 varchar
fixed_rate_coupon             numeric
floating_rate_index           varchar
floating_rate_margin          numeric
credit_spread_decimal         numeric
loss_scenario                 varchar(50)
pd                           numeric
lgd                          numeric
ead                          numeric
expected_loss                numeric
benchmark_type               varchar
benchmark_yield              numeric
wal_years                    numeric
modified_duration_years      numeric
maturity_date                date
origination_date             date
dscr_current                 numeric
ltv_current                  numeric
price                        numeric
market_yield                 numeric
market_yield_decimal         numeric
```

### Critical Missing Fields:
1. **rp_system_id** - The actual primary key from loans table
2. **fair_value** - Not calculated in the view
3. **accrued_interest** - Would need join to v_loan_accrued
4. **convexity** - Not calculated
5. **Risk metrics with multiple representations** (pd_percentage, lgd_percentage, etc.)
6. **Spread adjustments** - In separate view (v_loan_spread_breakdown)

## Implementation Analysis

### Current Transformation Mapping:

| Expected Field | Database Source | Current Implementation | Status |
|---------------|----------------|----------------------|---------|
| rp_system_id | NOT IN VIEW | Returns 555555 | ❌ Missing |
| loan_id | loan_id | Correctly mapped | ✅ |
| pricing_scenario | pricing_scenario | Correctly mapped | ✅ |
| risk_metrics.pd | pd | Mapped but often NULL | ⚠️ |
| risk_metrics.lgd | lgd | Mapped but often NULL | ⚠️ |
| risk_metrics.ead | ead | Mapped but often NULL | ⚠️ |
| valuation_results.fair_value | NOT IN VIEW | Returns 555555 | ❌ |
| valuation_results.accrued_interest | NOT IN VIEW | Returns 555555 | ❌ |
| valuation_results.convexity | NOT IN VIEW | Returns 555555 | ❌ |
| dates object | origination_date, maturity_date | Partially mapped | ⚠️ |

### Portfolio Analysis Gaps:

**Current Implementation:**
- Basic aggregations (total, averages)
- Sector allocation by percentage
- Simple risk/interest type distribution

**Missing from Expected:**
- Weighted average calculations for spread, LTV, DSCR
- Detailed sector breakdown with count, balance, avg_yield
- Status breakdown with metrics
- Expected loss aggregations
- Balance in default calculations

## Recommendations

### 1. Database View Enhancement
Create an enhanced view that includes all required fields:

```sql
CREATE OR REPLACE VIEW v_complete_loan_pricing AS
SELECT 
    l.rp_system_id,  -- Add primary key
    lp.*,
    lv.fair_value,
    lv.fair_value_including_accrued,
    la.accrued_interest,
    lrm.pd, lrm.lgd, lrm.ead, lrm.el,
    -- Add computed fields
    lp.credit_spread_decimal * 100 as credit_spread_percentage,
    lp.credit_spread_decimal * 10000 as credit_spread_bps,
    lp.market_yield_decimal * 100 as market_yield_percentage,
    -- Add convexity calculation
    CASE 
        WHEN lp.modified_duration_years > 0 
        THEN lp.modified_duration_years * lp.modified_duration_years * 1.2
        ELSE 0 
    END as convexity
FROM loans l
JOIN v_loan_pricing lp ON l.loan_id = lp.loan_id
LEFT JOIN v_loan_valuation lv ON l.loan_id = lv.loan_id
LEFT JOIN v_loan_accrued la ON l.loan_id = la.loan_id
LEFT JOIN v_loan_risk_metrics lrm ON l.rp_system_id = lrm.rp_system_id;
```

### 2. Enhanced Portfolio Summary View
```sql
CREATE OR REPLACE VIEW v_portfolio_summary_enhanced AS
SELECT 
    COUNT(*) as total_loans,
    SUM(current_balance) as total_balance,
    SUM(fair_value) as total_fair_value,
    
    -- Weighted averages
    SUM(market_yield * current_balance) / NULLIF(SUM(current_balance), 0) as weighted_avg_yield,
    SUM(credit_spread * current_balance) / NULLIF(SUM(current_balance), 0) as weighted_avg_spread,
    SUM(wal_years * current_balance) / NULLIF(SUM(current_balance), 0) as weighted_avg_wal,
    SUM(ltv_current * current_balance) / NULLIF(SUM(current_balance), 0) as weighted_avg_ltv,
    SUM(dscr_current * current_balance) / NULLIF(SUM(current_balance), 0) as weighted_avg_dscr,
    
    -- Risk metrics
    SUM(expected_loss) as total_expected_loss,
    SUM(expected_loss) / NULLIF(SUM(current_balance), 0) as expected_loss_rate,
    COUNT(CASE WHEN loan_status = 'Default' THEN 1 END) as loans_in_default,
    SUM(CASE WHEN loan_status = 'Default' THEN current_balance ELSE 0 END) as balance_in_default
    
FROM v_complete_loan_pricing;
```

### 3. Code Improvements

1. **Update SQL Query** to use enhanced view:
```python
loan_pricing_rows = db.execute(text("""
    SELECT * FROM v_complete_loan_pricing
    ORDER BY loan_id
""")).mappings().all()
```

2. **Remove Hardcoded Defaults** where data exists:
```python
# Instead of always returning 555555, check if related data exists
if "fair_value" in flat_record and flat_record["fair_value"] is not None:
    fair_value = float(flat_record["fair_value"])
else:
    fair_value = DEFAULT_NUMBER
```

3. **Add Multiple Representations**:
```python
# In transform_loan_record, add computed fields
credit_spread_decimal = float(get_value("credit_spread_decimal", 0))
transformed["pricing_metrics"] = {
    "credit_spread": credit_spread_decimal * 100,  # As percentage
    "credit_spread_decimal": credit_spread_decimal,
    "credit_spread_bps": credit_spread_decimal * 10000,
    # ... similar for other metrics
}
```

## Testing Checklist

- [ ] Verify rp_system_id is included in output
- [ ] Check risk metrics are populated where data exists
- [ ] Validate fair value and accrued interest calculations
- [ ] Test portfolio analysis calculations match expected format
- [ ] Ensure date formatting is consistent
- [ ] Verify all 215 fields are present in output

## Conclusion

The current implementation successfully creates the expected nested structure but is limited by:
1. Missing database fields (especially rp_system_id)
2. Incomplete view definitions
3. Lack of computed field variations

To fully meet the requirements, database view enhancements are needed along with minor code adjustments to properly handle the additional data.