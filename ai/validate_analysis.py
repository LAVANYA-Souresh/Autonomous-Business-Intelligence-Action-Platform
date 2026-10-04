from ai.claim_validator import ClaimValidator
from ai.evidence_index import EvidenceIndex
from ai.response_schema import BusinessAnalysis
from ai.validation_report import ValidationReport


def validate_analysis(analysis: BusinessAnalysis):
    """
    Validate every structured claim produced by the LLM.
    """

    evidence_index = EvidenceIndex()
    validator = ClaimValidator(evidence_index)

    validated_claims = []

    for claim in analysis.claims:
        validated_claim = validator.validate(claim)
        validated_claims.append(validated_claim)

    return validated_claims


def main():

    print("\n========== ANALYSIS CLAIM VALIDATION ==========\n")

    from ai.llm_client import OllamaLLMClient
    from ai.analysis_service import BusinessAnalysisService

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    service = BusinessAnalysisService(
        llm_client=llm_client
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

    print("Sending question to Qwen...\n")

    analysis = service.analyze(
        question=question,
        business_context=business_context
    )

    validated_claims = validate_analysis(analysis)

    print("\n========== VALIDATED CLAIMS ==========\n")

    for claim in validated_claims:
        print(
            f"{claim.entity} | "
            f"{claim.metric} | "
            f"{claim.value} | "
            f"{claim.unit} | "
            f"{claim.status.value}"
        )
        print(f"Explanation: {claim.explanation}\n")

    report = ValidationReport(validated_claims)
    report.print_report()


if __name__ == "__main__":
    main()