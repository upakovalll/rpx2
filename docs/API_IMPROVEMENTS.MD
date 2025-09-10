# API Improvements: Missing CRUD Endpoints

This document lists the missing CRUD (Create, Read, Update, Delete) endpoints for the following resources:
- Loan
- Pricing Data
- Benchmark Rates

---

## 1. Loan
**Implemented:**
- GET /loans/ (list all loans)
- GET /loans/{rp_system_id} (get loan by ID)
- GET /loans/by-system-id/{rp_system_id} (get loan details)
- POST /loans/ (create loan)
- PUT /loans/{rp_system_id} (update loan)
- PUT /loans/by-system-id/{rp_system_id} (update loan by system ID)
- DELETE /loans/{rp_system_id} (delete loan)

**Missing:**
- None (Full CRUD implemented)

---

## 2. Pricing Data
**Implemented:**
- GET endpoints for various pricing/valuation views (e.g., /valuation/pricing-output, /valuation/loan-pricing, /valuation/loan-valuation, etc.)

**Missing:**
- POST /valuation/pricing-data (create new pricing data)
- PUT /valuation/pricing-data/{id} (update pricing data)
- DELETE /valuation/pricing-data/{id} (delete pricing data)

> **Note:** All pricing data endpoints are currently read-only (GET). There are no endpoints to create, update, or delete pricing data records.

---

## 3. Benchmark Rates
**Implemented:**
- GET /portfolios/benchmarks/current (get current benchmark rates)
- GET /portfolios/benchmark-rates-view (get benchmark rates view)
- PUT /portfolios/benchmarks (update benchmark rates)
- POST /portfolios/benchmarks/bulk-upload (bulk upload benchmark rates)

**Missing:**
- POST /portfolios/benchmarks (create a new benchmark rate for a specific date/type/tenor)
- DELETE /portfolios/benchmarks/{benchmark_id} (delete a benchmark rate)
- GET /portfolios/benchmarks/{benchmark_id} (get a specific benchmark rate by ID)

> **Note:** There is no single-record create (POST) or delete (DELETE) endpoint for benchmark rates. Only update (PUT) and bulk upload (POST) are implemented.

---

## 4. Credit Spreads
**Implemented:**
- GET /portfolios/spreads (get current credit spreads)
- PUT /portfolios/spreads (update credit spreads)
- POST /portfolios/spreads/bulk-upload (bulk upload credit spreads)

**Missing:**
- POST /portfolios/spreads (create a new credit spread for a specific date/type/bucket)
- DELETE /portfolios/spreads/{spread_id} (delete a credit spread)
- GET /portfolios/spreads/{spread_id} (get a specific credit spread by ID)

> **Note:** There is no single-record create (POST) or delete (DELETE) endpoint for credit spreads. Only update (PUT) and bulk upload (POST) are implemented.

---

## Summary Table

| Resource        | GET | POST | PUT | DELETE |
|-----------------|-----|------|-----|--------|
| Loan            | ✔️  | ✔️   | ✔️  | ✔️     |
| Pricing Data    | ✔️  | ❌   | ❌  | ❌     |
| Benchmark Rates | ✔️  | ❌   | ✔️  | ❌     |
| Credit Spreads  | ✔️  | ❌   | ✔️  | ❌     |

---

**Legend:**
- ✔️ = Implemented
- ❌ = Missing 

---

# Missing CRUD Operations and Field Coverage

## Loan
- **CRUD:** Full CRUD is implemented.
- **Field Coverage:**
  - Some database columns (e.g., `x1`, `x2`, `x3`, and some JSON fields) are not present in the API schemas.
  - The API uses a nested `property_locations` object, while the DB has both embedded property fields and a separate `loan_properties` table.
  - `created_at` and `updated_at` are only exposed in some response models.
  - Some DB fields (e.g., `property_street`, `property_city`, etc.) are not present in the main API schemas, as they are handled via the property locations subresource.
  - **Recommendation:** Consider exposing all fields (including `x1`, `x2`, `x3`, and all JSON fields) in the API, or document why they are omitted. Ensure all business-critical fields are present in both API and DB.

## Pricing Data
- **CRUD:** Only GET endpoints are implemented; POST, PUT, DELETE are missing.
- **Field Coverage:**
  - No Pydantic schema for creating/updating pricing data; cannot POST/PUT new pricing records.
  - **Recommendation:** Implement POST, PUT, DELETE endpoints for pricing data. Add Pydantic schemas for pricing data creation and update, covering all columns in the `loan_pricing` table.

