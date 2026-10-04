import re
import json


class SQLValidationError(Exception):
    """Raised when generated SQL fails safety validation."""
    pass


class SQLValidator:
    """
    Validates AI-generated SQL before it can be executed.

    The validator allows only read-only SELECT queries.
    """

    FORBIDDEN_KEYWORDS = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE",
        "MERGE",
    ]

    def validate(self, sql: str) -> str:
        """
        Validate SQL and return the cleaned query.

        Raises SQLValidationError if the query is unsafe.
        """

        if not sql or not sql.strip():
            raise SQLValidationError(
                "SQL query is empty."
            )

        cleaned_sql = self._clean_sql(sql)

        self._check_single_statement(cleaned_sql)
        self._check_select_only(cleaned_sql)
        self._check_forbidden_keywords(cleaned_sql)

        return cleaned_sql

    def _clean_sql(self, sql: str) -> str:

        sql = sql.strip()

        # ---------------------------------------------------------
        # Remove Markdown code fences
        # ---------------------------------------------------------

        sql = re.sub(
            r"^```(?:sql|json)?\s*",
            "",
            sql,
            flags=re.IGNORECASE
        )

        sql = re.sub(
            r"\s*```$",
            "",
            sql
        )

        sql = sql.strip()

        # ---------------------------------------------------------
        # Handle JSON responses from the LLM
        # ---------------------------------------------------------

        if sql.startswith("{") and sql.endswith("}"):

            try:

                parsed = json.loads(sql)

                for key in [
                    "query",
                    "sql_query",
                    "sqlQuery",
                    "sql"
                ]:

                    if key in parsed:

                        sql = parsed[key]

                        if not isinstance(sql, str):
                            raise SQLValidationError(
                                "SQL value inside JSON response "
                                "must be a string."
                            )

                        break

            except json.JSONDecodeError:

                # Small local models sometimes return malformed
                # JSON containing multiline SQL.
                #
                # Attempt to recover the SQL from fields such as:
                #
                # "query": "SELECT ..."
                #
                # "sql": "SELECT ..."

                match = re.search(
                    r'"(?:query|sql_query|sqlQuery|sql)"'
                    r'\s*:\s*"?(SELECT\b.*)',
                    sql,
                    flags=re.IGNORECASE | re.DOTALL
                )

                if match:

                    sql = match.group(1)

                    # Remove JSON closing characters.
                    sql = re.sub(
                        r'"\s*}\s*$',
                        "",
                        sql,
                        flags=re.DOTALL
                    )

                    sql = sql.strip()

        sql = sql.strip()

        # ---------------------------------------------------------
        # Remove one trailing semicolon
        # ---------------------------------------------------------

        if sql.endswith(";"):
            sql = sql[:-1].strip()

        return sql

    def _check_single_statement(self, sql: str):
        """
        Allow only one SQL statement.
        """

        statements = [
            statement.strip()
            for statement in sql.split(";")
            if statement.strip()
        ]

        if len(statements) > 1:
            raise SQLValidationError(
                "Multiple SQL statements are not allowed."
            )

    def _check_select_only(self, sql: str):
        """
        The query must begin with SELECT or WITH.
        """

        normalized = sql.strip().upper()

        if not (
            normalized.startswith("SELECT ")
            or normalized.startswith("SELECT\n")
            or normalized.startswith("WITH ")
            or normalized.startswith("WITH\n")
        ):
            raise SQLValidationError(
                "Only SELECT or WITH queries are allowed."
            )

    def _check_forbidden_keywords(self, sql: str):
        """
        Reject dangerous SQL keywords.
        """

        normalized = sql.upper()

        for keyword in self.FORBIDDEN_KEYWORDS:

            pattern = rf"\b{keyword}\b"

            if re.search(pattern, normalized):

                raise SQLValidationError(
                    f"Forbidden SQL keyword detected: {keyword}"
                )


if __name__ == "__main__":

    print(
        "\n========== SQL VALIDATOR TEST ==========\n"
    )

    validator = SQLValidator()

    test_queries = [

        # ---------------------------------------------------------
        # Should pass
        # ---------------------------------------------------------

        """
        SELECT SUM(total_amount)
        FROM aibusinessanalytics.orders
        """,

        # ---------------------------------------------------------
        # Should pass
        # ---------------------------------------------------------

        """
        SELECT *
        FROM aibusinessanalytics.products
        """,

        # ---------------------------------------------------------
        # Should pass
        # ---------------------------------------------------------

        """
        WITH revenue AS (
            SELECT SUM(total_amount) AS total
            FROM aibusinessanalytics.orders
        )
        SELECT total
        FROM revenue
        """,

        # ---------------------------------------------------------
        # Should fail
        # ---------------------------------------------------------

        """
        DELETE FROM aibusinessanalytics.orders
        """,

        # ---------------------------------------------------------
        # Should fail
        # ---------------------------------------------------------

        """
        DROP TABLE aibusinessanalytics.orders
        """,

        # ---------------------------------------------------------
        # Should fail
        # ---------------------------------------------------------

        """
        UPDATE aibusinessanalytics.products
        SET price = 0
        """,

        # ---------------------------------------------------------
        # Should fail
        # ---------------------------------------------------------

        """
        SELECT 1;
        DELETE FROM aibusinessanalytics.orders;
        """,

        # ---------------------------------------------------------
        # Should fail
        # ---------------------------------------------------------

        """
        Hello, this is not SQL.
        """,

        # ---------------------------------------------------------
        # JSON response using "query"
        # ---------------------------------------------------------

        """
        {
            "query": "SELECT COUNT(*) FROM aibusinessanalytics.orders;"
        }
        """,

        # ---------------------------------------------------------
        # JSON response using "sql_query"
        # ---------------------------------------------------------

        """
        {
            "sql_query": "SELECT COUNT(*) FROM aibusinessanalytics.orders;"
        }
        """,
    ]

    for index, query in enumerate(
        test_queries,
        start=1
    ):

        print(f"Test {index}:")
        print(query.strip())

        try:

            cleaned_sql = validator.validate(
                query
            )

            print("Status: PASSED")
            print(
                f"Cleaned SQL: {cleaned_sql}"
            )

        except SQLValidationError as error:

            print("Status: REJECTED")
            print(
                f"Reason: {error}"
            )

        print()