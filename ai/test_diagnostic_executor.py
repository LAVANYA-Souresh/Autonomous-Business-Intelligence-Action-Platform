from ai.llm_client import OllamaLLMClient
from ai.nl_to_sql_service import NLToSQLService
from ai.diagnostic_executor import DiagnosticExecutor


def main():

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    sql_service = NLToSQLService(
        llm_client=llm_client
    )

    executor = DiagnosticExecutor(
        sql_service=sql_service
    )

    analysis_plan = {
        "analysis_type": "diagnostic",
        "primary_metric": "revenue",
        "dimensions": [
            "region",
            "product"
        ],
        "time_periods": [
            "May 2025"
        ],
        "requires_multiple_queries": True
    }

    question = (
        "Why did revenue change in May 2025?"
    )

    result = executor.execute(
        question=question,
        analysis_plan=analysis_plan
    )

    print(
        "\n========== DIAGNOSTIC EXECUTION RESULT ==========\n"
    )

    print(
        "Status:",
        result["status"]
    )

    print(
        "Primary period:",
        result["primary_period"]
    )

    print(
        "Previous period:",
        result["previous_period"]
    )

    print(
        "\nEvidence collected:",
        len(result["evidence"])
    )

    for index, item in enumerate(
        result["evidence"],
        start=1
    ):

        print(
            f"\n--- Evidence {index} ---"
        )

        print(
            "Type:",
            item["evidence_type"]
        )

        print(
            "Period:",
            item["period"]
        )

        print(
            "SQL:",
            item["sql"]
        )

        print(
            "Results:",
            item["results"]
        )

        print(
            "Attempts:",
            item["attempts"]
        )


if __name__ == "__main__":
    main()