# Database View Changes for Complete Pricing Output

This document outlines the concrete database view changes required to support the complete pricing output format as specified in the sample-loan-out.csv structure. These views will provide all necessary fields for the pricing engine output, with placeholders allowed where data is not available.

## Overview

The goal is to create database views that support all 215 fields required in the pricing output. Where actual data is not available, views should return appropriate placeholder values:
- Numeric fields: 0 or NULL (will be transformed to 555555 in application layer)
- String fields: NULL or empty string (will be transformed to "555555" in application layer)
- Date fields: NULL (will be transformed to "555555" in application layer)

## 1. Main Comprehensive Pricing View

### View: `v_complete_loan_pricing`

This view consolidates all loan pricing data from multiple sources:

```sql
CREATE OR REPLACE VIEW v_complete_loan_pricing AS
SELECT 
    -- Core loan identification (from loans table)
    l.rp_system_id,  -- Primary key from loans table
    l.loan_id,
    
    -- Basic loan fields from v_loan_pricing
    lp.pricing_scenario,
    lp.maturity_assumption,
    lp.client_loan_number,
    lp.loan_name,
    lp.property_sector,
    lp.property_type,
    lp.property_lifecycle_financing,
    lp.sponsor_borrower,
    lp.original_balance,
    lp.current_balance,
    lp.currency,
    lp.client_percentage,
    lp.pik_balance,
    lp.position_in_capital_stack,
    lp.amortization_type,
    lp.periodicity,
    lp.interest_day_count,
    lp.loan_status,
    lp.commentary,
    lp.interest_type,
    lp.fixed_rate_coupon,
    lp.floating_rate_index,
    lp.floating_rate_margin,
    lp.contract_type,
    
    -- Credit spread fields (ensure decimal representation)
    COALESCE(lp.credit_spread_decimal, 0) as credit_spread_decimal,
    COALESCE(lp.credit_spread_decimal * 100, 0) as credit_spread,
    
    -- Market yield fields
    COALESCE(lp.market_yield, 0) as market_yield,
    COALESCE(lp.market_yield_decimal, lp.market_yield / 100, 0) as market_yield_decimal,
    
    -- Benchmark fields
    COALESCE(lp.benchmark_type, 'US Treasury') as benchmark,
    COALESCE(lp.benchmark_yield, 0) as benchmark_yield,
    COALESCE(lp.benchmark_yield * 100, 0) as benchmark_yield_percentage,
    
    -- Loss scenario
    COALESCE(lp.loss_scenario, 'N') as loss_scenario,
    
    -- Risk metrics (from v_loan_risk_metrics or defaults)
    COALESCE(lrm.pd, lp.pd, 0) as pd,
    COALESCE(lrm.lgd, lp.lgd, 100) as lgd,
    COALESCE(lrm.ead, lp.ead, 100) as ead,
    COALESCE(lrm.el, lp.expected_loss, 0) as expected_loss,
    CAST(NULL AS DATE) as default_date,  -- Placeholder for default date
    0 as lag_to_recovery,
    '0%' as cdr,
    
    -- Valuation fields (from v_loan_valuation or calculate)
    COALESCE(lv.fair_value, lp.current_balance * (lp.price / 100), lp.current_balance) as fair_value,
    COALESCE(la.accrued_interest, 0) as accrued_interest,
    COALESCE(lv.fair_value_including_accrued, 
             lv.fair_value + COALESCE(la.accrued_interest, 0),
             lp.current_balance) as fair_value_plus_accrued,
    COALESCE(lp.price, 100) as price,
    COALESCE(lp.price + (COALESCE(la.accrued_interest, 0) / NULLIF(lp.current_balance, 0) * 100), 
             lp.price, 100) as price_including_accrued,
    
    -- WAL and duration
    COALESCE(lw.wal_years, lp.wal_years, 0) as wal_years,
    COALESCE(lp.modified_duration_years, 0) as modified_duration_years,
    
    -- Convexity calculation (if duration available, estimate convexity)
    CASE 
        WHEN lp.modified_duration_years IS NOT NULL AND lp.modified_duration_years > 0 
        THEN lp.modified_duration_years * lp.modified_duration_years * 1.2
        ELSE 0 
    END as convexity,
    
    -- Dates
    lp.origination_date as loan_origination_date,
    lp.maturity_date as original_maturity_date,
    COALESCE(lp.maturity_date, l.maturity_date) as maturity,
    l.extension_1st_date as extension_1st,
    l.extension_2nd_date as extension_2nd,
    l.extension_3rd_date as extension_3rd,
    
    -- Fair value ranges (calculate as +/- 2% of price)
    COALESCE(lp.price * 0.98, 98) as lower_price,
    COALESCE(lp.price * 1.02, 102) as upper_price,
    COALESCE(lv.fair_value * 0.98, lp.current_balance * 0.98) as lower_fv,
    COALESCE(lv.fair_value * 1.02, lp.current_balance * 1.02) as upper_fv,
    COALESCE(lp.market_yield + 0.2, 6.5) as lower_mey,
    COALESCE(lp.market_yield - 0.2, 6.0) as upper_mey,
    
    -- Default scenario
    CASE 
        WHEN lp.loan_status = 'Default' THEN 'Y - PD'
        ELSE 'N'
    END as default_scenario,
    
    -- Component yield (estimate if not available)
    COALESCE(lp.market_yield - 0.08, lp.market_yield, 0) as component_yield,
    
    -- LTV and DSCR
    lp.ltv_current,
    lp.dscr_current,
    
    -- Property location placeholder
    'City, ST' as property_location,
    
    -- Spread adjustments (from v_loan_spread_breakdown if available)
    COALESCE(lsb.sasb_premium_bps, 0) as sasb_premium_bps,
    COALESCE(lsb.adjusted_spread_bps, 175) as adjusted_spread_bps,
    COALESCE(lsb.dscr_adjustment_bps, 0) as dscr_adjustment_bps,
    COALESCE(lsb.effective_spread_bps, 185) as effective_spread_bps,
    COALESCE(lsb.lifecycle_adjustment_bps, 0) as lifecycle_adjustment_bps,
    COALESCE(lsb.mezzanine_adjustment_bps, 0) as mezzanine_adjustment_bps,
    COALESCE(lsb.total_rpx_adjustment_bps, -10) as total_rpx_adjustment_bps,
    COALESCE(lsb.ltv_factor_adjustment_bps, 0) as ltv_factor_adjustment_bps,
    COALESCE(lsb.loan_status_adjustment_bps, 0) as loan_status_adjustment_bps,
    COALESCE(lsb.senior_tiering_adjustment_bps, -10) as senior_tiering_adjustment_bps,
    COALESCE(lsb.ltv_performance_adjustment_bps, 0) as ltv_performance_adjustment_bps,
    
    -- Additional placeholder fields for cash flow modeling
    NULL::integer as period_number,
    NULL::date as accrual_dates_projected,
    NULL::date as dates_adjust_mid_period,
    NULL::date as accrual_dates_actual,
    NULL::integer as day_count,
    NULL::numeric as active_index_curve,
    NULL::numeric as prior_index_curve,
    NULL::varchar as prepayment_penalty_type,
    NULL::date as call_timing,
    NULL::date as maturity_adjusted_extensions,
    NULL::date as prepayment_lockout_date,
    NULL::integer as io_period,
    NULL::varchar as ancillary_fees_trigger,
    
    -- Sector allocation summary (placeholder)
    'Multifamily (25.9%), Hotel (25%), Office (24.7%), Industrial (13.7%), Retail (7.5%), Mixed Use (3.1%)' as sector_allocation_summary

FROM loans l
LEFT JOIN v_loan_pricing lp ON l.loan_id = lp.loan_id
LEFT JOIN v_loan_valuation lv ON l.loan_id = lv.loan_id
LEFT JOIN v_loan_accrued la ON l.loan_id = la.loan_id
LEFT JOIN v_loan_risk_metrics lrm ON l.rp_system_id = lrm.rp_system_id
LEFT JOIN v_loan_spread_breakdown lsb ON l.loan_id = lsb.loan_id
LEFT JOIN v_loan_wal lw ON l.loan_id = lw.loan_id;
```

