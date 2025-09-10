# Materialized Views Documentation

## Overview

This document provides comprehensive documentation of all materialized views in the RPX Backend system. These views were implemented to solve critical performance issues where regular views were timing out (2+ minutes) and now provide sub-second response times (~100-150ms).

## Materialized Views Inventory

### Current Materialized Views (8 total)

| View Name | Size | Purpose | Dependencies |
|-----------|------|---------|--------------|
| `mv_excel_calculation_cache` | 56 KB | Caches Excel export calculations | Base tables |
| `mv_loan_accrued` | 56 KB | Accrued interest calculations | loans, valuation_config |
| `mv_loan_benchmark_yields` | 56 KB | Benchmark yield interpolations | loans, market_benchmarks |
| `mv_loan_pricing` | 56 KB | WAL, duration, price calculations | loans, market_benchmarks, pricing_data |
| `mv_loan_rpx_adjustments` | 56 KB | RPX spread and factor adjustments | loans, rpx_* tables |
| `mv_loan_spread` | 56 KB | Credit spread calculations | loans, pricing_data_class_spreads |
| `mv_loan_valuation` | 64 KB | Fair value computations | loans, market_benchmarks |
| `mv_pricing_engine_output_complete` | 112 KB | Final aggregated pricing output | All Level 1 views |

## View Hierarchy and Dependencies

### Level 1: Base Calculation Views
These views perform the core calculations and must be refreshed first:

1. **mv_loan_pricing**
   - Calculates: WAL (Weighted Average Life), Duration, Convexity
   - Depends on: loans, market_benchmarks, pricing_data_fixed, pricing_data_floating
   - Used by: mv_pricing_engine_output_complete

2. **mv_loan_valuation**
   - Calculates: Fair value, PV calculations
   - Depends on: loans, market_benchmarks, valuation_config
   - Used by: mv_pricing_engine_output_complete

3. **mv_loan_accrued**
   - Calculates: Accrued interest, interest payments
   - Depends on: loans, valuation_config
   - Used by: mv_pricing_engine_output_complete

4. **mv_loan_spread**
   - Calculates: Credit spreads, RPX adjustments
   - Depends on: loans, pricing_data_class_spreads, rpx_spread_adjustment
   - Used by: mv_pricing_engine_output_complete

5. **mv_loan_benchmark_yields**
   - Calculates: Interpolated benchmark yields for each loan
   - Depends on: loans, market_benchmarks
   - Used by: mv_loan_pricing, mv_loan_valuation

6. **mv_loan_rpx_adjustments**
   - Calculates: RPX-specific adjustments (INTERNAL USE ONLY)
   - Depends on: loans, rpx_ltv_factor_adjustment, rpx_dscr_adjustment
   - Used by: mv_loan_spread

7. **mv_excel_calculation_cache**
   - Purpose: Pre-calculated Excel export data
   - Depends on: Multiple base tables
   - Used by: Excel export endpoints

### Level 2: Aggregation View
This view combines data from Level 1 views:

8. **mv_pricing_engine_output_complete**
   - Purpose: Final pricing engine output with all calculations
   - Depends on: All Level 1 views
   - Contains: 40+ columns of pricing data
   - Primary consumer: API endpoints and Excel exports

## Refresh Strategy

### Refresh Order (CRITICAL)
Views MUST be refreshed in dependency order:

```sql
-- Step 1: Refresh Level 1 views (can be parallelized)
REFRESH MATERIALIZED VIEW mv_loan_benchmark_yields;
REFRESH MATERIALIZED VIEW mv_loan_rpx_adjustments;
REFRESH MATERIALIZED VIEW mv_loan_pricing;
REFRESH MATERIALIZED VIEW mv_loan_valuation;
REFRESH MATERIALIZED VIEW mv_loan_accrued;
REFRESH MATERIALIZED VIEW mv_loan_spread;
REFRESH MATERIALIZED VIEW mv_excel_calculation_cache;

-- Step 2: Refresh Level 2 view (after Level 1 completes)
REFRESH MATERIALIZED VIEW mv_pricing_engine_output_complete;
```

### Refresh Triggers

Refresh is required when these tables are modified:
- `loans` - Core loan data
- `market_benchmarks` - Market rate updates
- `pricing_data_fixed` / `pricing_data_floating` - Pricing updates
- `pricing_data_class_spreads` - Credit spread updates
- `rpx_*_adjustment` tables - RPX methodology changes
- `valuation_config` - Valuation parameter changes

### Refresh Performance

| View | Typical Refresh Time |
|------|---------------------|
| Level 1 views | 2-3 seconds each |
| mv_pricing_engine_output_complete | <1 second |
| **Total refresh time** | **10-15 seconds** |

