import re


class BusinessSemanticValidationError(Exception):
    """Raised when generated SQL does not match the business intent."""
    pass


class BusinessSemanticValidator:
    """
    Validates whether generated SQL matches the business meaning
    of the user's natural-language question.
    """

    def validate(self, question: str, sql: str) -> bool:

        question_lower = question.lower()
        sql_lower = sql.lower()

        self._validate_regional_revenue(
            question_lower,
            sql_lower
        )

        self._validate_overall_revenue(
            question_lower,
            sql_lower
        )

        self._validate_product_revenue(
            question_lower,
            sql_lower
        )

        self._validate_return_rate(
            question_lower,
            sql_lower
        )

        return True

    # ============================================================
    # REGIONAL REVENUE
    # ============================================================

    def _validate_regional_revenue(
        self,
        question: str,
        sql: str
    ):

        regional_terms = [
            "revenue by region",
            "regional revenue",
            "which region generated",
            "which region had the highest revenue",
            "rank regions by revenue",
            "revenue for each region",
            "regional sales",
            "show the revenue for each region",
            "each region",
        ]

        if not any(
            term in question
            for term in regional_terms
        ):
            return

        if "aibusinessanalytics.orders" not in sql:
            raise BusinessSemanticValidationError(
                "Regional revenue must use the orders table."
            )

        if not re.search(
            r"\bo\.region\b",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Regional revenue must use o.region."
            )

        if not re.search(
            r"sum\s*\(\s*o\.total_amount\s*\)",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Regional revenue must use SUM(o.total_amount)."
            )

        if (
            "order_items" in sql
            or "products" in sql
        ):
            raise BusinessSemanticValidationError(
                "Regional revenue must not join "
                "order_items or products."
            )

        if (
            "oi.quantity" in sql
            or "oi.price" in sql
            or "p.price" in sql
        ):
            raise BusinessSemanticValidationError(
                "Product-level revenue logic is not allowed "
                "for regional revenue."
            )

        # --------------------------------------------------------
        # Full regional breakdown
        # --------------------------------------------------------

        full_breakdown_terms = [
            "revenue by region",
            "revenue for each region",
            "show the revenue for each region",
            "rank regions by revenue",
            "ranked from highest to lowest",
            "each region",
        ]

        requires_full_breakdown = any(
            term in question
            for term in full_breakdown_terms
        )

        if requires_full_breakdown:

            if re.search(
                r"\blimit\s+1\b",
                sql
            ):
                raise BusinessSemanticValidationError(
                    "Full regional revenue breakdown must not "
                    "use LIMIT 1."
                )

            if not re.search(
                r"\bgroup\s+by\b",
                sql
            ):
                raise BusinessSemanticValidationError(
                    "Full regional revenue breakdown must "
                    "use GROUP BY."
                )

            if not re.search(
                r"\bo\.region\b",
                sql
            ):
                raise BusinessSemanticValidationError(
                    "Full regional revenue breakdown must "
                    "GROUP BY o.region."
                )

            if not re.search(
                r"\border\s+by\b",
                sql
            ):
                raise BusinessSemanticValidationError(
                    "Ranked regional revenue must use ORDER BY."
                )

    # ============================================================
    # OVERALL REVENUE
    # ============================================================

    def _validate_overall_revenue(
        self,
        question: str,
        sql: str
    ):

        overall_terms = [
            "total revenue",
            "overall revenue",
            "total sales",
            "overall sales revenue",
            "revenue for a period",
            "how much revenue was generated",
            "what was the revenue",
        ]

        product_terms = [
            "product",
            "products",
        ]

        region_terms = [
            "region",
            "regional",
        ]

        if not any(
            term in question
            for term in overall_terms
        ):
            return

        # Product and regional questions are handled
        # by their own validators.
        if any(
            term in question
            for term in product_terms
        ):
            return

        if any(
            term in question
            for term in region_terms
        ):
            return

        if "aibusinessanalytics.orders" not in sql:
            raise BusinessSemanticValidationError(
                "Overall revenue must use the orders table."
            )

        if not re.search(
            r"sum\s*\(\s*o\.total_amount\s*\)",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Overall revenue must use SUM(o.total_amount)."
            )

        if (
            "order_items" in sql
            or "products" in sql
        ):
            raise BusinessSemanticValidationError(
                "Overall revenue must not join "
                "order_items or products."
            )

        if (
            "oi.quantity" in sql
            or "oi.price" in sql
            or "p.price" in sql
        ):
            raise BusinessSemanticValidationError(
                "Overall revenue must not use "
                "product-level revenue logic."
            )

        # Overall revenue must produce one aggregate value.
        if re.search(
            r"\bgroup\s+by\b",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Overall revenue must return one aggregate "
                "value and must not use GROUP BY."
            )

        # Overall revenue should not rank rows.
        if re.search(
            r"\border\s+by\b",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Overall revenue must not use ORDER BY."
            )

        # Overall revenue should not limit rows.
        if re.search(
            r"\blimit\b",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Overall revenue must not use LIMIT."
            )

        # Region must not appear as a selected/grouped dimension.
        if re.search(
            r"\bo\.region\b",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Overall revenue must not select or group by region."
            )

        # order_date is allowed in WHERE for date filtering.
        # It should not be used in GROUP BY.
        if re.search(
            r"\bgroup\s+by\b",
            sql
        ) and re.search(
            r"\bo\.order_date\b",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Overall revenue must not group by order_date."
            )

    # ============================================================
    # PRODUCT REVENUE
    # ============================================================

    def _validate_product_revenue(
        self,
        question: str,
        sql: str
    ):

        product_terms = [
            "revenue by product",
            "revenue for each product",
            "which product generated",
            "which product had",
            "which products generated",
            "rank products by revenue",
            "product revenue",
            "show the revenue for each product",
            "each product",
        ]

        if not any(
            term in question
            for term in product_terms
        ):
            return

        if "aibusinessanalytics.orders" not in sql:
            raise BusinessSemanticValidationError(
                "Product revenue must start from "
                "the orders table."
            )

        if "aibusinessanalytics.order_items" not in sql:
            raise BusinessSemanticValidationError(
                "Product revenue must use order_items."
            )

        if "aibusinessanalytics.products" not in sql:
            raise BusinessSemanticValidationError(
                "Product revenue must use products."
            )

        if not re.search(
            r"sum\s*\(\s*oi\.quantity\s*\*\s*oi\.price\s*\)",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Product revenue must use "
                "SUM(oi.quantity * oi.price)."
            )

        if "p.price" in sql:
            raise BusinessSemanticValidationError(
                "Product revenue must not use products.price."
            )

        if not re.search(
            r"\bp\.product_name\b",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Product revenue must use p.product_name."
            )

        # A full product ranking must not return only one product.
        full_product_breakdown_terms = [
            "revenue by product",
            "revenue for each product",
            "show the revenue for each product",
            "rank products by revenue",
            "ranked from highest to lowest",
            "each product",
        ]

        requires_full_breakdown = any(
            term in question
            for term in full_product_breakdown_terms
        )

        if requires_full_breakdown:

            if re.search(
                r"\blimit\s+1\b",
                sql
            ):
                raise BusinessSemanticValidationError(
                    "Full product revenue breakdown must not "
                    "use LIMIT 1."
                )

            if not re.search(
                r"\bgroup\s+by\b",
                sql
            ):
                raise BusinessSemanticValidationError(
                    "Full product revenue breakdown must "
                    "use GROUP BY."
                )

            if not re.search(
                r"\bp\.product_name\b",
                sql
            ):
                raise BusinessSemanticValidationError(
                    "Full product revenue breakdown must "
                    "group by p.product_name."
                )

            if not re.search(
                r"\border\s+by\b",
                sql
            ):
                raise BusinessSemanticValidationError(
                    "Ranked product revenue must use ORDER BY."
                )

    # ============================================================
    # RETURN RATE
    # ============================================================

    def _validate_return_rate(
        self,
        question: str,
        sql: str
    ):

        """
        Validates return-rate calculations.

        Business definition:

            Return rate =
                number of distinct orders with a return
                ----------------------------------------
                total number of distinct orders
                × 100

        The date filter applies to orders.

        Multiple return records may exist for one order,
        so COUNT(DISTINCT r.order_id) is required.
        """

        return_terms = [
            "return rate",
            "returns rate",
            "rate of returns",
            "percentage of orders returned",
            "percentage of returned orders",
        ]

        if not any(
            term in question
            for term in return_terms
        ):
            return

        if "aibusinessanalytics.orders" not in sql:
            raise BusinessSemanticValidationError(
                "Return rate must use the orders table."
            )

        if "aibusinessanalytics.returns" not in sql:
            raise BusinessSemanticValidationError(
                "Return rate must use the returns table."
            )

        if not re.search(
            r"count\s*\(\s*distinct\s+r\.order_id\s*\)",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Return rate must count distinct returned orders."
            )

        if not re.search(
            r"count\s*\(\s*distinct\s+o\.order_id\s*\)",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Return rate must use the distinct order count "
                "as the denominator."
            )

        if not re.search(
            r"r\.order_id\s*=\s*o\.order_id",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Returns must be joined to orders using order_id."
            )

        if not re.search(
            r"\*\s*100",
            sql
        ):
            raise BusinessSemanticValidationError(
                "Return rate must be expressed as a percentage."
            )

        if (
            "aibusinessanalytics.order_items" in sql
            or "aibusinessanalytics.products" in sql
        ):
            raise BusinessSemanticValidationError(
                "Return rate must not require "
                "order_items or products."
            )

        # return_rate is allowed only as a calculated alias.
        if re.search(
            r"\breturn_rate\b",
            sql
        ):

            alias_pattern = (
                r"\bas\s+return_rate\b"
            )

            if not re.search(
                alias_pattern,
                sql
            ):
                raise BusinessSemanticValidationError(
                    "return_rate is a calculated metric, "
                    "not a database column."
                )