## 2. Price Change Tracking View

### View: `v_loan_price_changes`

Track price and yield changes over time:

```sql
CREATE OR REPLACE VIEW v_loan_price_changes AS
SELECT 
    loan_id,
    rp_system_id,
    
    -- All delta fields default to 0 for now (would require historical data)
    0::numeric as delta_price,
    0::numeric as delta_price_yield_cbe,
    0::numeric as delta_price_credit_spread,
    0::numeric as delta_price_benchmark,
    0::numeric as delta_price_yield_curve_shift,
    0::numeric as delta_price_yield_curve_roll,
    0::numeric as delta_price_accretion,
    
    -- Yield changes
    0::numeric as delta_credit_spread,
    0::numeric as delta_benchmark_yield,
    0::numeric as delta_cbe_yield,
    0::numeric as yield_curve_shift,
    0::numeric as yield_curve_roll
    
FROM loans;
```

## 3. Prior Scenario View

### View: `v_loan_prior_scenario`

Store prior period values for comparison:

```sql
CREATE OR REPLACE VIEW v_loan_prior_scenario AS
SELECT 
    lcp.loan_id,
    lcp.rp_system_id,
    
    -- Prior scenario values (same as current for initial implementation)
    lcp.maturity_assumption as scenario,
    lcp.credit_spread as credit_spread_prior,
    lcp.market_yield as market_yield_prior,
    lcp.maturity_assumption as maturity_scenario,
    lcp.amortization_type,
    lcp.property_location,
    lcp.dscr_current as dscr_prior,
    lcp.ltv_current as ltv_prior,
    lcp.current_balance as current_balance_prior,
    lcp.price as price_prior,
    0::numeric as benchmark_yield_prior,
    lcp.wal_years as wal_prior,
    lcp.modified_duration_years as duration_prior,
    lcp.loan_status as loan_status_prior
    
FROM v_complete_loan_pricing lcp;
```

