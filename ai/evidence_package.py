
from typing import Any


class EvidencePackageError(Exception):
    """Raised when an evidence package cannot be created."""
    pass


class EvidencePackageBuilder:
    """
    Builds a structured, auditable evidence package
    from the results of the business orchestration pipeline.

    The package preserves:
        - business question
        - analysis plan
        - workflow
        - SQL evidence
        - RAG reasoning
        - numerical verification
        - final status

    This component does not generate or modify evidence.
    It only organizes existing trusted evidence.
    """

    def build(
        self,
        question: str,
        analysis_plan: dict[str, Any],
        workflow: str,
        result: dict[str, Any],
        sql_evidence: str,
        reasoning_answer: str,
        numerical_verification: dict[str, Any],
        status: str
    ) -> dict[str, Any]:

        if not question or not question.strip():
            raise EvidencePackageError(
                "Business question is required."
            )

        if not analysis_plan:
            raise EvidencePackageError(
                "Analysis plan is required."
            )

        if not workflow:
            raise EvidencePackageError(
                "Workflow is required."
            )

        if not result:
            raise EvidencePackageError(
                "Execution result is required."
            )

        if not sql_evidence or not sql_evidence.strip():
            raise EvidencePackageError(
                "SQL evidence is required."
            )

        if not reasoning_answer or not reasoning_answer.strip():
            raise EvidencePackageError(
                "Reasoning answer is required."
            )

        if not numerical_verification:
            raise EvidencePackageError(
                "Numerical verification result is required."
            )

        return {
            "question": question,
            "analysis": {
                "workflow": workflow,
                "plan": analysis_plan
            },
            "database_evidence": {
                "execution_result": result,
                "formatted_sql_evidence": sql_evidence
            },
            "reasoning": {
                "answer": reasoning_answer
            },
            "verification": {
                "numerical": numerical_verification
            },
            "final_status": status
        }


if __name__ == "__main__":

    print(
        "\n========== EVIDENCE PACKAGE TEST ==========\n"
    )

    builder = EvidencePackageBuilder()

    test_package = builder.build(
        question=(
            "Which region generated the most "
            "revenue in May 2025?"
        ),

        analysis_plan={
            "analysis_type": "simple_factual",
            "primary_metric": "revenue",
            "dimensions": ["region"],
            "time_periods": ["May 2025"],
            "requires_multiple_queries": False
        },

        workflow="simple_factual",

        result={
            "status": "EXECUTED",
            "analysis_type": "simple_factual",
            "sql": (
                "SELECT o.region, "
                "SUM(o.total_amount) AS revenue "
                "FROM aibusinessanalytics.orders o "
                "WHERE o.order_date >= '2025-05-01' "
                "AND o.order_date < '2025-06-01' "
                "GROUP BY o.region "
                "ORDER BY revenue DESC "
                "LIMIT 1"
            ),
            "results": [
                {
                    "region": "Puducherry",
                    "revenue": 30057941.0
                }
            ],
            "attempts": 2
        },

        sql_evidence=(
            "REGION: Puducherry\n"
            "REVENUE: 30057941.0"
        ),

        reasoning_answer=(
            "Puducherry generated the highest revenue "
            "in May 2025."
        ),

        numerical_verification={
            "status": "PASSED",
            "checked": True,
            "mismatches": []
        },

        status="VERIFIED"
    )

    print(
        "\nEvidence package created successfully.\n"
    )

    print(test_package)

