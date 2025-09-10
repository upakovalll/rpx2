# Excel Export Functionality

## Overview

The RPX Backend 2026 provides comprehensive Excel export capabilities for loan data, pricing results, and portfolio analysis. All export endpoints are located under the `/api/v1/exports` prefix and return Excel files (.xlsx format) with properly formatted data.

## Available Export Endpoints

### 1. Loans Export

**Endpoint:** `GET /api/v1/exports/loans/excel`

**Description:** Exports loan data from the source `loans` table with optional property locations.

**Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Number of records to return (default: all)
- `include_properties` (bool, optional): Include property locations sheet (default: true)

**Excel Structure:**
- **Sheet 1 - Loans:** All columns from the `loans` table
- **Sheet 2 - Properties:** Property locations from `loan_properties` table (if `include_properties=true`)

**Example Usage:**
```bash
# Export first 100 loans with properties
curl -O "http://localhost:8000/api/v1/exports/loans/excel?limit=100"

# Export all loans without properties
curl -O "http://localhost:8000/api/v1/exports/loans/excel?include_properties=false"
```

### 2. Pricing Results Export

**Endpoint:** `GET /api/v1/exports/pricing-results/excel`

**Description:** Exports comprehensive pricing analysis results from various database views.

**Parameters:**
- `include_summary` (bool, optional): Include portfolio summary sheet (default: true)
- `include_risk_metrics` (bool, optional): Include risk metrics sheet (default: true)
- `include_market_data` (bool, optional): Include benchmarks and spreads sheet (default: true)

**Excel Structure:**
- **Sheet 1 - Pricing Results:** Data from `v_loan_pricing` view
- **Sheet 2 - Portfolio Summary:** Aggregated metrics from `v_portfolio_summary` (optional)
- **Sheet 3 - Risk Metrics:** Risk analysis from `v_loan_risk_metrics` (optional)
- **Sheet 4 - Market Data:** Current benchmarks and credit spreads (optional)

**Example Usage:**
```bash
# Export full pricing results
curl -O "http://localhost:8000/api/v1/exports/pricing-results/excel"

# Export only pricing results without additional sheets
curl -O "http://localhost:8000/api/v1/exports/pricing-results/excel?include_summary=false&include_risk_metrics=false&include_market_data=false"
```

### 3. Complete Report Export

**Endpoint:** `GET /api/v1/exports/complete-report/excel`

**Description:** Generates a comprehensive Excel report combining source data and calculated results.

**Parameters:** None

**Excel Structure:**
- **Sheet 1 - Report Info:** Metadata including generation timestamp and record counts
- **Sheet 2 - Source Loans:** All loan records from `loans` table
- **Sheet 3 - Source Properties:** All property locations from `loan_properties`
- **Sheet 4 - Pricing Results:** Complete pricing calculations from `v_loan_pricing`
- **Sheet 5 - Portfolio Summary:** Aggregated portfolio-level metrics
- **Sheet 6 - Risk Analysis:** Detailed risk metrics for all loans
- **Sheet 7 - Market Data:** Current benchmark rates and credit spreads

**Example Usage:**
```bash
# Generate complete report
curl -O "http://localhost:8000/api/v1/exports/complete-report/excel"
```

### 4. Pricing Engine Output Export

**Endpoint:** `GET /api/v1/exports/pricing-engine-output/excel`

**Description:** Exports the JSONB pricing engine output in Excel format.

**Parameters:**
- `format` (string, optional): Output format - "nested" or "flat" (default: "nested")
  - **nested:** Preserves some JSON structure for readability
  - **flat:** Completely flattens all fields into columns

**Excel Structure:**
- Single sheet with pricing engine output data
- Column structure depends on format parameter

**Example Usage:**
```bash
# Export with nested structure
curl -O "http://localhost:8000/api/v1/exports/pricing-engine-output/excel"

# Export with completely flattened structure
curl -O "http://localhost:8000/api/v1/exports/pricing-engine-output/excel?format=flat"
```

## Excel Formatting Features

All exported Excel files include:

### Automatic Formatting
- **Column Width:** Auto-adjusted based on content (max 50 characters)
- **Headers:** Bold text with dark blue background and white font
- **Number Formats:**
  - Rates/Yields/Spreads: Displayed as percentages (e.g., 5.25%)
  - Currency/Balance fields: Comma-separated thousands (e.g., 1,234,567.89)
  - Dates: YYYY-MM-DD format

### Data Type Handling
- PostgreSQL `Decimal` types converted to Excel numbers
- PostgreSQL `Date`/`DateTime` types preserved as Excel dates
- NULL values displayed as empty cells
- JSONB data properly flattened or structured based on endpoint

## Implementation Details

### Technology Stack
- **pandas:** DataFrame manipulation and Excel writing
- **openpyxl:** Excel file formatting and styling
- **FastAPI StreamingResponse:** Efficient file delivery

### File Naming Convention
All exported files follow the pattern: `{export_type}_{YYYYMMDD}.xlsx`

Examples:
- `loans_export_20240115.xlsx`
- `pricing_results_20240115.xlsx`
- `rpx_complete_report_20240115.xlsx`

### Performance Considerations
- Large datasets are processed in memory
- Streaming response ensures efficient delivery
- No temporary files created on server

## Error Handling

The export endpoints handle common errors:
- Missing database views return appropriate error messages
- Failed queries logged with detailed error information
- Malformed data gracefully handled with fallback values

## Usage Examples

### Python Client
```python
import requests

# Download loans export
response = requests.get("http://localhost:8000/api/v1/exports/loans/excel")
with open("loans.xlsx", "wb") as f:
    f.write(response.content)
```

### JavaScript/TypeScript
```javascript
// Download complete report
fetch('http://localhost:8000/api/v1/exports/complete-report/excel')
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'rpx_complete_report.xlsx';
    a.click();
  });
```

### Command Line
```bash
# Using curl with custom filename
curl -o "my_report_$(date +%Y%m%d).xlsx" \
  "http://localhost:8000/api/v1/exports/complete-report/excel"

# Using wget
wget -O "pricing_export.xlsx" \
  "http://localhost:8000/api/v1/exports/pricing-results/excel"
```

## Best Practices

1. **Large Datasets:** Use pagination parameters (`skip`, `limit`) for loans export when dealing with large portfolios
2. **Selective Exports:** Use boolean parameters to exclude unnecessary sheets and reduce file size
3. **Regular Exports:** Schedule automated exports using cron jobs or task schedulers
4. **Data Validation:** Always verify critical calculations after export

## Troubleshooting

### Common Issues

1. **Empty Sheets**
   - Cause: Database view doesn't exist or returns no data
   - Solution: Verify view exists with `\dv` in psql

2. **Decimal Conversion Errors**
   - Cause: Non-numeric values in numeric columns
   - Solution: Data is automatically converted to safe values

3. **Large File Sizes**
   - Cause: Including all sheets with large datasets
   - Solution: Use parameters to exclude unnecessary sheets

### Debug Information

Enable debug logging to see detailed export information:
```python
import logging
logging.getLogger("app.api.endpoints.exports").setLevel(logging.DEBUG)
```

## Future Enhancements

Potential improvements for the export functionality:
- CSV export option for simpler data transfer
- Filtered exports based on loan criteria
- Scheduled export jobs with email delivery
- Custom template support for branded reports
- Export format configuration (fonts, colors, logos)