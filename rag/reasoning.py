
from typing import Optional

from rag.rag_engine import RAGRetriever
from ai.llm_client import LLMClient


class BusinessReasoningError(Exception):
    """Raised when business reasoning fails."""
    pass


class BusinessReasoningEngine:
    """
    Combines trusted SQL evidence with relevant business knowledge.

    SQL evidence is authoritative for numerical facts.
    RAG provides business definitions, policies, and guidelines.
    LLM is used for reasoning and explanation.

    Numerical verification is handled separately by:
        ai.numerical_verifier.NumericalVerifier
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None
    ):
        print("\nInitializing reasoning engine...")

        self.retriever = RAGRetriever()
        self.llm_client = llm_client

    def build_prompt(
        self,
        question: str,
        sql_evidence: str,
        top_k: int = 3
    ) -> str:

        if not question or not question.strip():
            raise BusinessReasoningError(
                "Business question cannot be empty."
            )

        if not sql_evidence or not sql_evidence.strip():
            raise BusinessReasoningError(
                "SQL evidence is required for reasoning."
            )

        # --------------------------------------
        # Retrieve relevant business knowledge
        # --------------------------------------

        knowledge_results = self.retriever.retrieve(
            question,
            top_k=top_k
        )

        knowledge_sections = []

        for result in knowledge_results:
            knowledge_sections.append(
                f"SOURCE: {result['source']}\n"
                f"{result['content']}"
            )

        knowledge_context = (
            "\n\n---\n\n".join(
                knowledge_sections
            )
        )

        # --------------------------------------
        # Reasoning instructions
        # --------------------------------------

        instructions = """
You are an AI Business Intelligence Analyst
for NovaMart.

Analyze the user's business question using
trusted database evidence and relevant business
knowledge.

IMPORTANT:

1. The database evidence is authoritative.

2. Use the database evidence to determine all
   numerical facts.

3. Do not invent numerical values.

4. Do not calculate new numerical values unless
   the calculation is explicitly supported by
   the trusted evidence.

5. Do not modify, round, scale, convert, or
   reinterpret database numbers.

6. Do not invent metrics, events, or business facts.

7. Business knowledge is only supporting context.
   It cannot override database evidence.

8. Clearly distinguish observed facts from
   possible explanations.

9. Do not make causal claims unless the evidence
   directly supports causation.

10. If the evidence directly answers the question,
    answer directly.

11. If the evidence is insufficient, say so.

12. Keep the response concise and focused on
    business interpretation.

13. Currency and number formatting:
- This business dataset uses Indian Rupees (INR).
- When presenting monetary values, use the ₹ symbol.
- Do not use $, USD, or other currency symbols.
- Preserve the exact database value; only change its presentation format.
- Use Indian number formatting where practical, for example ₹13,30,18,981.00.

Response structure:

Direct Answer:

<short answer>

Supporting Evidence:

<short explanation based only on the evidence>
"""

        # --------------------------------------
        # Build final reasoning prompt
        # --------------------------------------

        prompt = f"""
{instructions}

====================
USER QUESTION
====================

{question}

====================
RELEVANT BUSINESS KNOWLEDGE
====================

{knowledge_context}

====================
TRUSTED DATABASE EVIDENCE
====================

{sql_evidence}

====================
END OF CONTEXT
====================

Now analyze the user's question.
"""

        return prompt

    def reason(
        self,
        question: str,
        sql_evidence: str,
        top_k: int = 3
    ) -> str:
        """
        Generate an LLM reasoning response.

        Numerical verification is intentionally NOT performed
        here.

        The canonical numerical verification is performed by:

            ai.numerical_verifier.NumericalVerifier

        This keeps reasoning and verification as separate
        responsibilities.
        """

        if self.llm_client is None:
            raise BusinessReasoningError(
                "LLM client is required for reasoning."
            )

        prompt = self.build_prompt(
            question=question,
            sql_evidence=sql_evidence,
            top_k=top_k
        )

        response = self.llm_client.generate(
            prompt
        )

        if not response or not response.strip():
            raise BusinessReasoningError(
                "LLM returned an empty reasoning response."
            )

        return response.strip()


if __name__ == "__main__":

    from ai.llm_client import OllamaLLMClient

    print(
        "\n========== REASONING ENGINE TEST ==========\n"
    )

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    engine = BusinessReasoningEngine(
        llm_client=llm_client
    )

    test_evidence = """
Revenue for May 2025:

133018981.00
"""

    print(
        "\n========== PROMPT TEST ==========\n"
    )

    prompt = engine.build_prompt(
        question="What was the revenue in May 2025?",
        sql_evidence=test_evidence
    )

    print(prompt)

    print(
        "\n========== LLM REASONING TEST ==========\n"
    )

    try:

        answer = engine.reason(
            question="What was the revenue in May 2025?",
            sql_evidence=test_evidence
        )

        print(
            "\nREASONING STATUS: PASSED"
        )

        print(
            "\nGenerated Answer:\n"
        )

        print(answer)

    except BusinessReasoningError as error:

        print(
            "\nREASONING STATUS: FAILED"
        )

        print(
            f"\nReason: {error}"
        )

