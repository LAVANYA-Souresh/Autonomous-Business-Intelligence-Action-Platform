import re


class SchemaValidationError(Exception):
    """Raised when SQL references an invalid table or column."""
    pass


class SchemaValidator:
    """
    Validates SQL references against the known NovaMart schema.

    This validator checks:
    - referenced tables
    - table aliases
    - qualified columns
    - common unqualified columns
    """

    SCHEMA = {
        "customers": {
            "customer_id",
            "name",
            "email",
            "region",
            "signup_date",
        },
        "products": {
            "product_id",
            "product_name",
            "category",
            "price",
        },
        "orders": {
            "order_id",
            "customer_id",
            "order_date",
            "total_amount",
            "region",
        },
        "order_items": {
            "order_item_id",
            "order_id",
            "product_id",
            "quantity",
            "price",
        },
        "returns": {
            "return_id",
            "order_id",
            "product_id",
            "return_date",
            "reason",
        },
        "support_tickets": {
            "ticket_id",
            "customer_id",
            "product_id",
            "created_at",
            "category",
            "status",
        },
    }

    REQUIRED_SCHEMA = "aibusinessanalytics"

    SQL_KEYWORDS = {
        "SELECT",
        "FROM",
        "WHERE",
        "AND",
        "OR",
        "NOT",
        "NULL",
        "IS",
        "IN",
        "AS",
        "ON",
        "JOIN",
        "LEFT",
        "RIGHT",
        "INNER",
        "OUTER",
        "FULL",
        "CROSS",
        "GROUP",
        "BY",
        "ORDER",
        "ASC",
        "DESC",
        "HAVING",
        "LIMIT",
        "OFFSET",
        "DISTINCT",
        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",
        "WITH",
        "UNION",
        "ALL",
        "DATE",
        "DATE_PART",
        "EXTRACT",
        "SUM",
        "COUNT",
        "AVG",
        "MIN",
        "MAX",
        "COALESCE",
        "ROUND",
        "TRUE",
        "FALSE",
        "FROM",
        "LIKE",
        "ILIKE",
        "BETWEEN",
        "INTERVAL",
        "CAST",
        "FILTER",
        "OVER",
        "PARTITION",
        "WINDOW",
    }

    SQL_FUNCTIONS = {
        "SUM",
        "COUNT",
        "AVG",
        "MIN",
        "MAX",
        "ROUND",
        "COALESCE",
        "DATE",
        "DATE_PART",
        "EXTRACT",
    }

    def validate(self, sql: str):
        """
        Validate table and column references.

        Raises SchemaValidationError if an invalid reference is found.
        """

        if not sql or not sql.strip():
            raise SchemaValidationError(
                "SQL query is empty."
            )

        sql = sql.strip()

        tables, aliases = self._extract_tables_and_aliases(sql)

        if not tables:
            raise SchemaValidationError(
                "No known tables found in SQL query."
            )

        for table in tables:

            if table not in self.SCHEMA:
                raise SchemaValidationError(
                    f"Unknown table referenced: {table}"
                )

        self._check_schema_qualification(sql)

        self._validate_qualified_columns(
            sql,
            aliases
        )

        self._validate_unqualified_columns(
            sql,
            tables
        )

        return True

    def _extract_tables_and_aliases(self, sql: str):

        tables = set()
        aliases = {}

        # Remove EXTRACT(...) expressions temporarily.
        #
        # Otherwise:
        #
        # EXTRACT(MONTH FROM order_date)
        #
        # could incorrectly make the validator think
        # "order_date" is a table after FROM.

        sql_for_table_detection = re.sub(
            r"\bEXTRACT\s*\([^)]*\)",
            "",
            sql,
            flags=re.IGNORECASE
        )

        pattern = (
            r"\b(?:FROM|JOIN)\s+"
            r"(?:aibusinessanalytics\.)?"
            r"([A-Za-z_][A-Za-z0-9_]*)"
            r"(?:\s+(?:AS\s+)?"
            r"([A-Za-z_][A-Za-z0-9_]*))?"
        )

        matches = re.findall(
            pattern,
            sql_for_table_detection,
            flags=re.IGNORECASE
        )

        for table, alias in matches:

            table = table.lower()

            tables.add(table)

            if alias:

                alias = alias.lower()

                if alias.upper() not in self.SQL_KEYWORDS:
                    aliases[alias] = table

        return tables, aliases

    def _validate_qualified_columns(
        self,
        sql: str,
        aliases: dict
    ):
        """
        Validate references such as:

        orders.total_amount
        o.total_amount
        p.product_name
        """

        references = re.findall(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\."
            r"([A-Za-z_][A-Za-z0-9_]*)\b",
            sql,
        )

        for table_or_alias, column in references:

            table_or_alias = table_or_alias.lower()
            column = column.lower()

            # Ignore schema qualification.
            if table_or_alias == "aibusinessanalytics":
                continue

            # Resolve alias.
            if table_or_alias in aliases:

                table = aliases[table_or_alias]

            elif table_or_alias in self.SCHEMA:

                table = table_or_alias

            else:

                raise SchemaValidationError(
                    f"Unknown table or alias: "
                    f"{table_or_alias}"
                )

            if column not in self.SCHEMA[table]:

                raise SchemaValidationError(
                    f"Unknown column '{column}' "
                    f"in table '{table}'."
                )

    def _validate_unqualified_columns(
        self,
        sql: str,
        tables: set
    ):
        """
        Validate obvious unqualified column references.

        Example:

        SELECT total_amount
        FROM aibusinessanalytics.orders

        total_amount must exist in orders.
        """

        # With multiple tables, an unqualified column may belong
        # to more than one table.
        #
        # Leave those cases for PostgreSQL to resolve after
        # qualified references have been checked.

        if len(tables) != 1:
            return

        table = next(iter(tables))

        # Remove qualified references such as:
        #
        # o.total_amount
        #
        sql_without_qualified = re.sub(
            r"\b[A-Za-z_][A-Za-z0-9_]*\."
            r"[A-Za-z_][A-Za-z0-9_]*\b",
            "",
            sql
        )

        # Extract identifier-like words.
        identifiers = re.findall(
            r"\b[A-Za-z_][A-Za-z0-9_]*\b",
            sql_without_qualified
        )

        # Collect aliases created with AS.
        select_aliases = set(
            alias.lower()
            for alias in re.findall(
                r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)\b",
                sql,
                flags=re.IGNORECASE
            )
        )

        for identifier in identifiers:

            identifier_lower = identifier.lower()

            # SQL keywords.
            if identifier.upper() in self.SQL_KEYWORDS:
                continue

            # SQL functions.
            if identifier.upper() in self.SQL_FUNCTIONS:
                continue

            # Schema name.
            if identifier_lower == "aibusinessanalytics":
                continue

            # Table name.
            if identifier_lower == table:
                continue

            # Common SQL aliases.
            if identifier_lower in {
                "o",
                "p",
                "c",
                "oi",
                "r",
                "st",
            }:
                continue

            # SELECT aliases.
            if identifier_lower in select_aliases:
                continue

            # Numeric values.
            if identifier.isdigit():
                continue

            # Known column?
            if identifier_lower not in self.SCHEMA[table]:

                raise SchemaValidationError(
                    f"Unknown column '{identifier_lower}' "
                    f"in table '{table}'."
                )


    def _check_schema_qualification(self, sql: str):
        """
        Ensure every physical table reference uses
        the required PostgreSQL schema.
        """

        pattern = (
           r"\b(?:FROM|JOIN)\s+"
           r"(?!(?:aibusinessanalytics)\.)"
           r"([A-Za-z_][A-Za-z0-9_]*)"
           r"(?:\s+(?:AS\s+)?[A-Za-z_][A-Za-z0-9_]*)?"
        )

        matches = re.findall(
            pattern,
            sql,
            flags=re.IGNORECASE
        )

        for table in matches:

             table_lower = table.lower()

             if table_lower in self.SCHEMA:

                raise SchemaValidationError(
                f"Table '{table_lower}' must be schema-qualified as "
                f"'{self.REQUIRED_SCHEMA}.{table_lower}'."
              )


