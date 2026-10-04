from ai.sql_validator import SQLValidationError, SQLValidator


def test_valid_select():
    validator = SQLValidator()

    sql = """
    SELECT
        SUM(o.total_amount) AS total_revenue
    FROM aibusinessanalytics.orders o
    """

    result = validator.validate(sql)

    assert "SELECT" in result.upper()
    assert "SUM(o.total_amount)" in result


def test_valid_with_query():
    validator = SQLValidator()

    sql = """
    WITH revenue AS (
        SELECT SUM(o.total_amount) AS total_revenue
        FROM aibusinessanalytics.orders o
    )
    SELECT *
    FROM revenue
    """

    result = validator.validate(sql)

    assert result.upper().startswith("WITH")


def test_reject_insert():
    validator = SQLValidator()

    sql = """
    INSERT INTO aibusinessanalytics.orders
    (order_id, customer_id)
    VALUES (99999, 1)
    """

    try:
        validator.validate(sql)
        assert False, "INSERT should have been rejected."
    except SQLValidationError:
        assert True


def test_reject_update():
    validator = SQLValidator()

    sql = """
    UPDATE aibusinessanalytics.orders
    SET total_amount = 0
    """

    try:
        validator.validate(sql)
        assert False, "UPDATE should have been rejected."
    except SQLValidationError:
        assert True


def test_reject_delete():
    validator = SQLValidator()

    sql = """
    DELETE FROM aibusinessanalytics.orders
    """

    try:
        validator.validate(sql)
        assert False, "DELETE should have been rejected."
    except SQLValidationError:
        assert True


def test_reject_drop():
    validator = SQLValidator()

    sql = """
    DROP TABLE aibusinessanalytics.orders
    """

    try:
        validator.validate(sql)
        assert False, "DROP should have been rejected."
    except SQLValidationError:
        assert True


def test_reject_alter():
    validator = SQLValidator()

    sql = """
    ALTER TABLE aibusinessanalytics.orders
    ADD COLUMN test_column TEXT
    """

    try:
        validator.validate(sql)
        assert False, "ALTER should have been rejected."
    except SQLValidationError:
        assert True


def test_reject_empty_sql():
    validator = SQLValidator()

    try:
        validator.validate("")
        assert False, "Empty SQL should have been rejected."
    except SQLValidationError:
        assert True


def test_reject_multiple_statements():
    validator = SQLValidator()

    sql = """
    SELECT *
    FROM aibusinessanalytics.orders;

    SELECT *
    FROM aibusinessanalytics.customers;
    """

    try:
        validator.validate(sql)
        assert False, "Multiple statements should have been rejected."
    except SQLValidationError:
        assert True