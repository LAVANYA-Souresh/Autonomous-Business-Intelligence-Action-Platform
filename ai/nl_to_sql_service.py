from ai.llm_client import LLMClient
from ai.nl_to_sql import NLToSQLEngine
from ai.sql_validator import SQLValidator, SQLValidationError
from ai.schema_validator import SchemaValidator, SchemaValidationError
from ai.sql_executor import SQLExecutor, SQLExecutionError
from ai.business_semantic_validator import (
    BusinessSemanticValidator,
    BusinessSemanticValidationError,
)


class NLToSQLService:
    """
    End-to-end natural-language business question service.

    Flow:
        Question
            ↓
        SQL generation
            ↓
        Safety validation
            ↓
        Schema validation
            ↓
        Business semantic validation
            ↓
        If validation fails → LLM correction
            ↓
        PostgreSQL execution
    """

    MAX_ATTEMPTS = 3

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

        self.sql_engine = NLToSQLEngine(
            llm_client=llm_client
        )

        self.sql_validator = SQLValidator()
        self.schema_validator = SchemaValidator()
        self.business_semantic_validator = (
            BusinessSemanticValidator()
        )
        self.sql_executor = SQLExecutor()

    def _generate_sql(
        self,
        question: str,
        correction_error: str = None
    ):
        if correction_error is None:
            return self.sql_engine.generate_sql(question)

        correction_prompt = f"""
You are correcting an SQL query for NovaMart business analytics.

BUSINESS QUESTION:
{question}

VALIDATION ERROR:
{correction_error}

DATABASE SCHEMA:

Schema:
aibusinessanalytics

customers:
- customer_id
- name
- email
- region
- signup_date

products:
- product_id
- product_name
- category
- price

orders:
- order_id
- customer_id
- order_date
- total_amount
- region

order_items:
- order_item_id
- order_id
- product_id
- quantity
- price

returns:
- return_id
- order_id
- product_id
- return_date
- reason

support_tickets:
- ticket_id
- customer_id
- product_id
- created_at
- category
- status

MANDATORY SQL RULES:

MANDATORY SQL RULES:

1. Only generate a SELECT query.

2. Every table must be schema-qualified.

3. Always use the exact schema:
   aibusinessanalytics

4. IDENTIFY THE BUSINESS QUESTION TYPE FIRST.

   A. OVERALL / TOTAL REVENUE

   If the question asks:
   - total revenue
   - overall revenue
   - total sales
   - revenue for a period
   - what was the revenue in a month/period

   then:

   - Use ONLY aibusinessanalytics.orders.
   - Use SUM(o.total_amount).
   - Return exactly ONE aggregate result.
   - Do NOT select o.region.
   - Do NOT GROUP BY.
   - Do NOT ORDER BY.
   - Do NOT use LIMIT.
   - Do NOT join order_items.
   - Do NOT join products.
   - Use o.order_date for the date filter.

   Example:

   SELECT SUM(o.total_amount) AS total_revenue
   FROM aibusinessanalytics.orders o
   WHERE o.order_date >= '2025-05-01'
   AND o.order_date < '2025-06-01'

   B. REGIONAL REVENUE

   If the question asks:
   - revenue by region
   - revenue for each region
   - which region generated the most revenue
   - highest revenue region

   then:

   - Use ONLY aibusinessanalytics.orders.
   - Revenue means SUM(o.total_amount).
   - Use o.region.
   - Use o.order_date for the date filter.
   - Do NOT join order_items.
   - Do NOT join products.

   If asking for EACH region:
   - GROUP BY o.region.
   - ORDER BY revenue DESC.
   - Do NOT use LIMIT 1.

   If asking WHICH SINGLE REGION generated the most revenue:
   - GROUP BY o.region.
   - ORDER BY revenue DESC.
   - LIMIT 1.

       C. PRODUCT REVENUE

    If the question asks:
    - revenue by product
    - revenue for each product
    - which product generated the most revenue
    - which product had the highest revenue

    then:

    REQUIRED TABLES:
    - aibusinessanalytics.orders o
    - aibusinessanalytics.order_items oi
    - aibusinessanalytics.products p

    REQUIRED JOINS:
    - o.order_id = oi.order_id
    - oi.product_id = p.product_id

    REQUIRED REVENUE FORMULA:

    SUM(oi.quantity * oi.price)

    IMPORTANT:
    - quantity belongs to order_items.
    - price belongs to order_items.
    - NEVER use o.quantity.
    - NEVER use p.price.
    - NEVER use SUM(oi.quantity * p.price).
    - NEVER use SUM(o.quantity * oi.price).

    Product name must be:

    p.product_name

    For "which product generated the most revenue":

    SELECT
        p.product_name,
        SUM(oi.quantity * oi.price) AS revenue
    FROM aibusinessanalytics.orders o
    JOIN aibusinessanalytics.order_items oi
        ON o.order_id = oi.order_id
    JOIN aibusinessanalytics.products p
        ON oi.product_id = p.product_id
    WHERE o.order_date >= '2025-05-01'
      AND o.order_date < '2025-06-01'
    GROUP BY p.product_name
    ORDER BY revenue DESC
    LIMIT 1

    For "revenue for each product":

    - GROUP BY p.product_name.
    - ORDER BY revenue DESC.
    - Do NOT use LIMIT 1.

5. For May 2025 use exactly:

   o.order_date >= '2025-05-01'
   AND o.order_date < '2025-06-01'

6. Do not use columns that do not exist.

7. The orders table contains total_amount.
   There is NO column called revenue.

8. If using the orders alias o:
   - use o.region
   - use o.total_amount
   - use o.order_date

9. Do not use BETWEEN for date filtering.

10. Do not join tables unless the business question requires them.

11. Do not invent tables or columns.

12. IMPORTANT:
    Do not change an overall revenue question into a regional
    or product revenue question.

FINAL REQUIREMENT:

Return ONLY a JSON object containing the corrected SQL.

Use exactly this format:

{{
  "query": "SELECT ..."
}}

Do not provide explanations.
Do not provide markdown.
Do not provide multiple queries.


"""

        return self.llm_client.generate(correction_prompt)

    def ask(self, question: str):

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        print(
            "\n========== NL-TO-SQL PIPELINE ==========\n"
        )

        print("User question:")
        print(question)

        last_error = None

        for attempt in range(
            1,
            self.MAX_ATTEMPTS + 1
        ):

            print(
                f"\n========== ATTEMPT "
                f"{attempt}/{self.MAX_ATTEMPTS} ==========\n"
            )

            # STEP 1 — Generate SQL

            print("Generating SQL...\n")

            try:
                generated_sql = self._generate_sql(
                    question,
                    last_error
                )

            except Exception as error:
                raise ValueError(
                    f"SQL generation failed: {error}"
                ) from error

            print("Generated SQL:")
            print(generated_sql)

            # STEP 2 — Safety validation

            print(
                "\nRunning SQL safety validation..."
            )

            try:
                cleaned_sql = (
                    self.sql_validator.validate(
                        generated_sql
                    )
                )
                

            except SQLValidationError as error:

                last_error = (
                    "SQL safety validation failed: "
                    f"{error}"
                )

                print(
                    "Safety validation: FAILED"
                )
                print(f"Reason: {error}")

                if attempt < self.MAX_ATTEMPTS:
                    print(
                        "\nRetrying with correction...\n"
                    )
                    continue

                raise ValueError(
                    last_error
                ) from error

            print(
                "Safety validation: PASSED"
            )

            # STEP 3 — Schema validation

            print(
                "\nRunning schema validation..."
            )

            try:
                self.schema_validator.validate(
                    cleaned_sql
                )

            except SchemaValidationError as error:

                last_error = (
                    "Schema validation failed: "
                    f"{error}"
                )

                print(
                    "Schema validation: FAILED"
                )
                print(f"Reason: {error}")

                if attempt < self.MAX_ATTEMPTS:
                    print(
                        "\nRetrying with correction...\n"
                    )
                    continue

                raise ValueError(
                    last_error
                ) from error

            print(
                "Schema validation: PASSED"
            )

            # STEP 4 — Business semantic validation

            print(
                   "\nRunning business semantic validation..."
                      )

            

            try:
                (
                    self.business_semantic_validator.validate(
                        question,
                        cleaned_sql
                    )
                )

            except BusinessSemanticValidationError as error:

                last_error = (
                    "Business semantic validation failed: "
                    f"{error}"
                )

                print(
                    "Business semantic validation: FAILED"
                )
                print(f"Reason: {error}")

                if attempt < self.MAX_ATTEMPTS:
                    print(
                        "\nRetrying with correction...\n"
                    )
                    continue

                raise ValueError(
                    last_error
                ) from error

            print(
                "Business semantic validation: PASSED"
            )

            # STEP 5 — Execute SQL

            print(
                "\nExecuting SQL against PostgreSQL..."
            )

            try:
                results = self.sql_executor.execute(
                    cleaned_sql
                )

            except SQLExecutionError as error:

                last_error = (
                    "SQL execution failed: "
                    f"{error}"
                )

                print("Execution: FAILED")
                print(f"Reason: {error}")

                if attempt < self.MAX_ATTEMPTS:
                    print(
                        "\nRetrying with correction...\n"
                    )
                    continue

                raise ValueError(
                    last_error
                ) from error

            print("Execution: PASSED")

            return {
                "question": question,
                "sql": cleaned_sql,
                "results": results,
                "attempts": attempt,
            }

        raise ValueError(
            "NL-to-SQL pipeline failed "
            "after maximum attempts."
        )


if __name__ == "__main__":

    print(
        "\n========== NL-TO-SQL SERVICE TEST ==========\n"
    )

    from ai.llm_client import OllamaLLMClient

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    service = NLToSQLService(
        llm_client=llm_client
    )

    question = (
        "Which product generated the most "
        "revenue in May 2025?"
    )

    try:

        response = service.ask(question)

        print(
            "\n========== FINAL RESULT ==========\n"
        )

        print("Question:")
        print(response["question"])

        print("\nSQL:")
        print(response["sql"])

        print("\nAttempts:")
        print(response["attempts"])

        print("\nResults:")

        for row in response["results"]:
            print(row)

    except Exception as error:

        print(
            "\n========== PIPELINE FAILED ==========\n"
        )
        print(error)