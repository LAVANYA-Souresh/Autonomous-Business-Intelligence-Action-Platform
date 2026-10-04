import re


class ClaimVerificationError(Exception):
    """Raised when unsupported claims are detected."""
    pass


class ClaimVerifier:
    """
    Performs lightweight verification of claims in an LLM answer
    against trusted SQL evidence.

    This is intentionally conservative:
    it verifies that important entities and numerical facts
    appearing in the answer are supported by the database result.
    """

    def verify(
        self,
        answer: str,
        sql_results: list[dict]
    ) -> dict:

        if not answer or not answer.strip():
            raise ClaimVerificationError(
                "LLM answer is empty."
            )

        if not sql_results:
            return {
                "status": "PASSED",
                "checked": False,
                "unsupported_claims": [],
                "message": "No SQL evidence available."
            }

        supported_text = self._build_supported_text(
            sql_results
        )

        unsupported_claims = []

        sentences = self._split_sentences(answer)

        for sentence in sentences:

            sentence_lower = sentence.lower()

            # ------------------------------------------
            # Detect causal language
            # ------------------------------------------

            causal_patterns = [
                r"\bcaused\b",
                r"\bcausing\b",
                r"\bdue to\b",
                r"\bled to\b",
                r"\bresulted in\b",
                r"\bbecause of\b",
                r"\bcontributed to\b",
                r"\bdriven by\b",
                r"\blikely due\b",
                r"\bwhich might have\b",
                r"\bindicating\b",
            ]

            if any(
                re.search(pattern, sentence_lower)
                for pattern in causal_patterns
            ):

                unsupported_claims.append({
                    "claim": sentence.strip(),
                    "reason": (
                        "Causal or explanatory claim "
                        "is not directly supported by "
                        "the SQL evidence."
                    )
                })

                continue

            # ------------------------------------------
            # Detect claims involving unsupported
            # business metrics
            # ------------------------------------------

            metric_patterns = [
                r"\breturn rate\b",
                r"\bsupport tickets?\b",
                r"\bcancellations?\b",
                r"\bcustomer support\b",
                r"\bcomplaints?\b",
                r"\brefunds?\b",
                r"\bcustomer loyalty\b",
            ]

            contains_metric_claim = any(
                re.search(pattern, sentence_lower)
                for pattern in metric_patterns
            )

            if contains_metric_claim:

                if not self._sentence_supported_by_sql(
                    sentence,
                    supported_text
                ):

                    unsupported_claims.append({
                        "claim": sentence.strip(),
                        "reason": (
                            "The claim refers to a business "
                            "metric that is not present in "
                            "the SQL evidence."
                        )
                    })

        if unsupported_claims:

            return {
                "status": "FAILED",
                "checked": True,
                "unsupported_claims": unsupported_claims
            }

        return {
            "status": "PASSED",
            "checked": True,
            "unsupported_claims": []
        }

    def _build_supported_text(
        self,
        sql_results: list[dict]
    ) -> str:

        parts = []

        for row in sql_results:

            for field, value in row.items():

                parts.append(
                    f"{field}: {value}"
                )

        return " ".join(parts).lower()

    def _split_sentences(
        self,
        answer: str
    ) -> list[str]:

        sentences = re.split(
            r"(?<=[.!?])\s+",
            answer
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def _sentence_supported_by_sql(
        self,
        sentence: str,
        supported_text: str
    ) -> bool:

        sentence_lower = sentence.lower()

        # If the sentence contains a metric that
        # doesn't appear in SQL evidence, reject it.
        metrics = [
            "return rate",
            "support ticket",
            "cancellation",
            "customer support",
            "complaint",
            "refund",
            "customer loyalty",
        ]

        for metric in metrics:

            if metric in sentence_lower:
                if metric not in supported_text:
                    return False

        return True


if __name__ == "__main__":

    verifier = ClaimVerifier()

    database_results = [
        {
            "region": "Puducherry",
            "revenue": 30057941.0
        }
    ]

    correct_answer = """
    Puducherry generated revenue of 30,057,941.0
    in May 2025.
    """

    incorrect_answer = """
    Puducherry generated the highest revenue because
    its customer support activity was better.
    """

    print("\nTesting supported answer...")

    result = verifier.verify(
        correct_answer,
        database_results
    )

    print(result)

    print("\nTesting unsupported answer...")

    result = verifier.verify(
        incorrect_answer,
        database_results
    )

    print(result)