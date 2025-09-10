"""
Pricing data transformation utilities for restructuring flat database results
into the expected nested output format.
"""
from typing import Dict, List, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Default values for missing fields
DEFAULT_STRING = "555555"
DEFAULT_NUMBER = 555555
DEFAULT_DECIMAL = Decimal("555555")
DEFAULT_DATE = "555555"


class PricingTransformer:
    """Transform flat database pricing data into nested structure matching expected schema."""

    @staticmethod
    def transform_loan_record(flat_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a flat loan record into the expected nested structure."""

        # Helper function to get value with default
        def get_value(key: str, default: Any = None) -> Any:
            value = flat_record.get(key)
            if value is None:
                return default
            return value

        # Helper to format date values
        def format_date(date_value: Any) -> Optional[str]:
            if date_value is None:
                return None
            if isinstance(date_value, (date, datetime)):
                return date_value.strftime("%d.%m.%y")
            return str(date_value)

        # Helper to normalize percentage values. Values coming
        # from the database may be stored as decimals (0-1) but the
        # pricing schemas expect percentages on a 0-100 scale. This
        # function converts decimals to percentage values while
        # leaving already-percentage numbers untouched.
        def format_percentage(value: Any) -> float:
            try:
                numeric_value = float(value)
                return numeric_value * 100 if numeric_value < 1 else numeric_value
            except (TypeError, ValueError):
                return 0.0

        # Transform the record
        transformed = {
            # Core identification
            "loan_id": get_value("loan_id", DEFAULT_NUMBER),
            "pricing_scenario": get_value("pricing_scenario", "RPX Pricing"),
            "maturity_assumption": get_value("maturity_assumption", "Maturity"),
            "credit_spread": float(get_value("credit_spread", DEFAULT_NUMBER)),
            "market_yield": float(get_value("market_yield", DEFAULT_NUMBER)),
            "loss_scenario": get_value("loss_scenario", "N"),

            # Risk metrics group
            "risk_metrics": {
                "pd": float(get_value("risk_pd", get_value("pd", 0.0))),
                "ead": float(get_value("risk_ead", get_value("ead", 100.0))),
                "lgd": float(get_value("risk_lgd", get_value("lgd", 100.0))),
                "lag_to_recovery": get_value("lag_to_recovery", 0),
                "default_date": format_date(get_value("default_date")) or DEFAULT_DATE,
                "cdr": get_value("cdr", "0%")
            },

            # Loan identification group
            "loan_identification": {
                "client_loan_number": get_value("client_loan_number", DEFAULT_STRING),
                "loan_name": get_value("loan_name", DEFAULT_STRING)
            },

            # Property details group
            "property_details": {
                "sector": get_value("property_sector", get_value("sector", DEFAULT_STRING)),
                "property_type": get_value("property_type", DEFAULT_STRING),
                "property_lifecycle_financing": get_value("property_lifecycle_financing", "Permanent")
            },

            # Borrower group
            "borrower": {
                "sponsor_borrower": get_value("sponsor_borrower", DEFAULT_STRING)
            },

            # Loan amounts group
            "loan_amounts": {
                "original_balance": float(get_value("original_balance", DEFAULT_NUMBER)),
                "current_balance": float(get_value("current_balance", DEFAULT_NUMBER)),
                "currency": get_value("currency", "USD"),
                "client_percentage": float(get_value("client_percentage", 100.0)),
                "pik_balance": get_value("pik_balance", " -   ")
            },

            # Loan structure group
            "loan_structure": {
                "position_in_capital_stack": get_value("position_in_capital_stack", "Senior Loan"),
                "periodicity": get_value("periodicity", "Monthly"),
                "interest_day_count": get_value("interest_day_count", "30/360"),
                "loan_status": get_value("loan_status", "Performing"),
                "commentary": get_value("commentary", "Current"),
                "coupon_description": PricingTransformer._build_coupon_description(flat_record),
                "contract_type": get_value("contract_type", "Fixed"),
                "interest_type": get_value("interest_type", "Accrued Interest")
            },

            # Valuation results group
            "valuation_results": {
                "fair_value_plus_accrued": float(get_value("fair_value_plus_accrued",
                                                           get_value("fair_value", DEFAULT_NUMBER))),
                "accrued_interest": float(
                    get_value("loan_accrued_interest", get_value("accrued_interest", DEFAULT_NUMBER))),
                "fair_value": float(get_value("fair_value", DEFAULT_NUMBER)),
                "price_including_accrued": format_percentage(
                    get_value("price_including_accrued", get_value("price", DEFAULT_NUMBER))
                ),
                "price": format_percentage(get_value("price", DEFAULT_NUMBER)),
                "benchmark_yield": float(get_value("benchmark_yield", DEFAULT_NUMBER)),
                "benchmark": get_value("benchmark_type", "US Treasury"),
                "wal_years": float(get_value("wal_wal_years", get_value("wal_years", DEFAULT_NUMBER))),
                "modified_duration_years": float(get_value("modified_duration_years", DEFAULT_NUMBER)),
                "convexity": float(get_value("convexity", DEFAULT_NUMBER)),
                "maturity": format_date(get_value("maturity_date",
                                                  get_value("original_maturity_date"))) or DEFAULT_DATE
            },

            # Fair value ranges group
            "fair_value_ranges": {
                "lower_price": format_percentage(get_value("lower_price", DEFAULT_NUMBER)),
                "upper_price": format_percentage(get_value("upper_price", DEFAULT_NUMBER)),
                "lower_fv": float(get_value("lower_fv", DEFAULT_NUMBER)),
                "upper_fv": float(get_value("upper_fv", DEFAULT_NUMBER)),
                "lower_mey": float(get_value("lower_mey", DEFAULT_NUMBER)),
                "upper_mey": float(get_value("upper_mey", DEFAULT_NUMBER))
            },

            # Dates group
            "dates": {
                "loan_origination_date": format_date(get_value("origination_date",
                                                               get_value("loan_origination_date"))) or DEFAULT_DATE,
                "original_maturity_date": format_date(get_value("original_maturity_date",
                                                                get_value("maturity_date"))) or DEFAULT_DATE,
                "extension_1st": format_date(get_value("extension_1st_date",
                                                       get_value("extension_1st"))),
                "extension_2nd": format_date(get_value("extension_2nd_date",
                                                       get_value("extension_2nd"))),
                "extension_3rd": format_date(get_value("extension_3rd_date",
                                                       get_value("extension_3rd")))
            },

            # Default scenario
            "default_scenario": get_value("default_scenario", "N"),
            "component_yield": float(get_value("component_yield", DEFAULT_NUMBER)),

            # Price changes group
            "price_changes": {
                "delta_price": float(get_value("delta_price", 0.0)),
                "delta_price_yield_cbe": float(get_value("delta_price_yield_cbe", 0.0)),
                "delta_price_credit_spread": float(get_value("delta_price_credit_spread", 0.0)),
                "delta_price_benchmark": float(get_value("delta_price_benchmark", 0.0)),
                "delta_price_yield_curve_shift": float(get_value("delta_price_yield_curve_shift", 0.0)),
                "delta_price_yield_curve_roll": float(get_value("delta_price_yield_curve_roll", 0.0)),
                "delta_price_accretion": float(get_value("delta_price_accretion", 0.0))
            },

            # Yield changes group
            "yield_changes": {
                "delta_credit_spread": float(get_value("delta_credit_spread", 0.0)),
                "delta_benchmark_yield": float(get_value("delta_benchmark_yield", 0.0)),
                "delta_cbe_yield": float(get_value("delta_cbe_yield", 0.0)),
                "yield_curve_shift": float(get_value("yield_curve_shift", 0.0)),
                "yield_curve_roll": float(get_value("yield_curve_roll", 0.0))
            },

            # Prior scenario group
            "prior_scenario": {
                "scenario": get_value("prior_scenario", "Maturity"),
                "credit_spread": float(get_value("credit_spread_prior", get_value("credit_spread", DEFAULT_NUMBER))),
                "market_yield": float(get_value("market_yield_prior", get_value("market_yield", DEFAULT_NUMBER))),
                "maturity_scenario": get_value("maturity_scenario_prior", "Maturity"),
                "amortization_type": get_value("amortization_type", "Amortizing"),
                "property_location": get_value("property_location", "City, ST"),
                "dscr": get_value("dscr_prior", get_value("dscr_current")),
                "ltv": get_value("ltv_prior", get_value("ltv_current")),
                "current_balance_prior": float(get_value("current_balance_prior",
                                                         get_value("current_balance", DEFAULT_NUMBER))),
                "price_prior": format_percentage(get_value("price_prior", get_value("price", DEFAULT_NUMBER))),
                "benchmark_yield_prior": float(get_value("benchmark_yield_prior", 0)),
                "credit_spread_prior": float(get_value("credit_spread_prior",
                                                       get_value("credit_spread", DEFAULT_NUMBER))),
                "market_yield_prior": float(get_value("market_yield_prior",
                                                      get_value("market_yield", DEFAULT_NUMBER))),
                "dscr_prior": get_value("dscr_prior"),
                "ltv_prior": get_value("ltv_prior"),
                "wal_prior": float(get_value("wal_prior", get_value("wal_years", DEFAULT_NUMBER))),
                "duration_prior": float(get_value("duration_prior",
                                                  get_value("modified_duration_years", DEFAULT_NUMBER))),
                "loan_status_prior": get_value("loan_status_prior", get_value("loan_status", "Performing"))
            }
        }

        # Add all the cash flow and other fields with defaults
        cash_flow_fields = [
            "new_loan_indicator", "period_number", "accrual_dates_projected", "dates_adjust_mid_period",
            "accrual_dates_actual", "day_count", "active_index_curve", "prior_index_curve",
            "floating_rate_index", "index_margin", "bank_loan_coupon_step_up", "contract_rate",
            "prepayment_penalty_type", "call_timing", "maturity_adjusted_extensions",
            "prepayment_lockout_date", "io_period", "ancillary_fees_trigger",
            "forbearance_grace_period_counter", "forbearance_payback_period_counter",
            "default_timing", "credit_facility_funded_balance", "credit_facility_draws_projected",
            "credit_facility_unfunded_balance", "original_balance_total_commitment",
            "current_balance_with_accrued", "defaults", "performing_balance", "prepayments",
            "forbearance_account_beginning_balance", "interest_due_grace_period",
            "principal_due_grace_period", "forbearance_interest_paid", "forbearance_principal_paid",
            "forbearance_account_ending_balance", "pi_contractual_payment", "forbearance_adjusted_pi",
            "scheduled_interest_forbearance", "prepayment_penalties_yield_maintenance_term",
            "discount_factor", "prepayment_penalties_yield_maintenance_pv",
            "prepayment_penalties_yield_maintenance_amount", "ancillary_fees_extension_exit",
            "scheduled_principal_forbearance", "principal", "cash_flows", "aggregate_defaults",
            "pmt", "scheduled_interest", "scheduled_principal", "advanced_interest_paid",
            "advanced_principal_paid", "default_offset", "recovery", "non_performing_cash",
            "unfunded_commitment_fee", "prepayment_penalties", "additional_fees_extension_exit",
            "pik_interest", "default_interest", "total_interest", "principal_balloon",
            "equity_kicker", "total_cfs", "dates", "credit_facility_funded_balance_2",
            "credit_facility_draws", "credit_facility_unfunded_balance_2",
            "original_balance_total_commitment_2", "current_balance_with_accrued_2",
            "interest", "unfunded_commitment_fee_2", "additional_fees_extension_exit_2",
            "pik_interest_2", "default_interest_2", "principal_2", "equity_kicker_2",
            "cash_flow", "dr", "df", "dr_prior", "df_prior", "periods_from_settlement",
            "convexity_calculation", "lower_range_mey", "upper_range_mey", "lower_range_df",
            "upper_range_df", "dates_unindexed", "p_or_pi", "dates_indexed", "p_or_pi_indexed",
            "pi_indexed", "custom_dates_schedule_unindexed", "custom_dates_schedule_indexed",
            "eg", "default_interest_3", "dates_unindexed_2", "step_up_coupon_unindexed",
            "dates_indexed_2", "step_up_coupon_used", "dates_unindexed_3", "step_up_margin_unindexed",
            "dates_indexed_3", "step_up_margin_active", "dates_unindexed_4", "utilization_rate",
            "dates_indexed_4", "active_utilization_rate", "eg_2", "dates_unindexed_5",
            "interest_type_2", "dates_indexed_5", "interest_type_3", "eg_3"
        ]

        # Add all cash flow fields with None as default
        for field in cash_flow_fields:
            if field != "dates":  # Skip dates as it's already defined above
                transformed[field] = None

        # Add portfolio summary
        transformed["portfolio_summary"] = {
            "balance_current": float(get_value("current_balance", DEFAULT_NUMBER)),
            "ltv_current": get_value("ltv_current"),
            "ltv_prior": float(get_value("ltv_prior", 0.0)),
            "dscr_current": get_value("dscr_current"),
            "dscr_prior": get_value("dscr_prior"),
            "benchmark_yield": float(get_value("benchmark_yield", DEFAULT_NUMBER)),
            "sector": get_value("property_sector", get_value("sector", DEFAULT_STRING)),
            "fixed_float": get_value("contract_type", "Fixed"),
            "prior_balance": float(get_value("current_balance_prior",
                                             get_value("current_balance", DEFAULT_NUMBER))),
            "prior_benchmark_yield": float(get_value("benchmark_yield_prior",
                                                     get_value("benchmark_yield", DEFAULT_NUMBER))),
            "prior_wal": float(get_value("wal_prior", get_value("wal_years", DEFAULT_NUMBER))),
            "prior_duration": float(get_value("duration_prior",
                                              get_value("modified_duration_years", DEFAULT_NUMBER))),
            "prior_loan_status": get_value("loan_status_prior", get_value("loan_status", "Performing"))
        }

        # Add final fields
        transformed["new_loan_indicator_2"] = None
        transformed["sector_allocation_summary"] = DEFAULT_STRING

        return transformed

    @staticmethod
    def _build_coupon_description(record: Dict[str, Any]) -> str:
        """Build coupon description from available fields."""
        contract_type = record.get("contract_type", "Fixed")
        if contract_type.lower() == "fixed":
            rate = record.get("fixed_rate_coupon", 5.75)
            if rate and rate != DEFAULT_NUMBER:
                return f"Fixed @{rate}%"
            else:
                return "Fixed @5.75%"
        else:
            index = record.get("floating_rate_index", "SOFR1M")
            margin = record.get("floating_rate_margin", 1.82)
            if index and margin and margin != DEFAULT_NUMBER:
                return f"{index} + {margin}%"
            else:
                return "SOFR1M + 1.82%"

    @staticmethod
    def calculate_portfolio_analysis(loans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate portfolio-level analysis from loan data."""
        if not loans:
            return {
                "total_fair_value": 0.0,
                "average_price": 0.0,
                "average_yield": 0.0,
                "average_duration": 0.0,
                "sector_allocation": {},
                "risk_distribution": {"performing": 0, "default": 0},
                "interest_type_distribution": {"fixed": 0, "floating": 0},
                "credit_spread_ranges": {"low": 0.0, "high": 0.0, "average": 0.0}
            }

        # Calculate aggregates
        total_fair_value = sum(loan.get("valuation_results", {}).get("fair_value", 0) for loan in loans)
        total_balance = sum(loan.get("loan_amounts", {}).get("current_balance", 0) for loan in loans)

        # Calculate averages
        prices = [loan.get("valuation_results", {}).get("price", 0) for loan in loans if
                  loan.get("valuation_results", {}).get("price", 0) > 0]
        yields = [loan.get("market_yield", 0) for loan in loans if loan.get("market_yield", 0) > 0]
        durations = [loan.get("valuation_results", {}).get("modified_duration_years", 0) for loan in loans if
                     loan.get("valuation_results", {}).get("modified_duration_years", 0) > 0]

        # Sector allocation
        sector_allocation = {}
        for loan in loans:
            sector = loan.get("property_details", {}).get("sector", "Unknown")
            balance = loan.get("loan_amounts", {}).get("current_balance", 0)
            if total_balance > 0:
                pct = (balance / total_balance) * 100
                sector_allocation[sector] = sector_allocation.get(sector, 0) + pct

        # Risk distribution
        performing_count = sum(
            1 for loan in loans if loan.get("loan_structure", {}).get("loan_status", "").lower() != "default")
        default_count = len(loans) - performing_count

        # Interest type distribution
        fixed_count = sum(
            1 for loan in loans if loan.get("loan_structure", {}).get("contract_type", "").lower() == "fixed")
        floating_count = len(loans) - fixed_count

        # Credit spread ranges
        spreads = [loan.get("credit_spread", 0) for loan in loans if loan.get("credit_spread", 0) > 0]

        return {
            "total_fair_value": round(total_fair_value / 1000000, 1),  # In millions
            "average_price": round(sum(prices) / len(prices), 1) if prices else 0.0,
            "average_yield": round(sum(yields) / len(yields), 1) if yields else 0.0,
            "average_duration": round(sum(durations) / len(durations), 1) if durations else 0.0,
            "sector_allocation": {k: round(v, 1) for k, v in sector_allocation.items()},
            "risk_distribution": {
                "performing": round((performing_count / len(loans)) * 100, 0) if loans else 0,
                "default": round((default_count / len(loans)) * 100, 0) if loans else 0
            },
            "interest_type_distribution": {
                "fixed": round((fixed_count / len(loans)) * 100, 0) if loans else 0,
                "floating": round((floating_count / len(loans)) * 100, 0) if loans else 0
            },
            "credit_spread_ranges": {
                "low": round(min(spreads), 2) if spreads else 0.0,
                "high": round(max(spreads), 2) if spreads else 0.0,
                "average": round(sum(spreads) / len(spreads), 2) if spreads else 0.0
            }
        }

    @staticmethod
    def build_pricing_engine_metrics(total_loans: int) -> Dict[str, Any]:
        """Build pricing engine metrics."""
        return {
            "total_loans_analyzed": total_loans,
            "scenarios_run": total_loans * 2,  # Assuming 2 scenarios per loan
            "valuation_method": "Discounted Cash Flow",
            "benchmark_curve": "US Treasury",
            "risk_free_rate": 4.56,
            "market_risk_premium": 2.5,
            "liquidity_adjustment": 0.5
        }