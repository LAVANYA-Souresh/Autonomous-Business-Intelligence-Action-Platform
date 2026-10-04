from decimal import Decimal

from ai.numerical_verifier import NumericalVerifier


def test_correct_revenue_without_commas():
    verifier = NumericalVerifier()

    answer = (
        "The revenue was ₹133018981.00."
    )

    sql_results = [
        {
            "total_revenue": Decimal(
                "133018981.00"
            )
        }
    ]

    result = verifier.verify(
        answer=answer,
        sql_results=sql_results
    )

    assert result["status"] == "PASSED"
    assert result["checked"] is True
    assert result["mismatches"] == []


def test_correct_revenue_with_western_commas():
    verifier = NumericalVerifier()

    answer = (
        "The revenue was ₹133,018,981.00."
    )

    sql_results = [
        {
            "total_revenue": Decimal(
                "133018981.00"
            )
        }
    ]

    result = verifier.verify(
        answer=answer,
        sql_results=sql_results
    )

    assert result["status"] == "PASSED"


def test_correct_revenue_with_indian_commas():
    verifier = NumericalVerifier()

    answer = (
        "The revenue was ₹13,30,18,981.00."
    )

    sql_results = [
        {
            "total_revenue": Decimal(
                "133018981.00"
            )
        }
    ]

    result = verifier.verify(
        answer=answer,
        sql_results=sql_results
    )

    assert result["status"] == "PASSED"


def test_incorrect_revenue():
    verifier = NumericalVerifier()

    answer = (
        "The revenue was ₹120,000,000.00."
    )

    sql_results = [
        {
            "total_revenue": Decimal(
                "133018981.00"
            )
        }
    ]

    result = verifier.verify(
        answer=answer,
        sql_results=sql_results
    )

    assert result["status"] == "FAILED"
    assert result["checked"] is True
    assert len(result["mismatches"]) == 1


def test_correct_regional_revenue():
    verifier = NumericalVerifier()

    answer = (
        "Puducherry revenue was ₹25,000,000.00."
    )

    sql_results = [
        {
            "region": "Puducherry",
            "revenue": Decimal(
                "25000000.00"
            )
        }
    ]

    result = verifier.verify(
        answer=answer,
        sql_results=sql_results
    )

    assert result["status"] == "PASSED"


def test_incorrect_regional_revenue():
    verifier = NumericalVerifier()

    answer = (
        "Puducherry revenue was ₹20,000,000.00."
    )

    sql_results = [
        {
            "region": "Puducherry",
            "revenue": Decimal(
                "25000000.00"
            )
        }
    ]

    result = verifier.verify(
        answer=answer,
        sql_results=sql_results
    )

    assert result["status"] == "FAILED"


def test_empty_answer_fails():
    verifier = NumericalVerifier()

    sql_results = [
        {
            "total_revenue": Decimal(
                "133018981.00"
            )
        }
    ]

    result = None

    try:
        verifier.verify(
            answer="",
            sql_results=sql_results
        )
    except Exception:
        result = "FAILED"

    assert result == "FAILED"


def test_no_sql_results():
    verifier = NumericalVerifier()

    answer = (
        "The analysis could not produce database results."
    )

    result = verifier.verify(
        answer=answer,
        sql_results=[]
    )

    assert result["status"] == "PASSED"
    assert result["checked"] is False