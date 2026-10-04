from typing import List, Dict, Any

from ai.response_schema import BusinessAnalysis
from ai.claim_schema import BusinessClaim, ClaimStatus


class AnalysisGuardrailResult:
    """
    Stores the result of validating an AI-generated analysis.
    """

    def __init__(
        self,
        passed: bool,
        claims: List[BusinessClaim],
        issues: List[str],
        warnings: List[str]
    ):
        self.passed = passed
        self.claims = claims
        self.issues = issues
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:

        return {
            "passed": self.passed,
            "claims": [
                claim.model_dump()
                for claim in self.claims
            ],
            "issues": self.issues,
            "warnings": self.warnings
        }


def validate_business_analysis(
    analysis: BusinessAnalysis,
    evidence: Dict[str, Any]
) -> AnalysisGuardrailResult:

    issues = []
    warnings = []
    claims = []

    product_evidence = {
        item["product"]: item
        for item in evidence.get("product_evidence", [])
    }

    regional_evidence = {
        item["region"]: item
        for item in evidence.get("regional_evidence", [])
    }

    all_text = " ".join(
        analysis.observed_facts
        + analysis.supporting_evidence
        + analysis.possible_explanations
    ).lower()

    # =========================================================
    # PRODUCT EVIDENCE
    # =========================================================

    for product_name, product_data in product_evidence.items():

        product_lower = product_name.lower()

        if product_lower not in all_text:
            continue

        expected_revenue_change = (
            product_data["revenue_change_percentage"]
        )

        expected_return_change = (
            product_data["return_change"]
        )

        # -----------------------------------------------------
        # Revenue direction
        # -----------------------------------------------------

        if expected_revenue_change > 0:

            incorrect_patterns = [
                f"revenue decreased in {product_lower}",
                f"revenue declined in {product_lower}",
                f"revenue fell in {product_lower}"
            ]

            for pattern in incorrect_patterns:

                if pattern in all_text:

                    claim = BusinessClaim(
                        entity=product_name,
                        metric="revenue",
                        direction="decreased",
                        value=None,
                        unit="percentage",
                        status=ClaimStatus.CONTRADICTED,
                        explanation=(
                            f"Evidence shows revenue changed "
                            f"by {expected_revenue_change:+.2f}%."
                        )
                    )

                    claims.append(claim)

                    issues.append(
                        f"Incorrect revenue direction for "
                        f"{product_name}: evidence shows "
                        f"{expected_revenue_change:+.2f}%."
                    )

        elif expected_revenue_change < 0:

            incorrect_patterns = [
                f"revenue increased in {product_lower}",
                f"revenue rose in {product_lower}",
                f"revenue grew in {product_lower}"
            ]

            for pattern in incorrect_patterns:

                if pattern in all_text:

                    claim = BusinessClaim(
                        entity=product_name,
                        metric="revenue",
                        direction="increased",
                        value=None,
                        unit="percentage",
                        status=ClaimStatus.CONTRADICTED,
                        explanation=(
                            f"Evidence shows revenue changed "
                            f"by {expected_revenue_change:+.2f}%."
                        )
                    )

                    claims.append(claim)

                    issues.append(
                        f"Incorrect revenue direction for "
                        f"{product_name}: evidence shows "
                        f"{expected_revenue_change:+.2f}%."
                    )

        # -----------------------------------------------------
        # Return direction
        # -----------------------------------------------------

        if expected_return_change > 0:

            if (
                "return rates decreased"
                in all_text
            ):

                claim = BusinessClaim(
                    entity=product_name,
                    metric="returns",
                    direction="decreased",
                    value=float(expected_return_change),
                    unit="count",
                    status=ClaimStatus.CONTRADICTED,
                    explanation=(
                        f"Evidence shows return change "
                        f"of {expected_return_change:+d}."
                    )
                )

                claims.append(claim)

                issues.append(
                    f"Incorrect return direction for "
                    f"{product_name}: evidence shows "
                    f"{expected_return_change:+d}."
                )

        elif expected_return_change < 0:

            if (
                "return rates increased"
                in all_text
            ):

                claim = BusinessClaim(
                    entity=product_name,
                    metric="returns",
                    direction="increased",
                    value=float(abs(expected_return_change)),
                    unit="count",
                    status=ClaimStatus.CONTRADICTED,
                    explanation=(
                        f"Evidence shows return change "
                        f"of {expected_return_change:+d}."
                    )
                )

                claims.append(claim)

                issues.append(
                    f"Incorrect return direction for "
                    f"{product_name}: evidence shows "
                    f"{expected_return_change:+d}."
                )

    # =========================================================
    # REGIONAL EVIDENCE
    # =========================================================

    for region_name, region_data in regional_evidence.items():

        region_lower = region_name.lower()

        if region_lower not in all_text:
            continue

        expected_change = (
            region_data["revenue_change_percentage"]
        )

        if expected_change > 0:

            if (
                f"revenue decreased in {region_lower}"
                in all_text
                or
                f"revenue declined in {region_lower}"
                in all_text
            ):

                claim = BusinessClaim(
                    entity=region_name,
                    metric="revenue",
                    direction="decreased",
                    value=None,
                    unit="percentage",
                    status=ClaimStatus.CONTRADICTED,
                    explanation=(
                        f"Evidence shows regional revenue "
                        f"changed by {expected_change:+.2f}%."
                    )
                )

                claims.append(claim)

                issues.append(
                    f"Incorrect regional revenue direction "
                    f"for {region_name}: evidence shows "
                    f"{expected_change:+.2f}%."
                )

        elif expected_change < 0:

            if (
                f"revenue increased in {region_lower}"
                in all_text
                or
                f"revenue grew in {region_lower}"
                in all_text
            ):

                claim = BusinessClaim(
                    entity=region_name,
                    metric="revenue",
                    direction="increased",
                    value=None,
                    unit="percentage",
                    status=ClaimStatus.CONTRADICTED,
                    explanation=(
                        f"Evidence shows regional revenue "
                        f"changed by {expected_change:+.2f}%."
                    )
                )

                claims.append(claim)

                issues.append(
                    f"Incorrect regional revenue direction "
                    f"for {region_name}: evidence shows "
                    f"{expected_change:+.2f}%."
                )

    # =========================================================
    # CAUSAL LANGUAGE
    # =========================================================

    causal_phrases = [
        "caused by",
        "caused the",
        "resulted from",
        "resulted in",
        "because of",
        "due to",
        "led to"
    ]

    for phrase in causal_phrases:

        if phrase in all_text:

            warnings.append(
                f"Potential causal language detected: "
                f"'{phrase}'. Causal relationships require "
                f"direct evidence."
            )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    passed = len(issues) == 0

    return AnalysisGuardrailResult(
        passed=passed,
        claims=claims,
        issues=issues,
        warnings=warnings
    )


if __name__ == "__main__":

    print("\n========== GUARDRAIL MODULE TEST ==========\n")

    print("Guardrail module loaded successfully.")