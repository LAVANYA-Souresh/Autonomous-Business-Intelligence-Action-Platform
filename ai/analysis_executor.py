from decimal import Decimal
from typing import Any

from ai.nl_to_sql_service import NLToSQLService


class AnalysisExecutionError(Exception):
    """Raised when an analytical plan cannot be executed."""
    pass


class AnalysisExecutor:
    """
    Executes structured analytical plans using trusted
    database evidence.

    The executor does not generate SQL itself.
    It delegates SQL generation and validation to
    NLToSQLService.
    """

    def __init__(self, sql_service: NLToSQLService):
        self.sql_service = sql_service

    def execute(
        self,
        question: str,
        analysis_plan: dict[str, Any]
    ) -> dict[str, Any]:

        if not question or not question.strip():
            raise AnalysisExecutionError(
                "Business question is empty."
            )

        if not analysis_plan:
            raise AnalysisExecutionError(
                "Analysis plan is empty."
            )

        analysis_type = analysis_plan.get(
            "analysis_type"
        )

        if analysis_type == "trend":
            return self._execute_trend(
                question=question,
                analysis_plan=analysis_plan
            )

        if analysis_type == "comparison":
            return self._execute_comparison(
                question=question,
                analysis_plan=analysis_plan
            )

        if analysis_type == "diagnostic":
            return self._execute_diagnostic(
                question=question,
                analysis_plan=analysis_plan
            )

        raise AnalysisExecutionError(
            f"Unsupported analysis type: {analysis_type}"
        )

    def _execute_trend(
        self,
        question: str,
        analysis_plan: dict[str, Any]
    ) -> dict[str, Any]:

        time_periods = analysis_plan.get(
            "time_periods",
            []
        )

        if len(time_periods) < 2:
            raise AnalysisExecutionError(
                "Trend analysis requires at least two time periods."
            )

        evidence = []

        for period in time_periods:

            period_question = (
                f"What was the total revenue in {period}?"
            )

            print(
                f"\nExecuting trend evidence query "
                f"for {period}..."
            )

            sql_result = self.sql_service.ask(
                period_question
            )

            evidence.append({
                "period": period,
                "question": period_question,
                "sql": sql_result["sql"],
                "results": sql_result["results"],
                "attempts": sql_result["attempts"]
            })

        return {
            "status": "EXECUTED",
            "analysis_type": "trend",
            "question": question,
            "analysis_plan": analysis_plan,
            "evidence": evidence
        }

    def _execute_comparison(
        self,
        question: str,
        analysis_plan: dict[str, Any]
    ) -> dict[str, Any]:

        raise AnalysisExecutionError(
            "Comparison execution has not been implemented yet."
        )

    def _execute_diagnostic(
        self,
        question: str,
        analysis_plan: dict[str, Any]
    ) -> dict[str, Any]:

        raise AnalysisExecutionError(
            "Diagnostic execution has not been implemented yet."
        )


if __name__ == "__main__":

    from ai.llm_client import OllamaLLMClient

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    sql_service = NLToSQLService(
        llm_client=llm_client
    )

    executor = AnalysisExecutor(
        sql_service=sql_service
    )

    question = (
        "How did revenue change between "
        "April and May 2025?"
    )

    analysis_plan = {
        "analysis_type": "trend",
        "primary_metric": "revenue",
        "dimensions": ["month"],
        "time_periods": [
            "April 2025",
            "May 2025"
        ],
        "requires_multiple_queries": False
    }

    try:

        result = executor.execute(
            question=question,
            analysis_plan=analysis_plan
        )

        print("\n========================================")
        print("TREND EXECUTION RESULT")
        print("========================================")

        print(
            f"\nStatus: {result['status']}"
        )

        print(
            f"\nAnalysis type: "
            f"{result['analysis_type']}"
        )

        print("\nEvidence:")

        for item in result["evidence"]:

            print(
                f"\nPeriod: {item['period']}"
            )

            print(
                f"SQL: {item['sql']}"
            )

            print(
                f"Results: {item['results']}"
            )

            print(
                f"Attempts: {item['attempts']}"
            )

    except AnalysisExecutionError as error:

        print(
            "\nTREND EXECUTION FAILED:"
        )

        print(error)