## Benchmark Rates
- **CRUD:**
  - GET (list, view) and PUT (update) are implemented.
  - POST (single create) and DELETE (single delete) are missing.
  - Bulk upload POST exists, but not single-record POST.
- **Field Coverage:**
  - API schemas cover main fields, but DB also has `id`, `currency`, `source`, and `created_at`.
  - `id` is not exposed in the API, so you cannot reference or delete a specific benchmark rate by ID.
  - `currency` and `source` are only partially exposed.
  - **Recommendation:** Add POST and DELETE endpoints for single benchmark rates. Expose `id`, `currency`, and `source` fields in the API schemas and endpoints. Add GET by ID endpoint for benchmark rates.

## Credit Spreads
- **CRUD:**
  - GET (list, view) and PUT (update) are implemented.
  - POST (single create) and DELETE (single delete) are missing.
  - Bulk upload POST exists, but not single-record POST.
- **Field Coverage:**
  - API schemas cover main fields, but DB also has `id`, `source_column`, and `created_at`.
  - `id` is not exposed in the API, so you cannot reference or delete a specific credit spread by ID.
  - `source_column` and `created_at` are not exposed.
  - **Recommendation:** Add POST and DELETE endpoints for single credit spreads. Expose `id`, `source_column`, and `created_at` fields in the API schemas and endpoints. Add GET by ID endpoint for credit spreads.

---

# Existing API Endpoints

Below is a list of all currently implemented API endpoints, grouped by resource/module:

## Loan Endpoints (`/loans`)
- GET    /loans/                              (list all loans)
- GET    /loans/{rp_system_id}                (get loan by ID)
- GET    /loans/by-system-id/{rp_system_id}   (get loan details by system ID)
- POST   /loans/                              (create loan)
- PUT    /loans/{rp_system_id}                (update loan)
- PUT    /loans/by-system-id/{rp_system_id}   (update loan by system ID)
- DELETE /loans/{rp_system_id}                (delete loan)

## Property Location Endpoints (`/property-locations`)
- GET    /property-locations/                  (list all property locations)
- DELETE /property-locations/{location_id}     (delete property location)

## Portfolio & Benchmark Endpoints (`/portfolios`)
- GET    /portfolios/                          (portfolio summary - returns empty)
- GET    /portfolios/summary                   (portfolio summary stats)
- GET    /portfolios/risk-metrics              (portfolio risk metrics)
- GET    /portfolios/benchmarks/current        (current benchmark rates)
- GET    /portfolios/spreads                   (current credit spreads)
- GET    /portfolios/summary-view              (pricing summary view)
- GET    /portfolios/benchmark-rates-view      (benchmark rates view)
- PUT    /portfolios/benchmarks                (update benchmark rates)
- POST   /portfolios/benchmarks/bulk-upload    (bulk upload benchmark rates)
- PUT    /portfolios/spreads                   (update credit spreads)
- POST   /portfolios/spreads/bulk-upload       (bulk upload credit spreads)
- GET    /portfolios/{portfolio_id}            (get portfolio by ID - not implemented)
- POST   /portfolios/                          (create portfolio)
- PUT    /portfolios/{portfolio_id}            (update portfolio)
- DELETE /portfolios/{portfolio_id}            (delete portfolio)

## Valuation & Pricing Data Endpoints (`/valuation`)
- GET    /valuation/pricing-output             (loan pricing output)
- GET    /valuation/loan-valuation             (loan valuation data)
- GET    /valuation/loan-pricing               (loan pricing data)
- GET    /valuation/loan-risk-metrics          (loan risk metrics)
- GET    /valuation/loan-spread-breakdown      (loan spread breakdown)
- GET    /valuation/loan-summary               (loan summary)
- GET    /valuation/loan-benchmark             (loan benchmark data)
- GET    /valuation/loan-wal                   (loan weighted average life)
- GET    /valuation/loans-in-forbearance       (loans in forbearance)
- GET    /valuation/loan-accrued               (loan accrued interest)
- GET    /valuation/portfolio-summary          (portfolio summary - not implemented)
- GET    /valuation/pricing-summary            (pricing summary)
- GET    /valuation/benchmark-current          (current benchmark rates)
- GET    /valuation/current-pricing-spreads    (current pricing spreads) 

---

# Database Table Details for API Resources