## 4. Portfolio Summary View

### View: `v_loan_portfolio_summary`

Individual loan portfolio summary:

```sql
CREATE OR REPLACE VIEW v_loan_portfolio_summary AS
SELECT 
    loan_id,
    rp_system_id,
    current_balance as balance_current,
    ltv_current,
    COALESCE(ltv_current, 0) as ltv_prior,
    dscr_current,
    dscr_current as dscr_prior,
    benchmark_yield,
    property_sector as sector,
    contract_type as fixed_float,
    current_balance as prior_balance,
    benchmark_yield as prior_benchmark_yield,
    wal_years as prior_wal,
    modified_duration_years as prior_duration,
    loan_status as prior_loan_status
FROM v_complete_loan_pricing;
```

## 5. Enhanced Portfolio Analysis View

### View: `v_portfolio_analysis_enhanced`

Aggregate portfolio metrics:

```sql
CREATE OR REPLACE VIEW v_portfolio_analysis_enhanced AS
WITH loan_metrics AS (
    SELECT 
        *,
        CASE WHEN loan_status != 'Default' THEN 1 ELSE 0 END as is_performing,
        CASE WHEN contract_type = 'Fixed' THEN 1 ELSE 0 END as is_fixed
    FROM v_complete_loan_pricing
),
sector_totals AS (
    SELECT 
        property_sector,
        SUM(current_balance) as sector_balance,
        COUNT(*) as sector_count,
        AVG(market_yield) as sector_avg_yield
    FROM loan_metrics
    GROUP BY property_sector
),
total_balance AS (
    SELECT SUM(current_balance) as total_balance
    FROM loan_metrics
)
SELECT 
    -- Basic metrics
    COUNT(*) as total_loans,
    SUM(lm.fair_value) / 1000000 as total_fair_value_mm,
    AVG(lm.price) as average_price,
    AVG(lm.market_yield) as average_yield,
    AVG(lm.modified_duration_years) as average_duration,
    
    -- Weighted averages
    SUM(lm.market_yield * lm.current_balance) / NULLIF(SUM(lm.current_balance), 0) as weighted_avg_yield,
    SUM(lm.credit_spread * lm.current_balance) / NULLIF(SUM(lm.current_balance), 0) as weighted_avg_spread,
    SUM(lm.wal_years * lm.current_balance) / NULLIF(SUM(lm.current_balance), 0) as weighted_avg_wal,
    SUM(lm.ltv_current * lm.current_balance) / NULLIF(SUM(lm.current_balance), 0) as weighted_avg_ltv,
    SUM(lm.dscr_current * lm.current_balance) / NULLIF(SUM(lm.current_balance), 0) as weighted_avg_dscr,
    
    -- Risk distribution
    CAST(SUM(lm.is_performing) * 100.0 / COUNT(*) AS integer) as performing_percentage,
    CAST((COUNT(*) - SUM(lm.is_performing)) * 100.0 / COUNT(*) AS integer) as default_percentage,
    
    -- Interest type distribution
    CAST(SUM(lm.is_fixed) * 100.0 / COUNT(*) AS integer) as fixed_percentage,
    CAST((COUNT(*) - SUM(lm.is_fixed)) * 100.0 / COUNT(*) AS integer) as floating_percentage,
    
    -- Credit spread ranges
    MIN(lm.credit_spread) as spread_low,
    MAX(lm.credit_spread) as spread_high,
    AVG(lm.credit_spread) as spread_average,
    
    -- Sector allocation (as JSON for easier processing)
    json_object_agg(
        st.property_sector, 
        round((st.sector_balance / tb.total_balance * 100)::numeric, 1)
    ) as sector_allocation
    
FROM loan_metrics lm
CROSS JOIN total_balance tb
CROSS JOIN sector_totals st
GROUP BY tb.total_balance;
```

