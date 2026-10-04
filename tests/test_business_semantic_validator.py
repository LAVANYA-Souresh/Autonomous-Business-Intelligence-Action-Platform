import pytest

from ai.business_semantic_validator import (
    BusinessSemanticValidationError,
    BusinessSemanticValidator
)


def test_valid_overall_revenue_query():
    validator = BusinessSemanticValidator()

    sql = """
    SELECT
        SUM(o.total_amount) AS total_revenue
    FROM aibusinessanalytics.orders o
    """

    result = validator.validate(
        question="What was the total revenue?",
        sql=sql
    )

    assert result is True


def test_valid_regional_revenue_query():
    validator = BusinessSemanticValidator()

    sql = """
    SELECT
        o.region,
        SUM(o.total_amount) AS revenue
    FROM aibusinessanalytics.orders o
    GROUP BY o.region
    ORDER BY revenue DESC
    """

    result = validator.validate(
        question="Which region had the highest revenue?",
        sql=sql
    )

    assert result is True


def test_valid_product_revenue_query():
    validator = BusinessSemanticValidator()

    sql = """
    SELECT
        p.product_name,
        SUM(oi.quantity * oi.price) AS revenue
    FROM aibusinessanalytics.orders o
    JOIN aibusinessanalytics.order_items oi
        ON o.order_id = oi.order_id
    JOIN aibusinessanalytics.products p
        ON oi.product_id = p.product_id
    GROUP BY p.product_name
    ORDER BY revenue DESC
    """

    result = validator.validate(
        question="What was the revenue by product?",
        sql=sql
    )

    assert result is True


def test_valid_return_rate_query():
    validator = BusinessSemanticValidator()

    sql = """
    SELECT
        COUNT(DISTINCT r.order_id)::numeric
        /
        NULLIF(COUNT(DISTINCT o.order_id), 0)
        * 100 AS return_rate
    FROM aibusinessanalytics.orders o
    LEFT JOIN aibusinessanalytics.returns r
        ON r.order_id = o.order_id
    """

    result = validator.validate(
        question="What was the return rate?",
        sql=sql
    )

    assert result is True


def test_reject_wrong_overall_revenue_calculation():
    validator = BusinessSemanticValidator()

    sql = """
    SELECT
        SUM(oi.quantity * oi.price) AS total_revenue
    FROM aibusinessanalytics.order_items oi
    """

    with pytest.raises(BusinessSemanticValidationError):
        validator.validate(
            question="What was the total revenue?",
            sql=sql
        )


def test_reject_wrong_product_revenue_using_product_price():
    validator = BusinessSemanticValidator()

    sql = """
    SELECT
        p.product_name,
        SUM(oi.quantity * p.price) AS revenue
    FROM aibusinessanalytics.orders o
    JOIN aibusinessanalytics.order_items oi
        ON o.order_id = oi.order_id
    JOIN aibusinessanalytics.products p
        ON oi.product_id = p.product_id
    GROUP BY p.product_name
    """

    with pytest.raises(BusinessSemanticValidationError):
        validator.validate(
            question="What was the revenue by product?",
            sql=sql
        )


def test_reject_wrong_return_rate_without_distinct_orders():
    validator = BusinessSemanticValidator()

    sql = """
    SELECT
        COUNT(r.order_id)::numeric
        /
        NULLIF(COUNT(o.order_id), 0)
        * 100 AS return_rate
    FROM aibusinessanalytics.orders o
    LEFT JOIN aibusinessanalytics.returns r
        ON r.order_id = o.order_id
    """

    with pytest.raises(BusinessSemanticValidationError):
        validator.validate(
            question="What was the return rate?",
            sql=sql
        )


def test_reject_product_revenue_without_product_name():
    validator = BusinessSemanticValidator()

    sql = """
    SELECT
        SUM(oi.quantity * oi.price) AS revenue
    FROM aibusinessanalytics.orders o
    JOIN aibusinessanalytics.order_items oi
        ON o.order_id = oi.order_id
    JOIN aibusinessanalytics.products p
        ON oi.product_id = p.product_id
    """

    with pytest.raises(BusinessSemanticValidationError):
        validator.validate(
            question="What was the revenue by product?",
            sql=sql
        )