## loans
| Column                        | Type                | Nullable | Default                |
|-------------------------------|---------------------|----------|------------------------|
| rp_system_id                  | character varying   | NO       |                        |
| pricing_scenario              | character varying   | YES      |                        |
| maturity_assumption           | character varying   | YES      |                        |
| client_loan_number            | character varying   | YES      |                        |
| loan_name                     | character varying   | YES      |                        |
| property_sector               | character varying   | YES      |                        |
| property_type                 | character varying   | YES      |                        |
| property_lifecycle_financing  | character varying   | YES      |                        |
| sponsor_borrower              | character varying   | YES      |                        |
| original_balance              | numeric             | YES      |                        |
| current_balance               | numeric             | YES      |                        |
| currency                      | character varying   | YES      | 'USD'::character varying |
| client_percentage             | numeric             | YES      | 100                    |
| pik_balance                   | numeric             | YES      |                        |
| position_in_capital_stack     | character varying   | YES      |                        |
| amortization_type             | character varying   | YES      |                        |
| periodicity                   | character varying   | YES      |                        |
| interest_day_count            | character varying   | YES      |                        |
| io_end_date                   | date                | YES      |                        |
| original_amortization_term    | integer             | YES      |                        |
| contractual_pi_payment_amount | numeric             | YES      |                        |
| accrual_type                  | character varying   | YES      |                        |
| pik_coupon                    | numeric             | YES      |                        |
| commitment_type               | character varying   | YES      |                        |
| unfunded_commitment_fee       | numeric             | YES      |                        |
| interest_type                 | character varying   | YES      |                        |
| fixed_rate_coupon             | numeric             | YES      |                        |
| floating_rate_index           | character varying   | YES      |                        |
| floating_rate_margin          | numeric             | YES      |                        |
| index_cap                     | numeric             | YES      |                        |
| index_floor                   | numeric             | YES      |                        |
| ltv_current                   | numeric             | YES      |                        |
| dscr_current                  | numeric             | YES      |                        |
| debt_yield_current            | numeric             | YES      |                        |
| noi                           | numeric             | YES      |                        |
| property_appraisal_value      | numeric             | YES      |                        |
| property_appraisal_value_date | date                | YES      |                        |
| origination_date              | date                | YES      |                        |
| first_payment_date            | date                | YES      |                        |
| original_maturity_date        | date                | YES      |                        |
| prepayment_lockout_end_date   | date                | YES      |                        |
| open_call_period_date         | date                | YES      |                        |
| first_extension_date          | date                | YES      |                        |
| first_extension_fee           | numeric             | YES      |                        |
| second_extension_date         | date                | YES      |                        |
| second_extension_fee          | numeric             | YES      |                        |
| third_extension_date          | date                | YES      |                        |
| third_extension_fee           | numeric             | YES      |                        |
| exit_fee                      | numeric             | YES      |                        |
| loan_status                   | character varying   | YES      |                        |
| commentary                    | text                | YES      |                        |
| internal_credit_rating        | character varying   | YES      |                        |
| watchlist_monitoring          | character varying   | YES      |                        |
| properties_count              | integer             | YES      |                        |
| property_street               | character varying   | YES      |                        |
| property_city                 | character varying   | YES      |                        |
| property_state                | character varying   | YES      |                        |
| property_zip_code             | character varying   | YES      |                        |
| property_country              | character varying   | YES      | 'United States'::character varying |
| property_region               | character varying   | YES      |                        |
| step_up_date                  | date                | YES      |                        |
| step_up_incremental_rate      | numeric             | YES      |                        |
| prepayment_penalty_type       | character varying   | YES      |                        |
| prepayment_penalty_description| text                | YES      |                        |
| in_forbearance                | character varying   | YES      |                        |
| forbearance_start_date        | date                | YES      |                        |
| forbearance_original_term     | integer             | YES      |                        |
| forbearance_type              | character varying   | YES      |                        |
| forbearance_payback_start_date| date                | YES      |                        |
| forbearance_payback_term      | integer             | YES      |                        |
| credit_spread                 | numeric             | YES      |                        |
| market_yield                  | numeric             | YES      |                        |
| loss_scenario                 | character varying   | YES      |                        |
| pd                            | numeric             | YES      |                        |
| ead                           | numeric             | YES      |                        |
| lgd                           | numeric             | YES      |                        |
| lag_to_recovery               | integer             | YES      |                        |
| default_date                  | date                | YES      |                        |
| cdr                           | numeric             | YES      |                        |
| pi_scheduled_amortization     | jsonb               | YES      |                        |
| custom_payment_dates_schedule | jsonb               | YES      |                        |
| default_interest_schedule     | jsonb               | YES      |                        |
| preferred_equity_equity_kicker_schedule | jsonb     | YES      |                        |
| step_up_coupons               | jsonb               | YES      |                        |
| step_up_margin_interest_rate_floor | jsonb         | YES      |                        |
| proforma_assumptions          | jsonb               | YES      |                        |
| custom_interest_type_timing   | jsonb               | YES      |                        |
| x1                            | text                | YES      |                        |
| x2                            | text                | YES      |                        |
| x3                            | text                | YES      |                        |
| created_at                    | timestamp without time zone | YES | CURRENT_TIMESTAMP      |
| updated_at                    | timestamp without time zone | YES | CURRENT_TIMESTAMP      |

