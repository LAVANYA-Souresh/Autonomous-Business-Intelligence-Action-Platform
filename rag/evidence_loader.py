
import json
from pathlib import Path


EVIDENCE_FILE = Path(
    "analytics/investigation_output.json"
)


def load_investigation_evidence():

    if not EVIDENCE_FILE.exists():

        raise FileNotFoundError(
            f"Evidence file not found: {EVIDENCE_FILE}"
        )

    with open(
        EVIDENCE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        evidence = json.load(file)

    return evidence


def summarize_evidence(evidence):

    anomaly = evidence["anomaly"]

    summary = {

        "anomaly_month": anomaly["month"],

        "anomaly_revenue": anomaly["revenue"],

        "return_rate_current": (
            evidence["return_rate"]["current"]
        ),

        "return_rate_previous": (
            evidence["return_rate"]["previous"]
        ),

        "return_rate_change": (
            evidence["return_rate"][
                "change_percentage_points"
            ]
        ),

        "support_tickets_current": (
            evidence["support_tickets"]["current"]
        ),

        "support_tickets_previous": (
            evidence["support_tickets"]["previous"]
        ),

        "support_ticket_change": (
            evidence["support_tickets"]["change"]
        )
    }

    return summary


if __name__ == "__main__":

    print(
        "\n========== EVIDENCE LOADER TEST ==========\n"
    )

    evidence = load_investigation_evidence()

    print("Evidence loaded successfully.")

    summary = summarize_evidence(
        evidence
    )

    print("\nEvidence summary:")

    for key, value in summary.items():

        print(
            f"{key}: {value}"
        )

