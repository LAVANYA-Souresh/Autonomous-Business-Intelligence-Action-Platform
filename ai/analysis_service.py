import json

from ai.llm_client import LLMClient
from ai.response_schema import BusinessAnalysis
from ai.prompts import build_analysis_prompt


class BusinessAnalysisService:
    """
    Connects the business reasoning layer with an LLM.

    The service depends on the abstract LLMClient rather than
    directly depending on Ollama or any specific model.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def analyze(
        self,
        question: str,
        business_context: str,
        feedback: str = ""
    ) -> BusinessAnalysis:

        prompt = build_analysis_prompt(
            question=question,
            business_context=business_context
        )

        if feedback:
            prompt += """

IMPORTANT: The following is validation feedback about your previous
response. It is NOT business evidence.

Use it only to correct your previous response.

VALIDATION FEEDBACK:
""" + feedback + """

Do NOT copy validation feedback into the business evidence,
observed facts, supporting evidence, or claims.

Return the complete corrected analysis as JSON.
"""

        raw_response = self.llm_client.generate(prompt)

        try:
            parsed_response = json.loads(raw_response)
        except json.JSONDecodeError as error:
            raise ValueError(
                "LLM returned invalid JSON."
            ) from error

        return BusinessAnalysis.model_validate(parsed_response)


if __name__ == "__main__":
    print("\n========== ANALYSIS SERVICE TEST ==========\n")

    print("Analysis service module loaded successfully.")
    print("LLM provider is injected through LLMClient.")