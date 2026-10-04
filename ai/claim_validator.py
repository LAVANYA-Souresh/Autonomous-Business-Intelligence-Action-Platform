from ai.claim_schema import (
    ExtractedClaim,
    BusinessClaim,
    ClaimStatus
)

from ai.evidence_index import EvidenceIndex


class ClaimValidator:
    """
    Deterministically validates LLM-generated claims
    against the business evidence.

    The LLM provides the claim.
    Python decides whether it is supported.
    """

    def __init__(self, evidence_index=None):
        self.evidence_index = evidence_index or EvidenceIndex()

    def validate(self, claim: ExtractedClaim) -> BusinessClaim:

        evidence = self.evidence_index.get_metric(
            claim.entity,
            claim.metric
        )

        # ---------------------------------------------------------
        # Evidence not found
        # ---------------------------------------------------------

        if evidence is None:
            return BusinessClaim(
                **claim.model_dump(),
                status=ClaimStatus.UNCERTAIN,
                explanation=(
                    f"No evidence found for entity "
                    f"'{claim.entity}' and metric '{claim.metric}'."
                )
            )

        evidence_value = evidence["value"]
        evidence_unit = evidence["unit"]
        evidence_direction = evidence["direction"]

        # ---------------------------------------------------------
        # Normalize unit names
        # ---------------------------------------------------------

        unit_aliases = {
            "%": "percentage",
            "percent": "percentage",
            "percentage": "percentage",
            "percentage_point": "percentage_points",
            "percentage point": "percentage_points",
            "percentage_points": "percentage_points",
            "percentage points": "percentage_points",
            "count": "count"
        }

        normalized_claim_unit = None

        if claim.unit is not None:
            normalized_claim_unit = unit_aliases.get(
                claim.unit.strip().lower(),
                claim.unit.strip().lower()
            )

        # ---------------------------------------------------------
        # Check metric unit
        # ---------------------------------------------------------

        if normalized_claim_unit != evidence_unit:

            return BusinessClaim(
                **claim.model_dump(),
                status=ClaimStatus.CONTRADICTED,
                explanation=(
                    f"Unit mismatch. The evidence uses "
                    f"'{evidence_unit}', but the claim uses "
                    f"'{claim.unit}'."
                )
            )

        # ---------------------------------------------------------
        # Check direction
        # ---------------------------------------------------------

        if claim.direction is not None:

            normalized_claim_direction = (
                claim.direction.strip().lower()
            )

            normalized_evidence_direction = (
                evidence_direction.strip().lower()
            )

            if (
                normalized_claim_direction
                != normalized_evidence_direction
            ):

                return BusinessClaim(
                    **claim.model_dump(),
                    status=ClaimStatus.CONTRADICTED,
                    explanation=(
                        f"Claim says the metric "
                        f"'{normalized_claim_direction}', "
                        f"but the evidence shows it "
                        f"'{normalized_evidence_direction}' "
                        f"with a change of {evidence_value}."
                    )
                )

        # ---------------------------------------------------------
        # Check numerical value
        # ---------------------------------------------------------

        if claim.value is not None:

            tolerance = 0.01

            # Normal representation
            values_match = (
                abs(claim.value - evidence_value)
                <= tolerance
            )

            # Some LLMs represent:
            # 28.49% as 0.2849
            #
            # Accept this equivalent representation only when:
            # - evidence uses percentage
            # - claim uses percentage
            # - claim value is between -1 and 1

            percentage_scaled_match = False

            if (
                evidence_unit == "percentage"
                and normalized_claim_unit == "percentage"
                and abs(claim.value) <= 1
            ):

                percentage_scaled_value = claim.value * 100

                percentage_scaled_match = (
                    abs(
                        percentage_scaled_value
                        - evidence_value
                    )
                    <= tolerance
                )

            if (
                not values_match
                and not percentage_scaled_match
            ):

                return BusinessClaim(
                    **claim.model_dump(),
                    status=ClaimStatus.CONTRADICTED,
                    explanation=(
                        f"Claim reports {claim.value}, "
                        f"but the evidence shows "
                        f"{evidence_value}."
                    )
                )

        # ---------------------------------------------------------
        # Claim is supported
        # ---------------------------------------------------------

        return BusinessClaim(
            **claim.model_dump(),
            status=ClaimStatus.SUPPORTED,
            explanation=(
                f"Claim matches the available evidence: "
                f"{evidence_value} {evidence_unit}, "
                f"direction '{evidence_direction}'."
            )
        )


def main():

    print("\n========== CLAIM VALIDATOR TEST ==========\n")

    index = EvidenceIndex()
    validator = ClaimValidator(index)

    # ---------------------------------------------------------
    # Test 1: Correct claim
    # ---------------------------------------------------------

    correct_claim = ExtractedClaim(
        entity="Phone X1",
        metric="return",
        direction="decreased",
        value=-2,
        unit="count"
    )

    result = validator.validate(correct_claim)

    print("TEST 1 — Correct claim")
    print(result.model_dump())
    print()

    # ---------------------------------------------------------
    # Test 2: Incorrect direction
    # ---------------------------------------------------------

    incorrect_direction = ExtractedClaim(
        entity="Phone X1",
        metric="return",
        direction="increased",
        unit="count"
    )

    result = validator.validate(incorrect_direction)

    print("TEST 2 — Incorrect direction")
    print(result.model_dump())
    print()

    # ---------------------------------------------------------
    # Test 3: Incorrect value
    # ---------------------------------------------------------

    incorrect_value = ExtractedClaim(
        entity="Phone X1",
        metric="return",
        direction="decreased",
        value=-8,
        unit="count"
    )

    result = validator.validate(incorrect_value)

    print("TEST 3 — Incorrect value")
    print(result.model_dump())
    print()

    # ---------------------------------------------------------
    # Test 4: Incorrect unit
    # ---------------------------------------------------------

    incorrect_unit = ExtractedClaim(
        entity="Phone X1",
        metric="return",
        direction="decreased",
        value=-2,
        unit="percentage"
    )

    result = validator.validate(incorrect_unit)

    print("TEST 4 — Incorrect unit")
    print(result.model_dump())
    print()

    # ---------------------------------------------------------
    # Test 5: Unknown evidence
    # ---------------------------------------------------------

    unknown_claim = ExtractedClaim(
        entity="Unknown Product",
        metric="return",
        direction="increased",
        unit="count"
    )

    result = validator.validate(unknown_claim)

    print("TEST 5 — Unknown evidence")
    print(result.model_dump())
    print()

    # ---------------------------------------------------------
    # Test 6: Percentage alias
    # ---------------------------------------------------------

    percentage_alias_claim = ExtractedClaim(
        entity="Phone X1",
        metric="revenue",
        direction="increased",
        value=32.96,
        unit="%"
    )

    result = validator.validate(percentage_alias_claim)

    print("TEST 6 — Percentage alias (%)")
    print(result.model_dump())
    print()

    # ---------------------------------------------------------
    # Test 7: Scaled percentage representation
    # ---------------------------------------------------------

    scaled_percentage_claim = ExtractedClaim(
        entity="Monitor",
        metric="revenue",
        direction="increased",
        value=0.2849,
        unit="%"
    )

    result = validator.validate(scaled_percentage_claim)

    print("TEST 7 — Scaled percentage (0.2849 = 28.49%)")
    print(result.model_dump())
    print()


if __name__ == "__main__":
    main()