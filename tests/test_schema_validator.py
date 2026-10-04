import pytest

from ai.schema_validator import (
    SchemaValidationError,
    SchemaValidator
)


def test_valid_orders_query():
    validator = SchemaValidator()

    sql = """
    SELECT
        o.order_id,
        o.total_amount
    FROM aibusinessanalytics.orders o
    """

    result = validator.validate(sql)

    assert result is True


def test_valid_customers_query():
    validator = SchemaValidator()

    sql = """
    SELECT
        c.customer_id,
        c.name
    FROM aibusinessanalytics.customers c
    """

    result = validator.validate(sql)

    assert result is True


def test_valid_product_join():
    validator = SchemaValidator()

    sql = """
    SELECT
        p.product_name,
        SUM(oi.quantity * oi.price) AS revenue
    FROM aibusinessanalytics.order_items oi
    JOIN aibusinessanalytics.products p
        ON oi.product_id = p.product_id
    GROUP BY p.product_name
    """

    result = validator.validate(sql)

    assert result is True


def test_reject_unknown_table():
    validator = SchemaValidator()

    sql = """
    SELECT *
    FROM aibusinessanalytics.unknown_table
    """

    with pytest.raises(SchemaValidationError):
        validator.validate(sql)


def test_reject_unknown_column():
    validator = SchemaValidator()

    sql = """
    SELECT
        o.nonexistent_column
    FROM aibusinessanalytics.orders o
    """

    with pytest.raises(SchemaValidationError):
        validator.validate(sql)


def test_reject_wrong_schema():
    validator = SchemaValidator()

    sql = """
    SELECT *
    FROM public.orders
    """

    with pytest.raises(SchemaValidationError):
        validator.validate(sql)


def test_reject_missing_schema():
    validator = SchemaValidator()

    sql = """
    SELECT *
    FROM orders
    """

    with pytest.raises(SchemaValidationError):
        validator.validate(sql)