from decimal import Decimal

from ai.sql_evidence import SQLEvidenceFormatter
from rag.reasoning import BusinessReasoningEngine


def main():

    print(
        "\n========== REASONING + SQL EVIDENCE TEST ==========\n"
    )

    # --------------------------------------
    # Sample validated NL-to-SQL result
    # --------------------------------------

    sql_result = {
        "question": (
            "Which region generated the most "
            "revenue in May 2025?"
        ),

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
                "revenue": Decimal(
                    "30057941.00"
                )
            }
        ],

        "attempts": 2
    }

    # --------------------------------------
    # Convert SQL result to evidence
    # --------------------------------------

    formatter = SQLEvidenceFormatter()

    sql_evidence = formatter.format(
        sql_result
    )

    print("\nSQL evidence created successfully.")

    # --------------------------------------
    # Initialize reasoning engine
    # --------------------------------------

    engine = BusinessReasoningEngine()

    # --------------------------------------
    # Build reasoning prompt
    # --------------------------------------

    prompt = engine.build_prompt(
        question=sql_result["question"],
        sql_evidence=sql_evidence
    )

    print(
        "\n========== SQL EVIDENCE FOUND IN PROMPT ==========\n"
    )

    if "Puducherry" in prompt:

        print(
            "PASS: SQL evidence is present."
        )

    else:

        print(
            "FAIL: SQL evidence was not found."
        )

    print(
        "\n========== REASONING PROMPT PREVIEW ==========\n"
    )

    print(prompt)


if __name__ == "__main__":
    main()