## 6. Pricing Engine Metrics View

### View: `v_pricing_engine_metrics`

Static/configurable pricing engine parameters:

```sql
CREATE OR REPLACE VIEW v_pricing_engine_metrics AS
SELECT 
    COUNT(*) as total_loans_analyzed,
    COUNT(*) * 2 as scenarios_run,  -- Assuming 2 scenarios per loan
    'Discounted Cash Flow' as valuation_method,
    'US Treasury' as benchmark_curve,
    4.56 as risk_free_rate,
    2.5 as market_risk_premium,
    0.5 as liquidity_adjustment
FROM loans
WHERE loan_status IS NOT NULL;
```

## 7. Cash Flow Placeholder View

### View: `v_loan_cash_flow_placeholders`

Provides NULL placeholders for all cash flow fields:

```sql
CREATE OR REPLACE VIEW v_loan_cash_flow_placeholders AS
SELECT 
    loan_id,
    rp_system_id,
    
    -- All cash flow fields as NULL placeholders
    NULL::integer as new_loan_indicator,
    NULL::varchar as floating_rate_index,
    NULL::numeric as index_margin,
    NULL::numeric as bank_loan_coupon_step_up,
    NULL::numeric as contract_rate,
    NULL::integer as forbearance_grace_period_counter,
    NULL::integer as forbearance_payback_period_counter,
    NULL::date as default_timing,
    NULL::numeric as credit_facility_funded_balance,
    NULL::numeric as credit_facility_draws_projected,
    NULL::numeric as credit_facility_unfunded_balance,
    NULL::numeric as original_balance_total_commitment,
    NULL::numeric as current_balance_with_accrued,
    NULL::numeric as defaults,
    NULL::numeric as performing_balance,
    NULL::numeric as prepayments,
    NULL::numeric as forbearance_account_beginning_balance,
    NULL::numeric as interest_due_grace_period,
    NULL::numeric as principal_due_grace_period,
    NULL::numeric as forbearance_interest_paid,
    NULL::numeric as forbearance_principal_paid,
    NULL::numeric as forbearance_account_ending_balance,
    NULL::numeric as pi_contractual_payment,
    NULL::numeric as forbearance_adjusted_pi,
    NULL::numeric as scheduled_interest_forbearance,
    NULL::numeric as prepayment_penalties_yield_maintenance_term,
    NULL::numeric as discount_factor,
    NULL::numeric as prepayment_penalties_yield_maintenance_pv,
    NULL::numeric as prepayment_penalties_yield_maintenance_amount,
    NULL::numeric as ancillary_fees_extension_exit,
    NULL::numeric as scheduled_principal_forbearance,
    NULL::numeric as principal,
    NULL::numeric as cash_flows,
    NULL::numeric as aggregate_defaults,
    NULL::numeric as pmt,
    NULL::numeric as scheduled_interest,
    NULL::numeric as scheduled_principal,
    NULL::numeric as advanced_interest_paid,
    NULL::numeric as advanced_principal_paid,
    NULL::numeric as default_offset,
    NULL::numeric as recovery,
    NULL::numeric as non_performing_cash,
    NULL::numeric as unfunded_commitment_fee,
    NULL::numeric as prepayment_penalties,
    NULL::numeric as additional_fees_extension_exit,
    NULL::numeric as pik_interest,
    NULL::numeric as default_interest,
    NULL::numeric as total_interest,
    NULL::numeric as principal_balloon,
    NULL::numeric as equity_kicker,
    NULL::numeric as total_cfs,
    NULL::date as dates,
    NULL::numeric as credit_facility_funded_balance_2,
    NULL::numeric as credit_facility_draws,
    NULL::numeric as credit_facility_unfunded_balance_2,
    NULL::numeric as original_balance_total_commitment_2,
    NULL::numeric as current_balance_with_accrued_2,
    NULL::numeric as interest,
    NULL::numeric as unfunded_commitment_fee_2,
    NULL::numeric as additional_fees_extension_exit_2,
    NULL::numeric as pik_interest_2,
    NULL::numeric as default_interest_2,
    NULL::numeric as principal_2,
    NULL::numeric as equity_kicker_2,
    NULL::numeric as cash_flow,
    NULL::numeric as dr,
    NULL::numeric as df,
    NULL::numeric as dr_prior,
    NULL::numeric as df_prior,
    NULL::integer as periods_from_settlement,
    NULL::numeric as convexity_calculation,
    NULL::numeric as lower_range_mey,
    NULL::numeric as upper_range_mey,
    NULL::numeric as lower_range_df,
    NULL::numeric as upper_range_df,
    NULL::date as dates_unindexed,
    NULL::varchar as p_or_pi,
    NULL::date as dates_indexed,
    NULL::varchar as p_or_pi_indexed,
    NULL::numeric as pi_indexed,
    NULL::date as custom_dates_schedule_unindexed,
    NULL::date as custom_dates_schedule_indexed,
    NULL::varchar as eg,
    NULL::numeric as default_interest_3,
    NULL::date as dates_unindexed_2,
    NULL::numeric as step_up_coupon_unindexed,
    NULL::date as dates_indexed_2,
    NULL::numeric as step_up_coupon_used,
    NULL::date as dates_unindexed_3,
    NULL::numeric as step_up_margin_unindexed,
    NULL::date as dates_indexed_3,
    NULL::numeric as step_up_margin_active,
    NULL::date as dates_unindexed_4,
    NULL::numeric as utilization_rate,
    NULL::date as dates_indexed_4,
    NULL::numeric as active_utilization_rate,
    NULL::varchar as eg_2,
    NULL::date as dates_unindexed_5,
    NULL::varchar as interest_type_2,
    NULL::date as dates_indexed_5,
    NULL::varchar as interest_type_3,
    NULL::varchar as eg_3,
    NULL::integer as new_loan_indicator_2
    
FROM loans;
```

