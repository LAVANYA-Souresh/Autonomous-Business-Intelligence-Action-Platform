import re

from decimal import Decimal


class NumericalVerificationError(Exception):
    """Raised when the LLM answer contains incorrect numerical values."""
    pass


class NumericalVerifier:
    """
    Verifies numerical values in an LLM-generated answer
    against trusted database evidence.

    The verifier normalizes formatting differences such as:

        133018981.00
        133,018,981.00
        ₹133,018,981.00
        ₹13,30,18,981.00

    and treats them as the same numerical value.
    """

    # Matches:
    #
    # 133018981
    # 133018981.00
    # 133,018,981
    # 133,018,981.00
    # 13,30,18,981
    # 13,30,18,981.00
    # -12345.50
    #
    # Currency symbols are handled separately.
    #
    # IMPORTANT:
    # Western comma formatting is checked before Indian
    # comma formatting so that a value such as
    # 133,018,981.00 is captured as one complete number.

    NUMBER_PATTERN = (
        r"-?(?:"
        r"\d{1,3}(?:,\d{3})+"
        r"|"
        r"\d{1,3}(?:,\d{2})*,\d{3}"
        r"|"
        r"\d+"
        r")(?:\.\d+)?"
    )

    def verify(
        self,
        answer: str,
        sql_results: list[dict]
    ) -> dict:

        if not answer or not answer.strip():
            raise NumericalVerificationError(
                "LLM answer is empty."
            )

        if not sql_results:
            return {
                "status": "PASSED",
                "checked": False,
                "message": (
                    "No database rows available for "
                    "numerical verification."
                )
            }

        trusted_numbers = self._extract_trusted_numbers(
            sql_results
        )

        answer_numbers = self._extract_answer_numbers(
            answer
        )

        mismatches = []

        for field, expected_value in trusted_numbers.items():

            matching_values = [
                value
                for value in answer_numbers
                if self._numbers_match(
                    value,
                    expected_value
                )
            ]

            if not matching_values:

                mismatch = {
                    "field": field,
                    "expected": expected_value,
                    "found": None
                }

                # Show nearby values only as diagnostic information.
                nearby_values = [
                    value
                    for value in answer_numbers
                    if expected_value != 0
                    and abs(value - expected_value)
                    / abs(expected_value) < 0.20
                ]

                if nearby_values:

                    mismatch[
                        "possible_found_values"
                    ] = nearby_values

                mismatches.append(
                    mismatch
                )

        if mismatches:

            return {
                "status": "FAILED",
                "checked": True,
                "mismatches": mismatches
            }

        return {
            "status": "PASSED",
            "checked": True,
            "mismatches": []
        }

    # ---------------------------------------------------------
    # Extract trusted database numbers
    # ---------------------------------------------------------

    def _extract_trusted_numbers(
        self,
        sql_results: list[dict]
    ) -> dict:

        trusted_numbers = {}

        for row in sql_results:

            for field, value in row.items():

                if isinstance(
                    value,
                    (int, float, Decimal)
                ):

                    trusted_numbers[field] = float(
                        str(value).replace(
                            ",",
                            ""
                        )
                    )

        return trusted_numbers

    # ---------------------------------------------------------
    # Extract numbers from LLM answer
    # ---------------------------------------------------------

    def _extract_answer_numbers(
        self,
        answer: str
    ) -> list[float]:

        matches = re.findall(
            self.NUMBER_PATTERN,
            answer
        )

        numbers = []

        for value in matches:

            # Remove thousands separators.
            normalized = value.replace(
                ",",
                ""
            )

            try:

                numbers.append(
                    float(normalized)
                )

            except ValueError:

                continue

        return numbers

    # ---------------------------------------------------------
    # Compare numerical values
    # ---------------------------------------------------------

    def _numbers_match(
        self,
        actual: float,
        expected: float,
        tolerance: float = 0.01
    ) -> bool:

        return abs(
            actual - expected
        ) <= tolerance


# =============================================================
# TESTS
# =============================================================

if __name__ == "__main__":

    verifier = NumericalVerifier()

    # ---------------------------------------------------------
    # Test 1: Correct regional revenue
    # ---------------------------------------------------------

    database_results = [
        {
            "region": "Puducherry",
            "revenue": 30057941.0
        }
    ]

    correct_answer = """
    Puducherry generated revenue of
    30,057,941.0 in May 2025.
    """

    incorrect_answer = """
    Puducherry generated revenue of
    3 in May 2025.
    """

    print(
        "\nTesting correct answer..."
    )

    result = verifier.verify(
        correct_answer,
        database_results
    )

    print(result)

    print(
        "\nTesting incorrect answer..."
    )

    result = verifier.verify(
        incorrect_answer,
        database_results
    )

    print(result)

    # ---------------------------------------------------------
    # Test 2: Large revenue without commas
    # ---------------------------------------------------------

    database_results = [
        {
            "revenue": Decimal(
                "133018981.00"
            )
        }
    ]

    answer_without_commas = """
    Revenue in May 2025 was 133018981.00.
    """

    print(
        "\nTesting large number without commas..."
    )

    result = verifier.verify(
        answer_without_commas,
        database_results
    )

    print(result)

    # ---------------------------------------------------------
    # Test 3: Large revenue with western commas
    # ---------------------------------------------------------

    answer_with_commas = """
    Revenue in May 2025 was ₹133,018,981.00.
    """

    print(
        "\nTesting large number with commas..."
    )

    result = verifier.verify(
        answer_with_commas,
        database_results
    )

    print(result)

    # ---------------------------------------------------------
    # Test 4: Large revenue with Indian commas
    # ---------------------------------------------------------

    answer_with_indian_commas = """
    Revenue in May 2025 was ₹13,30,18,981.00.
    """

    print(
        "\nTesting Indian number formatting..."
    )

    result = verifier.verify(
        answer_with_indian_commas,
        database_results
    )

    print(result)

    # ---------------------------------------------------------
    # Test 5: Wrong large number
    # ---------------------------------------------------------

    wrong_large_answer = """
    Revenue in May 2025 was ₹13,301,898.10.
    """

    print(
        "\nTesting incorrect large number..."
    )

    result = verifier.verify(
        wrong_large_answer,
        database_results
    )

    print(result)