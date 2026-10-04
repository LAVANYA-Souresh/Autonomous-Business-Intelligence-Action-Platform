from decimal import Decimal


class SQLEvidenceFormatter:
    """
    Converts validated NL-to-SQL results into
    structured evidence suitable for the reasoning layer.
    """

    def format(self, sql_result):

        question = sql_result["question"]
        sql = sql_result["sql"]
        results = sql_result["results"]
        attempts = sql_result["attempts"]

        lines = []

        lines.append("DATABASE QUERY EVIDENCE")

        lines.append(
            f"Question: {question}"
        )

        lines.append("")

        lines.append(
            "SQL VALIDATION"
        )

        lines.append(
            "Safety validation: PASSED"
        )

        lines.append(
            "Schema validation: PASSED"
        )

        lines.append(
            "Business semantic validation: PASSED"
        )

        lines.append(
            "PostgreSQL execution: PASSED"
        )

        lines.append(
            f"Generation attempts: {attempts}"
        )

        lines.append("")

        lines.append(
            "EXECUTED SQL"
        )

        lines.append(sql)

        lines.append("")

        lines.append(
            "QUERY RESULTS"
        )

        if not results:

            lines.append(
                "No rows were returned."
            )

        else:

            for index, row in enumerate(
                results,
                start=1
            ):

                lines.append(
                    f"Row {index}:"
                )

                for key, value in row.items():

                    if isinstance(
                        value,
                        Decimal
                    ):
                        value = float(value)

                    lines.append(
                        f"  {key}: {value}"
                    )

        return "\n".join(lines)


if __name__ == "__main__":

    print(
        "\n========== SQL EVIDENCE FORMATTER TEST ==========\n"
    )

    formatter = SQLEvidenceFormatter()

    sample_result = {
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

    evidence = formatter.format(
        sample_result
    )

    print(evidence)