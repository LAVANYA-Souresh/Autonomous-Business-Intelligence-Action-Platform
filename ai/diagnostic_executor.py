from typing import Any

from ai.nl_to_sql_service import NLToSQLService
from ai.sql_executor import SQLExecutor


class DiagnosticExecutionError(Exception):
    """Raised when diagnostic evidence cannot be collected."""
    pass


class DiagnosticExecutor:
    """
    Collects trusted database evidence required for
    diagnostic business questions.

    The planner/LLM decides what should be investigated.
    Deterministic SQL collects the trusted evidence.
    This component does not claim causality.
    """

    def __init__(self, sql_service: NLToSQLService):
        self.sql_service = sql_service
        self.sql_executor = SQLExecutor()

    def execute(
        self,
        question: str,
        analysis_plan: dict[str, Any]
    ) -> dict[str, Any]:

        if not question or not question.strip():
            raise DiagnosticExecutionError(
                "Business question is empty."
            )

        if not analysis_plan:
            raise DiagnosticExecutionError(
                "Analysis plan is empty."
            )

        if analysis_plan.get("analysis_type") != "diagnostic":
            raise DiagnosticExecutionError(
                "DiagnosticExecutor requires a diagnostic analysis plan."
            )

        time_periods = analysis_plan.get("time_periods", [])

        if len(time_periods) < 2:
            raise DiagnosticExecutionError(
                "Diagnostic analysis requires at least two time periods."
            )

        previous_period = time_periods[0]
        primary_period = time_periods[-1]

        previous_start, previous_end = self._month_range(
            previous_period
        )

        current_start, current_end = self._month_range(
            primary_period
        )

        print(
            f"\nCollecting diagnostic evidence "
            f"for {previous_period} -> {primary_period}..."
        )

        evidence = []

        # =========================================================
        # 1. Current-period revenue
        # =========================================================

        current_sql = f"""
            SELECT
                COALESCE(SUM(o.total_amount), 0) AS revenue
            FROM aibusinessanalytics.orders o
            WHERE o.order_date >= '{current_start}'
              AND o.order_date < '{current_end}'
        """

        current_revenue = self._execute_sql(
            label="Current-period revenue",
            sql=current_sql
        )

        evidence.append({
            "evidence_type": "current_period_revenue",
            "period": primary_period,
            "sql": current_sql.strip(),
            "results": current_revenue,
            "attempts": 1
        })

        # =========================================================
        # 2. Previous-period revenue
        # =========================================================

        previous_sql = f"""
            SELECT
                COALESCE(SUM(o.total_amount), 0) AS revenue
            FROM aibusinessanalytics.orders o
            WHERE o.order_date >= '{previous_start}'
              AND o.order_date < '{previous_end}'
        """

        previous_revenue = self._execute_sql(
            label="Previous-period revenue",
            sql=previous_sql
        )

        evidence.append({
            "evidence_type": "previous_period_revenue",
            "period": previous_period,
            "sql": previous_sql.strip(),
            "results": previous_revenue,
            "attempts": 1
        })

        # =========================================================
        # 3. Current regional revenue
        # =========================================================

        current_region_sql = f"""
            SELECT
                o.region,
                COALESCE(SUM(o.total_amount), 0) AS revenue
            FROM aibusinessanalytics.orders o
            WHERE o.order_date >= '{current_start}'
              AND o.order_date < '{current_end}'
            GROUP BY o.region
            ORDER BY revenue DESC
        """

        current_regions = self._execute_sql(
            label="Current regional revenue",
            sql=current_region_sql
        )

        evidence.append({
            "evidence_type": "current_regional_revenue",
            "period": primary_period,
            "sql": current_region_sql.strip(),
            "results": current_regions,
            "attempts": 1
        })

        # =========================================================
        # 4. Previous regional revenue
        # =========================================================

        previous_region_sql = f"""
            SELECT
                o.region,
                COALESCE(SUM(o.total_amount), 0) AS revenue
            FROM aibusinessanalytics.orders o
            WHERE o.order_date >= '{previous_start}'
              AND o.order_date < '{previous_end}'
            GROUP BY o.region
            ORDER BY revenue DESC
        """

        previous_regions = self._execute_sql(
            label="Previous regional revenue",
            sql=previous_region_sql
        )

        evidence.append({
            "evidence_type": "previous_regional_revenue",
            "period": previous_period,
            "sql": previous_region_sql.strip(),
            "results": previous_regions,
            "attempts": 1
        })

        # =========================================================
        # 5. Current product revenue
        # =========================================================

        current_product_sql = f"""
            SELECT
                p.product_name,
                COALESCE(
                    SUM(oi.quantity * oi.price),
                    0
                ) AS revenue
            FROM aibusinessanalytics.orders o
            JOIN aibusinessanalytics.order_items oi
                ON o.order_id = oi.order_id
            JOIN aibusinessanalytics.products p
                ON oi.product_id = p.product_id
            WHERE o.order_date >= '{current_start}'
              AND o.order_date < '{current_end}'
            GROUP BY p.product_name
            ORDER BY revenue DESC
        """

        current_products = self._execute_sql(
            label="Current product revenue",
            sql=current_product_sql
        )

        evidence.append({
            "evidence_type": "current_product_revenue",
            "period": primary_period,
            "sql": current_product_sql.strip(),
            "results": current_products,
            "attempts": 1
        })

        # =========================================================
        # 6. Previous product revenue
        # =========================================================

        previous_product_sql = f"""
            SELECT
                p.product_name,
                COALESCE(
                    SUM(oi.quantity * oi.price),
                    0
                ) AS revenue
            FROM aibusinessanalytics.orders o
            JOIN aibusinessanalytics.order_items oi
                ON o.order_id = oi.order_id
            JOIN aibusinessanalytics.products p
                ON oi.product_id = p.product_id
            WHERE o.order_date >= '{previous_start}'
              AND o.order_date < '{previous_end}'
            GROUP BY p.product_name
            ORDER BY revenue DESC
        """

        previous_products = self._execute_sql(
            label="Previous product revenue",
            sql=previous_product_sql
        )

        evidence.append({
            "evidence_type": "previous_product_revenue",
            "period": previous_period,
            "sql": previous_product_sql.strip(),
            "results": previous_products,
            "attempts": 1
        })

        # =========================================================
        # 7. Current return rate
        # =========================================================

        return_rate_sql = f"""
            SELECT
                COALESCE(
                    COUNT(DISTINCT r.order_id)::numeric
                    / NULLIF(
                        COUNT(DISTINCT o.order_id),
                        0
                    )
                    * 100,
                    0
                ) AS return_rate
            FROM aibusinessanalytics.orders o
            LEFT JOIN aibusinessanalytics.returns r
                ON r.order_id = o.order_id
            WHERE o.order_date >= '{current_start}'
              AND o.order_date < '{current_end}'
        """

        return_rate = self._execute_sql(
            label="Current return rate",
            sql=return_rate_sql
        )

        evidence.append({
            "evidence_type": "return_rate",
            "period": primary_period,
            "sql": return_rate_sql.strip(),
            "results": return_rate,
            "attempts": 1
        })

        return {
            "status": "EXECUTED",
            "analysis_type": "diagnostic",
            "question": question,
            "analysis_plan": analysis_plan,
            "primary_period": primary_period,
            "previous_period": previous_period,
            "evidence": evidence
        }

    # =============================================================
    # SQL EXECUTION
    # =============================================================

    def _execute_sql(
        self,
        label: str,
        sql: str
    ) -> list[dict[str, Any]]:

        print(
            f"\nExecuting diagnostic evidence query: {label}"
        )

        try:
            results = self.sql_executor.execute(sql)

        except Exception as error:
            raise DiagnosticExecutionError(
                f"Failed to collect {label}: {error}"
            ) from error

        print("Diagnostic evidence query: PASSED")

        return results

    # =============================================================
    # MONTH RANGE
    # =============================================================

    def _month_range(
        self,
        period: str
    ) -> tuple[str, str]:

        month_names = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        parts = period.strip().lower().split()

        if len(parts) != 2:
            raise DiagnosticExecutionError(
                f"Invalid time period: {period}"
            )

        month_name = parts[0]
        year_text = parts[1]

        if month_name not in month_names:
            raise DiagnosticExecutionError(
                f"Unknown month: {month_name}"
            )

        try:
            year = int(year_text)
        except ValueError as error:
            raise DiagnosticExecutionError(
                f"Invalid year: {year_text}"
            ) from error

        month = month_names[month_name]

        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        start = f"{year:04d}-{month:02d}-01"
        end = f"{next_year:04d}-{next_month:02d}-01"

        return start, end