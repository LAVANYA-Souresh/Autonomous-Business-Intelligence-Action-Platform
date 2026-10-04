from typing import Any


class RecommendationEngineError(Exception):
    """Raised when a recommendation cannot be generated."""
    pass


class RecommendationEngine:
    """
    Generates business recommendations from verified evidence.

    This engine is intentionally deterministic:
    - It does not invent facts.
    - It does not modify database values.
    - It does not perform business actions.
    - Every recommendation requires human review.
    """
    
    def _format_inr(self, value):
        """
        Format a numeric value as Indian Rupees.

        Example:
        133018981.00 → ₹13,30,18,981.00
        """
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        formatted = f"{number:,.2f}"

        integer_part, decimal_part = formatted.split(".")

        parts = integer_part.split(",")

        if len(parts) > 1:
            last_three = parts[-1]
            remaining = parts[:-1]

            first_group = remaining[0]
            other_groups = remaining[1:]

            grouped = first_group

            for group in other_groups:
                grouped += "," + group

            if grouped:
                grouped = grouped + "," + last_three
            else:
                grouped = last_three
        else:
            grouped = integer_part

        # Convert western grouping to Indian grouping.
        digits = integer_part.replace(",", "")

        if len(digits) > 3:
            last_three = digits[-3:]
            remaining = digits[:-3]

            groups = []

            while len(remaining) > 2:
                groups.insert(0, remaining[-2:])
                remaining = remaining[:-2]

            groups.insert(0, remaining)

            indian_integer = ",".join(groups) + "," + last_three
        else:
            indian_integer = digits

        return f"₹{indian_integer}.{decimal_part}"

    def recommend(
        self,
        evidence_package: dict[str, Any]
    ) -> dict[str, Any]:

        if not evidence_package:
            raise RecommendationEngineError(
                "Evidence package is required."
            )

        if evidence_package.get("final_status") != "VERIFIED":
            raise RecommendationEngineError(
                "Recommendations can only be generated from verified evidence."
            )

        question = evidence_package.get("question", "")
        analysis = evidence_package.get("analysis", {})
        workflow = analysis.get("workflow", "")
        plan = analysis.get("plan", {})
        execution_result = evidence_package.get(
            "database_evidence",
            {}
        ).get("execution_result", {})

        results = execution_result.get("results", [])

        if not results:
            raise RecommendationEngineError(
                "Verified database results are required."
            )

        if workflow == "simple_factual":
            return self._recommend_simple_factual(
                question,
                plan,
                results
            )

        if workflow == "trend":
            return self._recommend_trend(
                question,
                plan,
                results
            )

        if workflow == "diagnostic":
            return self._recommend_diagnostic(
                question,
                plan,
                results
            )

        if workflow == "comparison":
            return self._recommend_comparison(
                question,
                plan,
                results
            )

        raise RecommendationEngineError(
            f"Unsupported workflow: {workflow}"
        )

    def _recommend_simple_factual(
        self,
        question: str,
        plan: dict[str, Any],
        results: list[dict[str, Any]]
    ) -> dict[str, Any]:

        row = results[0]

        if "region" in row and "total_revenue" in row:
            region = row["region"]
            revenue = row["total_revenue"]

            return self._build_recommendation(
                question=question,
                workflow="simple_factual",
                observed_fact=(
                    f"{region} generated the highest revenue "
                    f"in the analyzed period with revenue {revenue}."
                ),
                implication=(
                    f"{region} is the highest-revenue region "
                    f"in the analyzed period."
                ),
                action=(
                    f"Review {region} sales, inventory, and customer-support "
                    "performance before making region-specific resource "
                    "or promotion decisions."
                ),
                reason=(
                    "The recommendation is based on verified regional "
                    "revenue evidence. The evidence identifies performance "
                    "but does not establish its underlying causes."
                ),
                evidence_confidence="HIGH",
                recommendation_confidence="MEDIUM"
            )

        if "region" in row and "revenue" in row:
            region = row["region"]
            revenue = row["revenue"]

            return self._build_recommendation(
                question=question,
                workflow="simple_factual",
                observed_fact=(
                    f"{region} generated revenue of {revenue} "
                    "in the analyzed period."
                ),
                implication=(
                    f"{region} represents a measurable revenue "
                    "contribution in the analyzed period."
                ),
                action=(
                    f"Review {region}-specific sales and operational "
                    "performance before making resource-allocation decisions."
                ),
                reason=(
                    "The recommendation is based on verified regional "
                    "revenue evidence."
                ),
                evidence_confidence="HIGH",
                recommendation_confidence="MEDIUM"
            )

        if "product_name" in row:
            product = row["product_name"]

            revenue = row.get(
                "revenue",
                row.get("total_revenue")
            )

            return self._build_recommendation(
                question=question,
                workflow="simple_factual",
                observed_fact=(
                    f"{product} generated revenue of {revenue} "
                    "in the analyzed period."
                ),
                implication=(
                    f"{product} is a significant product-level "
                    "revenue observation for the analyzed period."
                ),
                action=(
                    f"Review {product} sales velocity, inventory "
                    "availability, and customer-support performance "
                    "before increasing promotion or inventory allocation."
                ),
                reason=(
                    "The recommendation is based on verified product-level "
                    "revenue evidence. Additional operational evidence "
                    "is needed before taking action."
                ),
                evidence_confidence="HIGH",
                recommendation_confidence="MEDIUM"
            )

        if "total_revenue" in row:
            revenue = row["total_revenue"]

            return self._build_recommendation(
                question=question,
                workflow="simple_factual",
                observed_fact=(
                    f"Total revenue in the analyzed period was {self._format_inr(revenue)}."
                ),
                implication=(
                    "The result provides a verified baseline for "
                    "the analyzed period."
                ),
                action=(
                    "Use this verified revenue baseline together with "
                    "regional, product, return, and operational evidence "
                    "before making business decisions."
                ),
                reason=(
                    "A single overall revenue figure establishes a baseline "
                    "but does not explain the drivers behind performance."
                ),
                evidence_confidence="HIGH",
                recommendation_confidence="MEDIUM"
            )

        return self._build_recommendation(
            question=question,
            workflow="simple_factual",
            observed_fact=(
                "The verified database query returned a business result."
            ),
            implication=(
                "The result can be used as evidence for further analysis."
            ),
            action=(
                "Review the underlying business dimensions and supporting "
                "evidence before making an operational decision."
            ),
            reason=(
                "The available evidence is factual but does not provide "
                "enough context for a more specific recommendation."
            ),
            evidence_confidence="HIGH",
            recommendation_confidence="LOW"
        )

    def _recommend_trend(
        self,
        question: str,
        plan: dict[str, Any],
        results: list[dict[str, Any]]
    ) -> dict[str, Any]:

        periods = [
            item.get("period")
            for item in results
            if item.get("period")
        ]

        period_text = ", ".join(periods)

        return self._build_recommendation(
            question=question,
            workflow="trend",
            observed_fact=(
                f"Verified trend evidence was collected for "
                f"{period_text}."
            ),
            implication=(
                "The analyzed periods provide a basis for identifying "
                "changes in business performance."
            ),
            action=(
                "Review the trend together with regional, product, "
                "return, and operational evidence before changing "
                "business strategy."
            ),
            reason=(
                "Trend evidence identifies performance movement but "
                "does not by itself establish why the movement occurred."
            ),
            evidence_confidence="HIGH",
            recommendation_confidence="MEDIUM"
        )

    def _recommend_diagnostic(
        self,
        question: str,
        plan: dict[str, Any],
        results: list[dict[str, Any]]
    ) -> dict[str, Any]:

        return self._build_recommendation(
            question=question,
            workflow="diagnostic",
            observed_fact=(
                "Verified diagnostic evidence was collected across "
                "multiple business dimensions."
            ),
            implication=(
                "The evidence can be used to prioritize areas requiring "
                "further business investigation."
            ),
            action=(
                "Investigate the largest regional and product-level "
                "changes first, then review return and operational "
                "signals before implementing any intervention."
            ),
            reason=(
                "Diagnostic evidence can identify where performance "
                "changed, but additional investigation is required "
                "before attributing causes or taking action."
            ),
            evidence_confidence="HIGH",
            recommendation_confidence="MEDIUM"
        )

    def _recommend_comparison(
        self,
        question: str,
        plan: dict[str, Any],
        results: list[dict[str, Any]]
    ) -> dict[str, Any]:

        return self._build_recommendation(
            question=question,
            workflow="comparison",
            observed_fact=(
                "Verified comparison evidence was collected for "
                "the requested business dimensions."
            ),
            implication=(
                "The comparison can be used to identify relatively "
                "stronger or weaker business segments."
            ),
            action=(
                "Review the strongest and weakest segments alongside "
                "operational evidence before reallocating resources."
            ),
            reason=(
                "Comparison results show relative performance but "
                "do not independently explain the reasons for the difference."
            ),
            evidence_confidence="HIGH",
            recommendation_confidence="MEDIUM"
        )

    def _build_recommendation(
        self,
        question: str,
        workflow: str,
        observed_fact: str,
        implication: str,
        action: str,
        reason: str,
        evidence_confidence: str,
        recommendation_confidence: str
    ) -> dict[str, Any]:

        return {
            "recommendation_status": "READY_FOR_REVIEW",
            "workflow": workflow,
            "question": question,
            "observed_fact": observed_fact,
            "business_implication": implication,
            "recommended_action": action,
            "reason": reason,
            "evidence_confidence": evidence_confidence,
            "recommendation_confidence": recommendation_confidence,
            "human_approval_required": True,
            "action_executed": False,
            "source": "verified_database_evidence"
        }


if __name__ == "__main__":

    sample_evidence_package = {
        "question": "Which region generated the highest revenue in May 2025?",
        "analysis": {
            "workflow": "simple_factual",
            "plan": {
                "analysis_type": "simple_factual",
                "primary_metric": "revenue",
                "dimensions": ["region"],
                "time_periods": ["May 2025"],
                "requires_multiple_queries": False
            }
        },
        "database_evidence": {
            "execution_result": {
                "status": "EXECUTED",
                "results": [
                    {
                        "region": "Puducherry",
                        "total_revenue": 30057941.00
                    }
                ]
            }
        },
        "final_status": "VERIFIED"
    }

    engine = RecommendationEngine()

    recommendation = engine.recommend(
        sample_evidence_package
    )

    print("Recommendation Engine Test")
    print("==========================")

    for key, value in recommendation.items():
        print(f"{key}: {value}")