# Benchmark Rates and Credit Spreads API Documentation

## Overview

The RPX Backend provides endpoints for managing market benchmark rates and credit spreads, which are essential for loan valuation and pricing calculations.

## Benchmark Rates

### Data Model
- **Table**: `market_benchmarks`
- **Key Fields**:
  - `benchmark_type`: Type of benchmark (e.g., '1M SOFR', '3M SOFR', 'UST')
  - `term_years`: Term in years (e.g., 0.0833 for 1 month, 10 for 10 years)
  - `rate`: Interest rate as decimal (0.0525 = 5.25%)
  - `benchmark_date`: Effective date of the rate
  - `currency`: Currency code (default: 'USD')
  - `source`: Data source identifier

### Endpoints

#### GET /api/v1/portfolios/benchmarks/current
Returns the most recent benchmark rates.

**Response Example:**
```json
[
  {"benchmark_type": "1M SOFR", "tenor": "0.0833", "rate": 0.0525, "date": "2024-01-15"},
  {"benchmark_type": "3M SOFR", "tenor": "0.2500", "rate": 0.0530, "date": "2024-01-15"},
  {"benchmark_type": "UST", "tenor": "10", "rate": 0.0425, "date": "2024-01-15"}
]
```

#### PUT /api/v1/portfolios/benchmarks
Updates benchmark rates. Supports two input formats:

**Dictionary Format** (for common benchmarks):
```json
{
  "effective_date": "2024-01-15",
  "rates": {
    "SOFR1M": 0.0525,      // Converts to '1M SOFR', term_years=0.0833
    "SOFR3M": 0.0530,      // Converts to '3M SOFR', term_years=0.25
    "SOFR6M": 0.0535,      // Converts to '6M SOFR', term_years=0.5
    "Treasury10Y": 0.0425  // Converts to 'UST', term_years=10
  },
  "source": "Fed Data"
}
```

**List Format** (for detailed control):
```json
{
  "effective_date": "2024-01-15",
  "rates": [
    {"benchmark_type": "UST", "tenor": "5", "rate": 0.041},
    {"benchmark_type": "UST", "tenor": "30", "rate": 0.045}
  ],
  "source": "Bloomberg"
}
```

#### POST /api/v1/portfolios/benchmarks/bulk-upload
Bulk upload historical benchmark rates from CSV files.

**Request:**
```json
{
  "benchmark_type": "SOFR",
  "file": "rates.csv",
  "validate_only": false
}
```

## Credit Spreads

### Data Model
- **Table**: `pricing_data_class_spreads`
- **Key Fields**:
  - `property_type`: Property sector (e.g., 'Office', 'Retail', 'Multifamily')
  - `loan_class`: Risk classification (e.g., 'ClassA', 'Class B/C')
  - `spread`: Credit spread as decimal (0.025 = 250 bps)
  - `pricing_date`: Effective date of the spread
  - `source_column`: Data source identifier

### Endpoints

#### GET /api/v1/portfolios/spreads
Returns the most recent credit spreads.

**Response Example:**
```json
[
  {"property_sector": "Office", "term_bucket": "ClassA", "spread_bps": 250, "date": "2024-01-15"},
  {"property_sector": "Retail", "term_bucket": "Class B/C", "spread_bps": 300, "date": "2024-01-15"}
]
```

#### PUT /api/v1/portfolios/spreads
Updates credit spreads.

**Request:**
```json
{
  "effective_date": "2024-01-15",
  "spreads": [
    {"property_sector": "Office", "term_bucket": "ClassA", "spread_bps": 250},
    {"property_sector": "Retail", "term_bucket": "Class B/C", "spread_bps": 300}
  ],
  "notes": "Q1 2024 market update"
}
```

Note: `spread_bps` is in basis points (250 = 2.50%). The API automatically converts to decimal for storage.

#### POST /api/v1/portfolios/spreads/bulk-upload
Bulk upload credit spreads from CSV files.

**Request:**
```json
{
  "effective_date": "2024-01-15",
  "file": "spreads.csv",
  "validate_only": false
}
```

## Usage Notes

1. **Authentication**: These endpoints are intended for admin users. Implement appropriate authentication in production.

2. **Data Validation**: 
   - Dates should be in ISO format (YYYY-MM-DD)
   - Rates are stored as decimals (5.25% = 0.0525)
   - Spreads are input as basis points but stored as decimals

3. **Conflict Resolution**: 
   - For benchmarks: Updates existing records based on (benchmark_date, benchmark_type, term_years, currency)
   - For spreads: Updates based on (pricing_date, property_type, loan_class)

4. **Historical Data**: Both benchmarks and spreads support historical data. The GET endpoints return the most recent values by default.