## loan_pricing
| Column            | Type                | Nullable | Default         |
|-------------------|---------------------|----------|-----------------|
| rp_system_id      | character varying   | NO       |                 |
| valuation_date    | date                | NO       |                 |
| reporting_period  | character varying   | YES      |                 |
| mark_frequency    | character varying   | YES      |                 |
| coupon            | numeric             | YES      |                 |
| pik_coupon        | numeric             | YES      |                 |
| spread            | numeric             | YES      |                 |
| margin            | numeric             | YES      |                 |
| index_name        | character varying   | YES      |                 |
| index_value       | numeric             | YES      |                 |
| yield             | numeric             | YES      |                 |
| yield_benchmark   | numeric             | YES      |                 |
| market_yield_cbe  | numeric             | YES      |                 |
| discount_rate     | numeric             | YES      |                 |
| price_clean       | numeric             | YES      |                 |
| price_dirty       | numeric             | YES      |                 |
| price_prior       | numeric             | YES      |                 |
| gross_proceeds    | numeric             | YES      |                 |
| net_proceeds      | numeric             | YES      |                 |
| accrued_interest  | numeric             | YES      |                 |
| modified_duration | numeric             | YES      |                 |
| wal               | numeric             | YES      |                 |
| wal_prior         | numeric             | YES      |                 |
| pd_estimate       | numeric             | YES      |                 |
| lgd_estimate      | numeric             | YES      |                 |
| recovery_estimate | numeric             | YES      |                 |
| fair_value_estimate| numeric            | YES      |                 |
| created_at        | timestamp without time zone | YES | CURRENT_TIMESTAMP |

## market_benchmarks
| Column         | Type                | Nullable | Default         |
|----------------|---------------------|----------|-----------------|
| id             | integer             | NO       | nextval('market_benchmarks_id_seq'::regclass) |
| benchmark_date | date                | NO       |                 |
| benchmark_type | character varying   | NO       |                 |
| term_years     | numeric             | NO       |                 |
| rate           | numeric             | YES      |                 |
| currency       | character varying   | NO       | 'USD'::character varying |
| source         | character varying   | YES      |                 |
| created_at     | timestamp without time zone | YES | CURRENT_TIMESTAMP |

## pricing_data_class_spreads
| Column         | Type                | Nullable | Default         |
|----------------|---------------------|----------|-----------------|
| id             | integer             | NO       | nextval('pricing_data_class_spreads_id_seq'::regclass) |
| pricing_date   | date                | NO       |                 |
| property_type  | character varying   | NO       |                 |
| loan_class     | character varying   | NO       |                 |
| spread         | numeric             | YES      |                 |
| source_column  | character varying   | YES      |                 |
| created_at     | timestamp without time zone | YES | CURRENT_TIMESTAMP |

## loan_properties
| Column         | Type                | Nullable | Default         |
|----------------|---------------------|----------|-----------------|
| id             | integer             | NO       | nextval('loan_properties_id_seq'::regclass) |
| rp_system_id   | character varying   | YES      |                 |
| property_number| integer             | YES      | 1               |
| street         | character varying   | YES      |                 |
| city           | character varying   | YES      |                 |
| state          | character varying   | YES      |                 |
| zip_code       | character varying   | YES      |                 |
| country        | character varying   | YES      | 'United States'::character varying |
| region         | character varying   | YES      |                 |
| created_at     | timestamp without time zone | YES | CURRENT_TIMESTAMP | 