from ai.business_pipeline import BusinessPipeline


def main():

    pipeline = BusinessPipeline()

    question = (
        "Which region generated the most revenue in May 2025?"
    )

    result = pipeline.ask(question)

    print("\n========== FINAL RESULT ==========\n")

    print("Status:")
    print(result["status"])

    print("\nAnswer:")
    print(result["answer"])

    print("\nSQL:")
    print(result["sql"])

    print("\nDatabase Results:")
    print(result["results"])


if __name__ == "__main__":
    main()