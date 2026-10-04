
from rag.evidence_loader import (
    load_investigation_evidence
)


def format_evidence(evidence):

    anomaly = evidence["anomaly"]

    return_rate = evidence["return_rate"]

    support = evidence["support_tickets"]

    lines = []

    # --------------------------------------
    # Anomaly
    # --------------------------------------

    lines.append(
        "BUSINESS ANOMALY"
    )

    lines.append(
        f"Period: {anomaly['month']}"
    )

    lines.append(
        f"Revenue: {anomaly['revenue']:,.2f}"
    )

    # --------------------------------------
    # Return rate
    # --------------------------------------

    lines.append("")

    lines.append(
        "RETURN RATE"
    )

    lines.append(
        f"Current period: "
        f"{return_rate['current']:.2f}%"
    )

    lines.append(
        f"Previous period: "
        f"{return_rate['previous']:.2f}%"
    )

    lines.append(
        f"Change: "
        f"{return_rate['change_percentage_points']:+.2f} "
        f"percentage points"
    )

    # --------------------------------------
    # Support tickets
    # --------------------------------------

    lines.append("")

    lines.append(
        "SUPPORT TICKETS"
    )

    lines.append(
        f"Current period: "
        f"{support['current']}"
    )

    lines.append(
        f"Previous period: "
        f"{support['previous']}"
    )

    lines.append(
        f"Change: "
        f"{support['change']:+d}"
    )

    # --------------------------------------
    # Product evidence
    # --------------------------------------

    lines.append("")

    lines.append(
        "PRODUCT EVIDENCE"
    )

    for product in evidence[
        "product_evidence"
    ]:

        lines.append(
            f"- {product['product']}: "
            f"revenue change "
            f"{product['revenue_change_percentage']:+.2f}%, "
            f"return change "
            f"{product['return_change']:+d}, "
            f"support ticket change "
            f"{product['support_ticket_change']:+d}, "
            f"complaint change "
            f"{product['complaint_change']:+d}, "
            f"refund change "
            f"{product['refund_change']:+d}"
        )

    # --------------------------------------
    # Regional evidence
    # --------------------------------------

    lines.append("")

    lines.append(
        "REGIONAL EVIDENCE"
    )

    for region in evidence[
        "regional_evidence"
    ]:

        lines.append(
            f"- {region['region']}: "
            f"revenue change "
            f"{region['revenue_change_percentage']:+.2f}%"
        )

    return "\n".join(lines)


if __name__ == "__main__":

    print(
        "\n========== EVIDENCE FORMATTER TEST ==========\n"
    )

    evidence = load_investigation_evidence()

    formatted = format_evidence(
        evidence
    )

    print(formatted)

