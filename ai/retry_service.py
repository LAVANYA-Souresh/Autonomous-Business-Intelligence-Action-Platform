from ai.claim_validator import ClaimValidator
from ai.evidence_index import EvidenceIndex
from ai.validation_report import ValidationReport
from ai.text_guardrail import TextGuardrail


class AnalysisRetryService:

    def __init__(self, analysis_service, max_retries=2):
        self.analysis_service = analysis_service
        self.max_retries = max_retries

        self.evidence_index = EvidenceIndex()
        self.validator = ClaimValidator(self.evidence_index)
        self.text_guardrail = TextGuardrail()

    def validate_claims(self, analysis):
        """
        Validate all structured claims produced by the LLM.
        """

        validated_claims = []

        for claim in analysis.claims:
            validated_claim = self.validator.validate(claim)
            validated_claims.append(validated_claim)

        return validated_claims

    def build_feedback(self, validated_claims, text_issues=None):
        """
        Build correction feedback from contradicted,
        uncertain, or text-guardrail issues.
        """

        issues = []

        # Structured claim validation issues
        for claim in validated_claims:

            if claim.status.value == "contradicted":
                issues.append(
                    f"- {claim.entity} | {claim.metric} | "
                    f"CONTRADICTED: {claim.explanation}"
                )

            elif claim.status.value == "uncertain":
                issues.append(
                    f"- {claim.entity} | {claim.metric} | "
                    f"UNCERTAIN: {claim.explanation}"
                )

        # Text guardrail issues
        if text_issues:
            for issue in text_issues:
                issues.append(
                    f"- {issue['field']} | "
                    f"{issue['type']}: "
                    f"{issue['message']}"
                )

        if not issues:
            return ""

        return """
Your previous analysis contained claims or text that failed validation.

You MUST correct these issues.

Validation feedback:
""" + "\n".join(issues) + """

Rules:
- Use only the business evidence provided.
- Do not invent values.
- Do not change the direction of a metric.
- Do not use percentage when the evidence represents a count.
- Do not use percentage_points unless the evidence represents a percentage-point change.
- Avoid unsupported causal claims.
- Do not present hypotheses as confirmed facts.
- If evidence is unavailable, mark the claim as uncertain.
- Return the complete analysis again.
"""

    def analyze_with_retry(self, question, business_context):

        feedback = ""

        for attempt in range(self.max_retries + 1):

            print(
                f"\n========== AI ANALYSIS ATTEMPT "
                f"{attempt + 1} ==========\n"
            )

            current_context = business_context

            if feedback:
                current_context += "\n\n" + feedback

            analysis = self.analysis_service.analyze(
    question=question,
    business_context=business_context,
    feedback=feedback
            )

            # Validate structured claims
            validated_claims = self.validate_claims(analysis)

            report = ValidationReport(validated_claims)

            report.print_report()

            # Validate free-form text
            text_issues = self.text_guardrail.check_analysis(analysis)

            if text_issues:

                print(
                    "\n========== TEXT GUARDRAIL ISSUES ==========\n"
                )

                for issue in text_issues:
                    print(
                        f"- {issue['field']} | "
                        f"{issue['type']} | "
                        f"{issue['message']}"
                    )

            # Success condition
            if report.validation_passed and not text_issues:

                print(
                    "\nAI analysis passed all validation checks."
                )

                return analysis, validated_claims

            # Retry if validation failed
            if attempt < self.max_retries:

                print(
                    "\nValidation failed. "
                    "Sending correction feedback to the LLM..."
                )

                feedback = self.build_feedback(
                    validated_claims,
                    text_issues
                )

            else:

                print(
                    "\nMaximum retry count reached. "
                    "Returning the last analysis."
                )

        return analysis, validated_claims


if __name__ == "__main__":

    from ai.llm_client import OllamaLLMClient
    from ai.analysis_service import BusinessAnalysisService

    print("\n========== RETRY SYSTEM TEST ==========\n")

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    analysis_service = BusinessAnalysisService(
        llm_client=llm_client
    )

    retry_service = AnalysisRetryService(
        analysis_service=analysis_service,
        max_retries=2
    )

    question = "What happened to the business in May 2025?"

    business_context = """
May 2025 revenue: 115381593.0

Return rate:
Previous: 9.46%
Current: 10.13%
Change: +0.67 percentage points

Support tickets:
Previous: 158
Current: 146
Change: -12

Product evidence:
- Phone X1: revenue +32.96%, return -2
- Phone X2: revenue +23.02%, return +1
- Monitor: revenue +28.49%, return 0
- Watch: revenue +18.18%, return +8

Regional evidence:
- South India: revenue -1.97%
- East India: revenue +27.84%
- Puducherry: revenue +48.26%

The evidence does not establish causal relationships.
"""

    analysis, validated_claims = retry_service.analyze_with_retry(
        question=question,
        business_context=business_context
    )

    print("\n========== FINAL VALIDATED CLAIMS ==========\n")

    for claim in validated_claims:
        print(
            f"{claim.entity} | "
            f"{claim.metric} | "
            f"{claim.value} | "
            f"{claim.unit} | "
            f"{claim.status.value}"
        )