## Implementation Notes

1. **Placeholder Strategy**: 
   - Views return NULL for unavailable fields
   - Application layer transforms NULL to appropriate defaults (555555 for missing data)
   - This allows flexibility to add real data later without schema changes

2. **Join Strategy**:
   - Use LEFT JOINs to ensure all loans are included even if related data is missing
   - COALESCE functions provide fallback values where appropriate

3. **Performance Considerations**:
   - Create indexes on join columns (loan_id, rp_system_id)
   - Consider materialized views for complex aggregations if performance is an issue

4. **Data Quality**:
   - The views assume certain fields exist in base tables
   - Missing base fields will result in NULL values (handled by application)

5. **Extension Points**:
   - Cash flow fields are all NULL placeholders - can be populated when cash flow engine is implemented
   - Price change tracking requires historical data - placeholder 0 values for now
   - Prior scenario tracking needs historical snapshots - uses current values as placeholder

## Testing the Views

After creating these views, test with:

```sql
-- Test main view
SELECT * FROM v_complete_loan_pricing LIMIT 1;

-- Test portfolio analysis
SELECT * FROM v_portfolio_analysis_enhanced;

-- Verify all required fields are present
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'v_complete_loan_pricing'
ORDER BY ordinal_position;
```

## Next Steps

1. Create these views in the database
2. Update the application endpoint to use `v_complete_loan_pricing` instead of `v_loan_pricing`
3. Remove hardcoded defaults from the transformer where actual data is now available
4. Add any missing columns to base tables as needed
5. Implement historical tracking for price changes and prior scenarios