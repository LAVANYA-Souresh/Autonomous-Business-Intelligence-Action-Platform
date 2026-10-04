# analytics/investigation_report.py

import json


def build_investigation_report(
    anomaly_month,
    anomaly_revenue,
    product_evidence,
    regional_evidence,
    return_rate_current,
    return_rate_previous,
    support_ticket_current,
    support_ticket_previous
):

    report = {
        "anomaly": {
            "month": anomaly_month.strftime("%Y-%m"),
            "revenue": float(anomaly_revenue)
        },

        "investigation_summary": {
        "type": "evidence_based",
        "causal_claims": False,
        "note": (
            "The investigation identifies correlations and "
            "changes in business metrics. It does not establish "
            "causal relationships."
        )
    },

        "product_evidence": [],

        "regional_evidence": [],

        "return_rate": {
            "current": float(return_rate_current),
            "previous": float(return_rate_previous),
            "change_percentage_points": float(
                return_rate_current
                - return_rate_previous
            )
        },

        "support_tickets": {
            "current": int(support_ticket_current),
            "previous": int(support_ticket_previous),
            "change": int(
                support_ticket_current
                - support_ticket_previous
            )
        }
    }

    # -----------------------------
    # Product evidence
    # -----------------------------

    for _, row in product_evidence.iterrows():

        report["product_evidence"].append({

            "product": row["product"],

            "revenue_change_percentage": float(
                row["revenue_change_percentage"]
            ),

            "return_change": int(
                row["return_change"]
            ),

            "support_ticket_change": int(
                row["ticket_change"]
            ),

            "complaint_change": int(
                row["complaint_change"]
            ),

            "refund_change": int(
                row["refund_change"]
            )
        })

    # -----------------------------
    # Regional evidence
    # -----------------------------

    for _, row in regional_evidence.iterrows():

        report["regional_evidence"].append({

            "region": row["region"],

            "revenue_change_percentage": float(
                row["change_percentage"]
            )
        })

    return report


def save_report(report):

    output_file = (
        "analytics/investigation_output.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )

    print(
        f"\nInvestigation report saved to: "
        f"{output_file}"
    )