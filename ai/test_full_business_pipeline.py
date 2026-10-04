
from ai.llm_client import OllamaLLMClient
from ai.nl_to_sql_service import NLToSQLService
from ai.sql_evidence import SQLEvidenceFormatter
from ai.numerical_verifier import NumericalVerifier
from ai.claim_verifier import ClaimVerifier
from rag.reasoning import BusinessReasoningEngine


def main():

    print("\n========== FULL BUSINESS AI PIPELINE ==========\n")

    # --------------------------------------------------
    # INITIALIZE LLM
    # --------------------------------------------------

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    # --------------------------------------------------
    # INITIALIZE SQL SERVICE
    # --------------------------------------------------

    sql_service = NLToSQLService(
        llm_client=llm_client
    )

    question = (
        "Which region generated the most revenue in May 2025?"
    )

    # ==================================================
    # STAGE 1: NL-TO-SQL
    # ==================================================

    print("\n========== STAGE 1: NL-TO-SQL ==========\n")

    sql_result = sql_service.ask(
        question
    )

    print(
        "\nSQL pipeline completed successfully."
    )

    # ==================================================
    # STAGE 2: SQL EVIDENCE
    # ==================================================

    print("\n========== STAGE 2: SQL EVIDENCE ==========\n")

    formatter = SQLEvidenceFormatter()

    sql_evidence = formatter.format(
        sql_result
    )

    print(sql_evidence)

    # ==================================================
    # STAGE 3: REASONING
    # ==================================================

    print("\n========== STAGE 3: REASONING ==========\n")

    reasoning_engine = BusinessReasoningEngine()

    reasoning_prompt = reasoning_engine.build_prompt(
        question=question,
        sql_evidence=sql_evidence
    )

    print(
        "\nReasoning prompt created successfully."
    )

    # ==================================================
    # STAGE 4: LLM REASONING
    # ==================================================

    print("\n========== STAGE 4: LLM REASONING ==========\n")

    print(
        "Sending reasoning request to Ollama..."
    )

    final_answer = llm_client.generate(
        reasoning_prompt
    )

    print(
        "\n========== RAW LLM ANSWER ==========\n"
    )

    print(final_answer)

    # ==================================================
    # STAGE 5: NUMERICAL VERIFICATION
    # ==================================================

    print(
        "\n========== STAGE 5: NUMERICAL VERIFICATION ==========\n"
    )

    numerical_verifier = NumericalVerifier()

    numerical_result = numerical_verifier.verify(
        answer=final_answer,
        sql_results=sql_result["results"]
    )

    print("\nNumerical verification result:")

    print(numerical_result)

    # ==================================================
    # STAGE 6: CLAIM VERIFICATION
    # ==================================================

    print(
        "\n========== STAGE 6: CLAIM VERIFICATION ==========\n"
    )

    claim_verifier = ClaimVerifier()

    claim_result = claim_verifier.verify(
        answer=final_answer,
        sql_results=sql_result["results"]
    )

    print("\nClaim verification result:")

    print(claim_result)

    # ==================================================
    # CHECK WHETHER CORRECTION IS REQUIRED
    # ==================================================

    numerical_failed = (
        numerical_result["status"] == "FAILED"
    )

    claims_failed = (
        claim_result["status"] == "FAILED"
    )

    # ==================================================
    # STAGE 7: ANSWER CORRECTION
    # ==================================================

    if numerical_failed or claims_failed:

        print(
            "\n========== STAGE 7: ANSWER CORRECTION ==========\n"
        )

        correction_prompt = f"""
You are correcting an AI-generated business intelligence answer.

USER QUESTION:

{question}

TRUSTED DATABASE EVIDENCE:

{sql_evidence}

PREVIOUS LLM ANSWER:

{final_answer}

NUMERICAL VERIFICATION RESULT:

{numerical_result}

CLAIM VERIFICATION RESULT:

{claim_result}

Your previous answer failed one or more verification checks.

Correct the answer using ONLY the trusted database evidence.

IMPORTANT RULES:

1. Use exact numerical values from the database evidence.
2. Never change, round, multiply, divide, or reinterpret database values.
3. Do not invent business metrics.
4. Do not invent causes or explanations.
5. Do not claim that one business metric caused another unless the evidence directly proves it.
6. Do not mention metrics that are not present in the trusted database evidence.
7. Clearly distinguish facts from uncertainty.
8. If the evidence only answers the user's question, give only the supported answer.
9. Keep the answer concise.
10. Answer the original user question directly.
11. Return normal natural-language text.
12. Do not return JSON.
13. Do not return markdown code blocks.

The corrected answer must be completely supported by the trusted database evidence.
"""

        print(
            "Sending correction request to Ollama..."
        )

        corrected_answer = llm_client.generate(
            correction_prompt
        )

        print(
            "\n========== CORRECTED LLM ANSWER ==========\n"
        )

        print(corrected_answer)

        # ==================================================
        # STAGE 8: RE-VERIFICATION
        # ==================================================

        print(
            "\n========== STAGE 8: RE-VERIFICATION ==========\n"
        )

        second_numerical_result = (
            numerical_verifier.verify(
                answer=corrected_answer,
                sql_results=sql_result["results"]
            )
        )

        second_claim_result = (
            claim_verifier.verify(
                answer=corrected_answer,
                sql_results=sql_result["results"]
            )
        )

        print(
            "\nSecond numerical verification:"
        )

        print(
            second_numerical_result
        )

        print(
            "\nSecond claim verification:"
        )

        print(
            second_claim_result
        )

        # ==================================================
        # FINAL VERIFICATION DECISION
        # ==================================================

        if (
            second_numerical_result["status"] == "PASSED"
            and
            second_claim_result["status"] == "PASSED"
        ):

            print(
                "\nFINAL ANSWER STATUS: VERIFIED"
            )

            print(
                "\n========== VERIFIED BUSINESS ANSWER ==========\n"
            )

            print(
                corrected_answer
            )

        else:

            print(
                "\nFINAL ANSWER STATUS: REJECTED"
            )

            print(
                "The corrected answer still contains "
                "numerical or unsupported claims."
            )

        return

    # ==================================================
    # ORIGINAL ANSWER PASSED BOTH CHECKS
    # ==================================================

    print(
        "\nFINAL ANSWER STATUS: VERIFIED"
    )

    print(
        "\n========== VERIFIED BUSINESS ANSWER ==========\n"
    )

    print(
        final_answer
    )


if __name__ == "__main__":

    main()

