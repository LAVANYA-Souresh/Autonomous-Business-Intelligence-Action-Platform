import json
from typing import Any


class AnalysisPlanningError(Exception):
    """Raised when the analysis planner cannot create a valid plan."""
    pass


class AnalysisPlanner:
    """
    Converts a natural-language business question into a structured
    analytical plan.

    The planner does not execute SQL.
    It only determines what type of analysis is required.
    """

    ALLOWED_TYPES = {
        "simple_factual",
        "comparison",
        "trend",
        "diagnostic",
    }

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def plan(self, question: str) -> dict[str, Any]:

        if not question or not question.strip():
            raise AnalysisPlanningError(
                "Business question is empty."
            )

        prompt = f"""
You are an analysis planning engine for NovaMart,
an e-commerce business intelligence system.

Your job is to classify the user's business question
and determine what kind of evidence is required.

USER QUESTION:
{question}

Choose exactly ONE analysis_type:

1. simple_factual
   Use when the question asks for one direct database fact,
   such as:
   - Which region generated the most revenue?
   - What was the total revenue?
   - Which product had the highest sales?

2. comparison
   Use when the question asks to compare two or more
   periods, regions, products, or groups.

3. trend
   Use when the question asks how a metric changed
   across multiple time periods.

4. diagnostic
   Use when the question asks why something happened,
   what may be driving a change, or what factors should
   be investigated.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "analysis_type": "simple_factual",
  "primary_metric": "revenue",
  "dimensions": ["region"],
  "time_periods": ["May 2025"],
  "requires_multiple_queries": false
}}

Rules:

- analysis_type must be one of:
  simple_factual, comparison, trend, diagnostic

- primary_metric must be a concise business metric.

- dimensions must contain the business dimensions
  needed to answer the question.

- time_periods must contain the relevant periods.

- requires_multiple_queries must be true when answering
  the question requires multiple independent database queries.

- Do not invent business metrics.

- Do not answer the user's question.

- Do not generate SQL.

- Return JSON only.
"""

        raw_response = self.llm_client.generate(
            prompt,
            response_format="json"
        )

        plan = self._parse_response(raw_response)

        self._validate_plan(plan)

        return plan

    def _parse_response(self, response: str) -> dict[str, Any]:

        if not response or not response.strip():
            raise AnalysisPlanningError(
                "Analysis planner returned an empty response."
            )

        cleaned = response.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "")
            cleaned = cleaned.strip()

        try:
            plan = json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise AnalysisPlanningError(
                f"Planner returned invalid JSON: {error}"
            ) from error

        if not isinstance(plan, dict):
            raise AnalysisPlanningError(
                "Planner response must be a JSON object."
            )

        return plan

    def _validate_plan(self, plan: dict[str, Any]):

        required_fields = [
            "analysis_type",
            "primary_metric",
            "dimensions",
            "time_periods",
            "requires_multiple_queries",
        ]

        for field in required_fields:
            if field not in plan:
                raise AnalysisPlanningError(
                    f"Planner output is missing required field: {field}"
                )

        if plan["analysis_type"] not in self.ALLOWED_TYPES:
            raise AnalysisPlanningError(
                f"Invalid analysis type: {plan['analysis_type']}"
            )

        if not isinstance(plan["primary_metric"], str):
            raise AnalysisPlanningError(
                "primary_metric must be a string."
            )

        if not isinstance(plan["dimensions"], list):
            raise AnalysisPlanningError(
                "dimensions must be a list."
            )

        if not isinstance(plan["time_periods"], list):
            raise AnalysisPlanningError(
                "time_periods must be a list."
            )

        if not isinstance(
            plan["requires_multiple_queries"],
            bool
        ):
            raise AnalysisPlanningError(
                "requires_multiple_queries must be boolean."
            )


if __name__ == "__main__":

    from ai.llm_client import OllamaLLMClient

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    planner = AnalysisPlanner(
        llm_client=llm_client
    )

    questions = [
        "Which region generated the most revenue in May 2025?",
        "How did revenue change between April and May 2025?",
        "Why did revenue change in May 2025?"
    ]

    for question in questions:

        print("\n========================================")
        print("QUESTION:")
        print(question)

        try:
            result = planner.plan(question)

            print("\nANALYSIS PLAN:")
            print(json.dumps(
                result,
                indent=2
            ))

        except AnalysisPlanningError as error:

            print("\nPLANNING FAILED:")
            print(error)