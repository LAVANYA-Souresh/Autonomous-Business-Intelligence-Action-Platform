
import re


class TextGuardrail:

    def __init__(self):

        # Strong causal statements
        self.causal_patterns = [
            r"\bbecause\b",
            r"\bcaused by\b",
            r"\bcauses\b",
            r"\bcaused\b",
            r"\bresulted from\b",
            r"\bwas driven by\b",
            r"\bwere driven by\b",
            r"\bdriven by\b",
            r"\bled to\b",
            r"\bleads to\b",
            r"\bthe reason is\b",
            r"\bthis explains\b",
        ]

        # "due to" needs special handling because
        # it can appear inside a cautious statement.
        self.due_to_pattern = r"\bdue to\b"

        # Business concepts that should not be presented
        # as established causes without evidence.
        self.unsupported_business_patterns = [
            r"\bcustomer satisfaction\b",
            r"\bcustomer preference\b",
            r"\bcustomer preferences\b",
            r"\bproduct quality\b",
            r"\bmarket demand\b",
            r"\bcustomer demand\b",
            r"\bcustomer loyalty\b",
            r"\bbrand perception\b",
        ]

        # Language indicating uncertainty or investigation.
        self.safe_context_patterns = [
            r"\bdoes not establish\b",
            r"\bdoesn't establish\b",
            r"\bnot establish\b",
            r"\bcannot establish\b",
            r"\bcan't establish\b",
            r"\bno evidence\b",
            r"\binsufficient evidence\b",
            r"\bunknown whether\b",
            r"\bunknown if\b",
            r"\bunclear whether\b",
            r"\bunclear if\b",
            r"\bnot clear whether\b",
            r"\bnot clear if\b",
            r"\bwhether\b",
            r"\bmay be\b",
            r"\bmight be\b",
            r"\bcould be\b",
            r"\bpossible explanation\b",
            r"\bpossible explanations\b",
            r"\bhypothesis\b",
            r"\bhypotheses\b",
            r"\binvestigate\b",
            r"\binvestigation\b",
            r"\btest whether\b",
            r"\btest if\b",
            r"\bdetermine whether\b",
            r"\bdetermine if\b",
        ]

    def check_text(self, text: str):

        issues = []

        if not text:
            return issues

        text_lower = text.lower()

        # Check whether the sentence is clearly
        # cautious, uncertain, or investigative.
        has_safe_context = self._has_safe_context(text_lower)

        # --------------------------------------------------
        # 1. Check strong causal language
        # --------------------------------------------------

        for pattern in self.causal_patterns:

            if re.search(pattern, text_lower):

                # Do not flag causal wording when it is
                # explicitly framed as uncertain or investigative.
                if not has_safe_context:

                    issues.append({
                        "type": "causal_language",
                        "message": (
                            f"Potential causal claim detected: "
                            f"'{pattern}'"
                        )
                    })

        # --------------------------------------------------
        # 2. Check "due to"
        # --------------------------------------------------

        if re.search(self.due_to_pattern, text_lower):

            if not has_safe_context:

                issues.append({
                    "type": "causal_language",
                    "message": (
                        "Potential causal claim detected: "
                        "'due to'"
                    )
                })

        # --------------------------------------------------
        # 3. Check unsupported business concepts
        # --------------------------------------------------

        for pattern in self.unsupported_business_patterns:

            if re.search(pattern, text_lower):

                # Allow these concepts when they appear in
                # an investigation or uncertainty context.
                if not has_safe_context:

                    issues.append({
                        "type": "unsupported_business_claim",
                        "message": (
                            "Potential unsupported business claim "
                            f"detected: '{pattern}'"
                        )
                    })

        return issues

    def _has_safe_context(self, text_lower):

        for pattern in self.safe_context_patterns:

            if re.search(pattern, text_lower):
                return True

        return False

    def check_analysis(self, analysis):

        issues = []

        issues.extend(
            self._check_field(
                "summary",
                analysis.summary
            )
        )

        for item in analysis.observed_facts:

            issues.extend(
                self._check_field(
                    "observed_facts",
                    self._item_to_text(item)
                )
            )

        for item in analysis.supporting_evidence:

            issues.extend(
                self._check_field(
                    "supporting_evidence",
                    self._item_to_text(item)
                )
            )

        for item in analysis.possible_explanations:

            issues.extend(
                self._check_field(
                    "possible_explanations",
                    item
                )
            )

        for item in analysis.uncertainty:

            issues.extend(
                self._check_field(
                    "uncertainty",
                    item
                )
            )

        for item in analysis.recommended_next_investigation:

            issues.extend(
                self._check_field(
                    "recommended_next_investigation",
                    item
                )
            )

        return issues

    def _check_field(self, field_name, text):

        issues = self.check_text(text)

        for issue in issues:

            issue["field"] = field_name

        return issues

    def _item_to_text(self, item):

        if isinstance(item, str):
            return item

        if hasattr(item, "model_dump"):
            return str(item.model_dump())

        return str(item)


if __name__ == "__main__":

    guardrail = TextGuardrail()

    test_sentences = [

        # --------------------------------------------------
        # These SHOULD be flagged
        # --------------------------------------------------

        "Revenue increased because customers preferred the product.",

        "Revenue increased due to better product quality.",

        "Customer satisfaction caused the increase.",

        "The increase was driven by customer demand.",

        "The change resulted from better product quality.",

        # --------------------------------------------------
        # These SHOULD pass
        # --------------------------------------------------

        "Revenue in Puducherry increased by 48.26%.",

        "The evidence does not establish whether the increase was due to customer satisfaction.",

        "It is unclear whether product quality affected revenue.",

        "One possible explanation is increased customer demand.",

        "Investigate customer satisfaction.",

        "Investigate product quality as a possible factor.",

        "The available evidence does not establish the cause.",

        "There is insufficient evidence to determine whether customer demand affected revenue.",
    ]

    print("\n========== TEXT GUARDRAIL TEST ==========\n")

    for sentence in test_sentences:

        issues = guardrail.check_text(sentence)

        print(f"Text: {sentence}")

        if issues:

            print("Status: FLAGGED")

            for issue in issues:

                print(
                    f"- {issue['type']}: "
                    f"{issue['message']}"
                )

        else:

            print("Status: PASSED")

        print()

