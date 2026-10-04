from decimal import Decimal
from typing import Any


class TrendAnalysisError(Exception):
    """Raised when trend evidence cannot be analyzed."""
    pass


class TrendAnalyzer:
    """
    Performs deterministic trend calculations from trusted
    database evidence.

    This component does not use an LLM.

    The database provides the trusted values.
    Python performs the calculations.
    """

    def analyze(
        self,
        trend_execution: dict[str, Any]
    ) -> dict[str, Any]:

        if not trend_execution:
            raise TrendAnalysisError(
                "Trend execution result is empty."
            )

        if trend_execution.get("status") != "EXECUTED":
            raise TrendAnalysisError(
                "Trend evidence was not successfully executed."
            )

        evidence = trend_execution.get(
            "evidence",
            []
        )

        if len(evidence) < 2:
            raise TrendAnalysisError(
                "Trend analysis requires at least two periods."
            )

        values = {}

        for item in evidence:

            period = item.get("period")

            results = item.get(
                "results",
                []
            )

            if not period:
                raise TrendAnalysisError(
                    "Trend evidence is missing a period."
                )

            if not results:
                raise TrendAnalysisError(
                    f"No database result found for {period}."
                )

            row = results[0]

            if "total_revenue" not in row:
                raise TrendAnalysisError(
                    f"Revenue value missing for {period}."
                )

            revenue = row["total_revenue"]

            if not isinstance(
                revenue,
                (int, float, Decimal)
            ):
                raise TrendAnalysisError(
                    f"Invalid revenue value for {period}: "
                    f"{revenue}"
                )

            values[period] = Decimal(
                str(revenue)
            )

        periods = list(values.keys())

        if len(periods) != 2:
            raise TrendAnalysisError(
                "This trend analyzer currently supports "
                "exactly two periods."
            )

        first_period = periods[0]
        second_period = periods[1]

        first_value = values[first_period]
        second_value = values[second_period]

        absolute_change = (
            second_value - first_value
        )

        if first_value == 0:
            percentage_change = None
        else:
            percentage_change = (
                absolute_change
                / first_value
            ) * Decimal("100")

        if absolute_change > 0:
            direction = "increased"

        elif absolute_change < 0:
            direction = "decreased"

        else:
            direction = "remained unchanged"

        return {
            "status": "ANALYZED",
            "analysis_type": "trend",
            "question": trend_execution["question"],
            "first_period": first_period,
            "second_period": second_period,
            "first_value": first_value,
            "second_value": second_value,
            "absolute_change": absolute_change,
            "percentage_change": percentage_change,
            "direction": direction
        }


if __name__ == "__main__":

    analyzer = TrendAnalyzer()

    test_execution = {
        "status": "EXECUTED",
        "analysis_type": "trend",
        "question": (
            "How did revenue change between "
            "April and May 2025?"
        ),
        "evidence": [
            {
                "period": "April 2025",
                "results": [
                    {
                        "total_revenue":
                            Decimal("118630583.00")
                    }
                ]
            },
            {
                "period": "May 2025",
                "results": [
                    {
                        "total_revenue":
                            Decimal("133018981.00")
                    }
                ]
            }
        ]
    }

    try:

        result = analyzer.analyze(
            test_execution
        )

        print(
            "\n========================================"
        )
        print(
            "TREND ANALYSIS RESULT"
        )
        print(
            "========================================"
        )

        print(
            f"\nFirst period: "
            f"{result['first_period']}"
        )

        print(
            f"First value: "
            f"{result['first_value']}"
        )

        print(
            f"\nSecond period: "
            f"{result['second_period']}"
        )

        print(
            f"Second value: "
            f"{result['second_value']}"
        )

        print(
            f"\nDirection: "
            f"{result['direction']}"
        )

        print(
            f"Absolute change: "
            f"{result['absolute_change']}"
        )

        if result["percentage_change"] is not None:

            print(
                f"Percentage change: "
                f"{result['percentage_change']:.2f}%"
            )

        else:

            print(
                "Percentage change: "
                "Not available because the first "
                "period value is zero."
            )

    except TrendAnalysisError as error:

        print(
            "\nTREND ANALYSIS FAILED:"
        )

        print(error)