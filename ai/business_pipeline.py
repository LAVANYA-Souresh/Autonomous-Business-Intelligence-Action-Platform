from typing import Any

from ai.llm_client import OllamaLLMClient
from ai.nl_to_sql_service import NLToSQLService
from ai.sql_evidence import SQLEvidenceFormatter
from ai.analysis_planner import AnalysisPlanner
from ai.analysis_executor import AnalysisExecutor
from ai.trend_analyzer import TrendAnalyzer
from ai.diagnostic_executor import DiagnosticExecutor
from ai.orchestrator import BusinessOrchestrator
from rag.reasoning import BusinessReasoningEngine


class BusinessPipeline:

    def __init__(self):

        print("\nInitializing Business AI Pipeline...")

        self.llm_client = OllamaLLMClient(
            model="qwen2.5:1.5b"
        )

        self.sql_service = NLToSQLService(
            llm_client=self.llm_client
        )

        self.evidence_formatter = SQLEvidenceFormatter()

        self.analysis_planner = AnalysisPlanner(
            llm_client=self.llm_client
        )

        self.analysis_executor = AnalysisExecutor(
            sql_service=self.sql_service
        )

        self.trend_analyzer = TrendAnalyzer()

        self.diagnostic_executor = DiagnosticExecutor(
            sql_service=self.sql_service
        )
       
        self.reasoning_engine = BusinessReasoningEngine(llm_client=self.llm_client)

        self.orchestrator = BusinessOrchestrator(
            analysis_planner=self.analysis_planner,
            analysis_executor=self.analysis_executor,
            diagnostic_executor=self.diagnostic_executor,
            reasoning_engine=self.reasoning_engine,
        )

    def ask(self, question: str) -> dict[str, Any]:
        if not question or not question.strip():
            raise ValueError("Business question cannot be empty.")

        orchestration_result = self.orchestrator.run(question)

        workflow = orchestration_result["workflow"]
        analysis_plan = orchestration_result["analysis_plan"]
        result = orchestration_result["result"]

        if workflow == "simple_factual":
            answer = self._build_deterministic_answer(
               question,
               result
        )

        elif workflow == "trend":
            answer = self._build_trend_answer(
               question,
               analysis_plan,
               result
        )

        elif workflow == "diagnostic":
            diagnostic_result = self._analyze_diagnostic_evidence(
              result
        )

            answer = self._build_diagnostic_answer(
              diagnostic_result
        )

            return {
                "status": "VERIFIED",
                "question": question,
                "analysis_plan": analysis_plan,
                "workflow": workflow,
                "answer": answer,
                "diagnostic_analysis": diagnostic_result,
                "evidence": result["evidence"]
        }

        else:
            raise ValueError(
            f"Unsupported workflow: {workflow}"
        )

        return {
            "status": "VERIFIED",
            "question": question,
            "analysis_plan": analysis_plan,
            "workflow": workflow,
            "answer": answer,
            "result": result
    }
    # =============================================================
    # SIMPLE FACTUAL
    # =============================================================

    def _run_simple_factual(
        self,
        question: str,
        analysis_plan: dict[str, Any]
    ):

        sql_result = self.sql_service.ask(question)

        sql_evidence = self.evidence_formatter.format(
            sql_result
        )

        answer = self._build_deterministic_answer(
            question=question,
            sql_result=sql_result
        )

        return {
            "status": "VERIFIED",
            "question": question,
            "analysis_plan": analysis_plan,
            "answer": answer,
            "sql": sql_result["sql"],
            "results": sql_result["results"],
            "attempts": sql_result["attempts"],
            "evidence": sql_evidence,
        }

    # =============================================================
    # TREND
    # =============================================================

    def _run_trend_analysis(
        self,
        question: str,
        analysis_plan: dict[str, Any]
    ):

        trend_execution = self.analysis_executor.execute(
            question=question,
            analysis_plan=analysis_plan
        )

        trend_result = self.trend_analyzer.analyze(
            trend_execution
        )

        answer = self._build_trend_answer(
            trend_result
        )

        return {
            "status": "VERIFIED",
            "question": question,
            "analysis_plan": analysis_plan,
            "answer": answer,
            "trend_analysis": trend_result,
            "evidence": trend_execution["evidence"]
        }

    # =============================================================
    # DIAGNOSTIC
    # =============================================================

    def _run_diagnostic_analysis(
        self,
        question: str,
        analysis_plan: dict[str, Any]
    ):

        diagnostic_execution = (
            self.diagnostic_executor.execute(
                question=question,
                analysis_plan=analysis_plan
            )
        )

        diagnostic_result = (
            self._analyze_diagnostic_evidence(
                diagnostic_execution
            )
        )

        answer = self._build_diagnostic_answer(
            diagnostic_result
        )

        return {
            "status": "VERIFIED",
            "question": question,
            "analysis_plan": analysis_plan,
            "answer": answer,
            "diagnostic_analysis": diagnostic_result,
            "evidence": diagnostic_execution["evidence"]
        }

    # =============================================================
    # DIAGNOSTIC ANALYSIS
    # =============================================================

    def _analyze_diagnostic_evidence(
        self,
        diagnostic_execution: dict[str, Any]
    ):

        evidence = diagnostic_execution["evidence"]

        previous_period = (
            diagnostic_execution["previous_period"]
        )

        primary_period = (
            diagnostic_execution["primary_period"]
        )

        evidence_map = {
            item["evidence_type"]: item
            for item in evidence
        }

        # ---------------------------------------------------------
        # Revenue change
        # ---------------------------------------------------------

        previous_revenue = self._extract_value(
            evidence_map["previous_period_revenue"]
        )

        current_revenue = self._extract_value(
            evidence_map["current_period_revenue"]
        )

        revenue_change = (
            current_revenue - previous_revenue
        )

        if previous_revenue != 0:

            revenue_change_percent = (
                revenue_change
                / previous_revenue
                * 100
            )

        else:
            revenue_change_percent = 0

        # ---------------------------------------------------------
        # Regional changes
        # ---------------------------------------------------------

        previous_regions = self._rows_by_key(
            evidence_map["previous_regional_revenue"],
            "region"
        )

        current_regions = self._rows_by_key(
            evidence_map["current_regional_revenue"],
            "region"
        )

        regional_changes = []

        for region in set(
            previous_regions
        ).union(current_regions):

            previous_value = float(
                previous_regions.get(region, 0)
            )

            current_value = float(
                current_regions.get(region, 0)
            )

            change = current_value - previous_value

            regional_changes.append({
                "region": region,
                "previous_revenue": previous_value,
                "current_revenue": current_value,
                "change": change
            })

        regional_changes.sort(
            key=lambda item: item["change"],
            reverse=True
        )

        # ---------------------------------------------------------
        # Product changes
        # ---------------------------------------------------------

        previous_products = self._rows_by_key(
            evidence_map["previous_product_revenue"],
            "product_name"
        )

        current_products = self._rows_by_key(
            evidence_map["current_product_revenue"],
            "product_name"
        )

        product_changes = []

        for product in set(
            previous_products
        ).union(current_products):

            previous_value = float(
                previous_products.get(product, 0)
            )

            current_value = float(
                current_products.get(product, 0)
            )

            change = current_value - previous_value

            product_changes.append({
                "product_name": product,
                "previous_revenue": previous_value,
                "current_revenue": current_value,
                "change": change
            })

        product_changes.sort(
            key=lambda item: item["change"],
            reverse=True
        )

        # ---------------------------------------------------------
        # Return rate
        # ---------------------------------------------------------

        return_rate = self._extract_named_value(
            evidence_map["return_rate"],
            "return_rate"
        )

        return {
            "previous_period": previous_period,
            "current_period": primary_period,
            "previous_revenue": previous_revenue,
            "current_revenue": current_revenue,
            "revenue_change": revenue_change,
            "revenue_change_percent": revenue_change_percent,
            "regional_changes": regional_changes,
            "product_changes": product_changes,
            "current_return_rate": return_rate
        }

    # =============================================================
    # DIAGNOSTIC ANSWER
    # =============================================================

    def _build_diagnostic_answer(
        self,
        diagnostic_result: dict[str, Any]
    ):

        previous_period = diagnostic_result[
            "previous_period"
        ]

        current_period = diagnostic_result[
            "current_period"
        ]

        previous_revenue = diagnostic_result[
            "previous_revenue"
        ]

        current_revenue = diagnostic_result[
            "current_revenue"
        ]

        revenue_change = diagnostic_result[
            "revenue_change"
        ]

        revenue_change_percent = diagnostic_result[
            "revenue_change_percent"
        ]

        regional_changes = diagnostic_result[
            "regional_changes"
        ]

        product_changes = diagnostic_result[
            "product_changes"
        ]

        return_rate = diagnostic_result[
            "current_return_rate"
        ]

        direction = (
            "increased"
            if revenue_change > 0
            else "decreased"
            if revenue_change < 0
            else "remained unchanged"
        )

        answer = (
            f"Revenue {direction} from "
            f"₹{previous_revenue:,.0f} in {previous_period} "
            f"to ₹{current_revenue:,.0f} in {current_period}, "
            f"a change of ₹{abs(revenue_change):,.0f} "
            f"({abs(revenue_change_percent):.2f}%)."
        )

        if regional_changes:

            strongest_region = regional_changes[0]

            answer += (
                f" The largest positive regional change "
                f"was in {strongest_region['region']}, "
                f"which changed by "
                f"₹{strongest_region['change']:,.0f}."
            )

        if product_changes:

            strongest_product = product_changes[0]

            answer += (
                f" The largest positive product-level "
                f"change was for "
                f"{strongest_product['product_name']}, "
                f"which changed by "
                f"₹{strongest_product['change']:,.0f}."
            )

        answer += (
            f" The return rate in {current_period} "
            f"was {return_rate:.2f}%."
        )

        answer += (
            " These are observed revenue patterns in the "
            "database and should not be interpreted as proof "
            "of causation."
        )

        return answer

    # =============================================================
    # HELPERS
    # =============================================================

    def _extract_value(
        self,
        evidence_item: dict[str, Any]
    ) -> float:

        results = evidence_item.get("results", [])

        if not results:
            return 0.0

        row = results[0]

        for key in (
            "revenue",
            "total_revenue",
            "sum",
            "total"
        ):

            if key in row:
                return float(row[key])

        raise ValueError(
            "Could not find revenue value in diagnostic evidence."
        )

    def _extract_named_value(
        self,
        evidence_item: dict[str, Any],
        field_name: str
    ) -> float:

        results = evidence_item.get("results", [])

        if not results:
            return 0.0

        row = results[0]

        if field_name not in row:
            raise ValueError(
                f"Expected field '{field_name}' "
                "was not found in diagnostic evidence."
            )

        return float(row[field_name])

    def _rows_by_key(
        self,
        evidence_item: dict[str, Any],
        key_field: str
    ) -> dict[str, float]:

        rows = evidence_item.get("results", [])

        result = {}

        for row in rows:

            key = row.get(key_field)

            if key is None:
                continue

            value = row.get("revenue", 0)

            result[str(key)] = float(value)

        return result

    # =============================================================
    # SIMPLE ANSWER
    # =============================================================

    def _build_deterministic_answer(
        self,
        question: str,
        sql_result: dict[str, Any]
    ):

        results = sql_result["results"]

        if not results:
            return "The database returned no results."

        first_row = results[0]

        if (
            "region" in first_row
            and "revenue" in first_row
        ):

            region = first_row["region"]
            revenue = first_row["revenue"]

            formatted_revenue = (
                f"{float(revenue):,.0f}"
            )

            return (
                f"The region that generated the most "
                f"revenue in May 2025 is {region} "
                f"with revenue of ₹{formatted_revenue}."
            )

        if (
            "product_name" in first_row
            and "revenue" in first_row
        ):

            product = first_row["product_name"]
            revenue = first_row["revenue"]

            formatted_revenue = (
                f"{float(revenue):,.0f}"
            )

            return (
                f"{product} generated the highest "
                f"revenue in May 2025, with revenue "
                f"of ₹{formatted_revenue}."
            )

        if len(first_row) == 1:

            field = next(iter(first_row))
            value = first_row[field]
            try:
                formatted_value = f"{float(value):,.2f}"
                return f"The result is ₹{formatted_value}."
            except (TypeError, ValueError):
                return f"The result is {value}."

        parts = []

        for field, value in first_row.items():
            parts.append(
                f"{field}: {value}"
            )

        return (
            "The database returned: "
            + ", ".join(parts)
        )

    # =============================================================
    # TREND ANSWER
    # =============================================================

    def _build_trend_answer(
        self,
        trend_result: dict[str, Any]
    ):

        previous = float(
            trend_result["previous_value"]
        )

        current = float(
            trend_result["current_value"]
        )

        change = float(
            trend_result["change"]
        )

        percentage = float(
            trend_result["percentage_change"]
        )

        direction = (
            "increased"
            if change > 0
            else "decreased"
            if change < 0
            else "remained unchanged"
        )

        return (
            f"Revenue {direction} from "
            f"₹{previous:,.0f} to "
            f"₹{current:,.0f}, "
            f"a change of ₹{abs(change):,.0f} "
            f"({abs(percentage):.2f}%)."
        )



if __name__ == "__main__":
    pipeline = BusinessPipeline()

    result = pipeline.ask(
        "Why did revenue change between April and May 2025?"
    )

    print("\n========== FINAL RESULT ==========\n")
    print(result)