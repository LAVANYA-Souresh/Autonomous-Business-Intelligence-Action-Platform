from sqlalchemy import text

from analytics.db import engine
from ai.sql_validator import SQLValidator
from ai.schema_validator import SchemaValidator


class SQLExecutionError(Exception):
    """Raised when SQL cannot be safely executed."""
    pass


class SQLExecutor:
    """
    Safely executes validated read-only SQL against PostgreSQL.
    """

    def __init__(self):
        self.sql_validator = SQLValidator()
        self.schema_validator = SchemaValidator()

    def execute(self, sql: str):
        """
        Validate and execute a read-only SQL query.

        Returns:
            list[dict]: Query results as dictionaries.
        """

        try:
            # Step 1: Safety validation
            cleaned_sql = self.sql_validator.validate(sql)

            # Step 2: Schema validation
            self.schema_validator.validate(cleaned_sql)

            # Step 3: Execute only after validation passes
            with engine.connect() as connection:

                result = connection.execute(
                    text(cleaned_sql)
                )

                rows = result.mappings().all()

            return [dict(row) for row in rows]

        except Exception as error:
            raise SQLExecutionError(
                f"SQL execution failed: {error}"
            ) from error


if __name__ == "__main__":

    print("\n========== SQL EXECUTOR TEST ==========\n")

    executor = SQLExecutor()

    test_sql = """
    SELECT
        COUNT(*) AS order_count,
        SUM(total_amount) AS total_revenue
    FROM aibusinessanalytics.orders
    """

    print("SQL:")
    print(test_sql)

    try:

        results = executor.execute(test_sql)

        print("\nExecution successful.")
        print("\nResults:")

        for row in results:
            print(row)

    except SQLExecutionError as error:

        print("\nExecution rejected.")
        print(f"Reason: {error}")