if __name__ == "__main__":

    print("\n========== SCHEMA VALIDATOR TEST ==========\n")

    validator = SchemaValidator()

    test_queries = [

        # Test 1 — should pass
        """
        SELECT SUM(total_amount)
        FROM aibusinessanalytics.orders
        """,

        # Test 2 — should pass
        """
        SELECT
            o.order_id,
            o.total_amount
        FROM aibusinessanalytics.orders AS o
        """,

        # Test 3 — should pass
        """
        SELECT
            p.product_name,
            p.price
        FROM aibusinessanalytics.products AS p
        """,

        # Test 4 — should fail
        """
        SELECT customer_salary
        FROM aibusinessanalytics.customers
        """,

        # Test 5 — should fail
        """
        SELECT *
        FROM aibusinessanalytics.orderss
        """,

        # Test 6 — should fail
        """
        SELECT o.fake_column
        FROM aibusinessanalytics.orders AS o
        """,

        # Test 7 — should pass
        """
        SELECT
            order_date,
            total_amount
        FROM aibusinessanalytics.orders
        WHERE total_amount > 1000
        """,

        # Test 8 — should fail
        """
        SELECT nonexistent_column
        FROM aibusinessanalytics.products
        """,

        # Test 9 — EXTRACT should pass
        """
        SELECT COUNT(order_id)
        FROM aibusinessanalytics.orders
        WHERE EXTRACT(MONTH FROM order_date) = 5
        AND EXTRACT(YEAR FROM order_date) = 2025
        """,

        # Should FAIL — schema missing
"""
SELECT COUNT(order_id)
FROM orders
WHERE order_date >= '2025-05-01'
  AND order_date < '2025-06-01'
""",

# Should PASS — schema included
"""
SELECT COUNT(order_id)
FROM aibusinessanalytics.orders
WHERE order_date >= '2025-05-01'
  AND order_date < '2025-06-01'
""",
    ]

    for index, query in enumerate(
        test_queries,
        start=1
    ):

        print(f"Test {index}:")
        print(query.strip())

        try:

            validator.validate(query)

            print("Status: PASSED")

        except SchemaValidationError as error:

            print("Status: REJECTED")
            print(f"Reason: {error}")

        print()