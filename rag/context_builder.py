
from rag.rag_engine import RAGRetriever
from rag.evidence_loader import (
    load_investigation_evidence
)


class BusinessContextBuilder:

    def __init__(self):

        print(
            "\nInitializing business context builder..."
        )

        self.retriever = RAGRetriever()

        self.evidence = (
            load_investigation_evidence()
        )

        print(
            "Business evidence loaded."
        )

    def build_context(
        self,
        question,
        top_k=3
    ):

        # --------------------------------------
        # Retrieve relevant business knowledge
        # --------------------------------------

        knowledge_results = (
            self.retriever.retrieve(
                question,
                top_k=top_k
            )
        )

        # --------------------------------------
        # Build knowledge context
        # --------------------------------------

        knowledge_context = []

        for result in knowledge_results:

            knowledge_context.append({

                "source": result["source"],

                "content": result["content"],

                "distance": result["distance"]
            })

        # --------------------------------------
        # Build evidence context
        # --------------------------------------

        evidence_context = {

            "anomaly": self.evidence[
                "anomaly"
            ],

            "return_rate": self.evidence[
                "return_rate"
            ],

            "support_tickets": self.evidence[
                "support_tickets"
            ],

            "product_evidence": self.evidence[
                "product_evidence"
            ],

            "regional_evidence": self.evidence[
                "regional_evidence"
            ]
        }

        # --------------------------------------
        # Combine everything
        # --------------------------------------

        context = {

            "question": question,

            "knowledge": knowledge_context,

            "business_evidence": evidence_context
        }

        return context


if __name__ == "__main__":

    print(
        "\n========== CONTEXT BUILDER TEST ==========\n"
    )

    builder = BusinessContextBuilder()

    question = (
        "What happened to the business "
        "in May 2025?"
    )

    context = builder.build_context(
        question
    )

    print("\nQUESTION")
    print(
        context["question"]
    )

    print("\nRELEVANT KNOWLEDGE")

    for item in context["knowledge"]:

        print("\n--------------------")

        print(
            f"Source: {item['source']}"
        )

        print(
            f"Distance: "
            f"{item['distance']:.4f}"
        )

        print(
            item["content"]
        )

    print("\nBUSINESS EVIDENCE")

    print(
        "\nAnomaly:"
    )

    print(
        context[
            "business_evidence"
        ]["anomaly"]
    )

    print(
        "\nReturn Rate:"
    )

    print(
        context[
            "business_evidence"
        ]["return_rate"]
    )

    print(
        "\nSupport Tickets:"
    )

    print(
        context[
            "business_evidence"
        ]["support_tickets"]
    )

    print(
        "\nProduct Evidence:"
    )

    print(
        f"{len(context['business_evidence']['product_evidence'])} "
        "product records"
    )

    print(
        "\nRegional Evidence:"
    )

    print(
        f"{len(context['business_evidence']['regional_evidence'])} "
        "regional records"
    )

