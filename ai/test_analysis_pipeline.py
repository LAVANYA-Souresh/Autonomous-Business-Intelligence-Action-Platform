from ai.llm_client import LLMClient
from ai.analysis_service import BusinessAnalysisService


class MockLLMClient(LLMClient):
    """
    Temporary test LLM.

    This simulates an LLM response so we can verify the
    complete analysis pipeline before connecting the
    real local model.
    """

    def generate(self, prompt: str) -> str:

        return """
{
    "summary": "Revenue increased during May 2025 while the return rate also increased.",

    "observed_facts": [
        "May 2025 revenue was 115381593.0.",
        "Return rate increased from 9.46% to 10.13%.",
        "Support tickets decreased by 12."
    ],

    "supporting_evidence": [
        "Revenue for May 2025 was 115381593.0.",
        "Return rate increased by 0.67 percentage points.",
        "Support tickets changed from 158 to 146."
    ],

    "possible_explanations": [
        "Higher sales activity may have contributed to the revenue increase.",
        "The available evidence does not establish the cause of the return-rate change."
    ],

    "uncertainty": [
        "The available evidence does not establish causal relationships."
    ],

    "recommended_next_investigation": [
        "Investigate revenue changes by product.",
        "Examine return reasons by product.",
        "Investigate regional revenue changes."
    ],

    "claims": [
        {
            "entity": "Phone X1",
            "metric": "revenue",
            "direction": "increased",
            "value": 32.96,
            "unit": "percentage"
        },
        {
            "entity": "Phone X1",
            "metric": "return",
            "direction": "decreased",
            "value": -2,
            "unit": "count"
        }
    ]
}
"""


def main():

    print("\n========== END-TO-END ANALYSIS TEST ==========\n")

    llm_client = MockLLMClient()

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

    The evidence does not establish causal relationships.
    """

    result = service.analyze(
        question=question,
        business_context=business_context
    )

    print("Analysis completed successfully.\n")

    print(result.model_dump_json(indent=4))


if __name__ == "__main__":
    main()