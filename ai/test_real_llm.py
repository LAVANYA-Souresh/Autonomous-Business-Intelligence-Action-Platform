from ai.llm_client import OllamaLLMClient
from ai.analysis_service import BusinessAnalysisService


def main():

    print("\n========== REAL LLM ANALYSIS TEST ==========\n")

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

    print("Sending business question to Qwen...\n")

    result = service.analyze(
        question=question,
        business_context=business_context
    )

    print("========== STRUCTURED AI ANALYSIS ==========\n")

    print(result.model_dump_json(indent=4))


if __name__ == "__main__":
    main()