## API Integration

### Manual Refresh Endpoint
```
POST /api/v1/valuation/the-refresh
```
- Refreshes all materialized views in correct order
- Returns timing and status for each view
- Total duration: ~10-15 seconds

### Endpoints Using Materialized Views

| Endpoint | Materialized View Used |
|----------|----------------------|
| `/api/v1/valuation/pricing-output` | mv_pricing_engine_output_complete |
| `/api/v1/valuation/loan-pricing` | mv_loan_pricing |
| `/api/v1/valuation/loan-valuation` | mv_loan_valuation |
| `/api/v1/valuation/loan-accrued` | mv_loan_accrued |
| `/api/v1/valuation/loan-spread-breakdown` | mv_loan_spread |
| `/api/v1/exports/pricing-results/excel` | mv_pricing_engine_output_complete |
| `/api/v1/exports/complete-report/excel` | Multiple materialized views |

## Performance Impact

### Before Materialized Views
- Query time: 2+ minutes (timeout)
- Excel exports: Failed due to timeout
- User experience: Unusable

### After Materialized Views
- Query time: 100-150ms
- Excel exports: 100-300ms
- User experience: Instant response
- **Performance improvement: ~1200x**

## Monitoring and Maintenance

### Health Checks
1. **Population Status**
   ```sql
   SELECT matviewname, ispopulated 
   FROM pg_matviews 
   WHERE matviewname LIKE 'mv_%';
   ```

2. **Size Monitoring**
   ```sql
   SELECT matviewname, 
          pg_size_pretty(pg_total_relation_size(matviewname::regclass)) as size
   FROM pg_matviews 
   WHERE matviewname LIKE 'mv_%'
   ORDER BY pg_total_relation_size(matviewname::regclass) DESC;
   ```

3. **Last Refresh Time** (requires custom tracking)
   ```sql
   -- This would require implementing refresh logging
   SELECT view_name, last_refresh_time 
   FROM materialized_view_refresh_log
   ORDER BY last_refresh_time DESC;
   ```

### Common Issues and Solutions

1. **View Not Populated**
   - Symptom: Query returns no data
   - Solution: Run manual refresh via API or SQL

2. **Stale Data**
   - Symptom: Data doesn't reflect recent changes
   - Solution: Implement automated refresh schedule

3. **Refresh Failures**
   - Symptom: Refresh endpoint returns errors
   - Check: Disk space, locks, dependency issues
   - Solution: Check logs, ensure proper refresh order

## Security Considerations

### RPX Adjustments (CONFIDENTIAL)
The following views contain proprietary RPX pricing methodology and should NOT be exposed to end users:
- `mv_loan_rpx_adjustments`
- Any fields containing "rpx_adjustment" in other views

Frontend applications should:
- Hide RPX adjustment fields
- Show only final calculated values
- Never expose adjustment factors or methodology

## Future Enhancements

### Planned Improvements
1. **Automated Refresh Scheduling**
   - Implement cron-based refresh
   - Configure based on business hours
   - Different schedules for different views

2. **Refresh Logging**
   - Track refresh history
   - Monitor performance trends
   - Alert on failures

3. **Incremental Refresh**
   - Implement CONCURRENTLY option where possible
   - Reduce lock time during refresh
   - Maintain availability during updates

4. **Monitoring Dashboard**
   - Real-time view status
   - Refresh history visualization
   - Performance metrics

## Best Practices

1. **Always refresh in dependency order**
2. **Monitor view sizes** - Large growth may indicate issues
3. **Test refresh after schema changes**
4. **Document any new dependencies**
5. **Keep refresh times under 15 seconds**
6. **Implement alerting for refresh failures**
7. **Hide internal calculations from end users**

## Appendix: View Definitions

### Example: mv_loan_pricing
```sql
CREATE MATERIALIZED VIEW mv_loan_pricing AS
SELECT 
    l.rp_system_id,
    l.loan_id,
    -- WAL calculation
    CASE 
        WHEN l.amortization_type = 'Bullet' THEN 
            EXTRACT(YEAR FROM AGE(l.maturity_date, CURRENT_DATE))
        ELSE 
            -- Complex WAL calculation for amortizing loans
            ...
    END as wal_years,
    -- Duration calculation
    ... as modified_duration_years,
    -- Price calculation
    ... as price
FROM loans l
LEFT JOIN market_benchmarks mb ON ...
WHERE l.loan_status != 'Closed';
```

## Contact

For questions or issues related to materialized views:
- Backend Team Lead
- Database Administrator
- DevOps Team (for monitoring/alerting)