from ai.llm_client import OllamaLLMClient
from ai.nl_to_sql_service import NLToSQLService


def main():

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    sql_service = NLToSQLService(
        llm_client=llm_client
    )

    question = (
        "What was the return rate in May 2025?"
    )

    print(
        "\n========== RETURN RATE TEST ==========\n"
    )

    result = sql_service.ask(
        question
    )

    print(
        "\n========== RESULT ==========\n"
    )

    print("SQL:")
    print(result["sql"])

    print("\nResults:")
    print(result["results"])

    print("\nAttempts:")
    print(result["attempts"])


if __name__ == "__main__":
    main()