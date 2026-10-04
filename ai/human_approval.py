
from datetime import datetime, timezone
from typing import Any


class HumanApprovalError(Exception):
    """Raised when a human approval decision cannot be processed."""
    pass


class HumanApprovalGate:
    """
    Controls human approval of AI-generated recommendations.

    The AI recommendation can only become actionable after
    an explicit human decision.

    Supported decisions:
        - APPROVE
        - REJECT
    """

    def create_pending_approval(
        self,
        recommendation: dict[str, Any]
    ) -> dict[str, Any]:

        if not recommendation:
            raise HumanApprovalError(
                "Recommendation is required."
            )

        if recommendation.get(
            "recommendation_status"
        ) != "READY_FOR_REVIEW":

            raise HumanApprovalError(
                "Only recommendations with "
                "READY_FOR_REVIEW status can enter "
                "the human approval process."
            )

        return {
            "approval_status": "PENDING",
            "approved_by": None,
            "approved_at": None,
            "decision_reason": None,
            "recommendation": recommendation
        }

    def approve(
        self,
        approval: dict[str, Any],
        approved_by: str,
        decision_reason: str = ""
    ) -> dict[str, Any]:

        if not approval:
            raise HumanApprovalError(
                "Approval record is required."
            )

        if approval.get("approval_status") != "PENDING":
            raise HumanApprovalError(
                "Only PENDING approvals can be approved."
            )

        if not approved_by or not approved_by.strip():
            raise HumanApprovalError(
                "approved_by is required."
            )

        approval["approval_status"] = "APPROVED"
        approval["approved_by"] = approved_by.strip()
        approval["approved_at"] = (
            datetime.now(timezone.utc).isoformat()
        )
        approval["decision_reason"] = (
            decision_reason.strip()
            if decision_reason
            else "Human approved the recommendation."
        )

        return approval

    def reject(
        self,
        approval: dict[str, Any],
        approved_by: str,
        decision_reason: str = ""
    ) -> dict[str, Any]:

        if not approval:
            raise HumanApprovalError(
                "Approval record is required."
            )

        if approval.get("approval_status") != "PENDING":
            raise HumanApprovalError(
                "Only PENDING approvals can be rejected."
            )

        if not approved_by or not approved_by.strip():
            raise HumanApprovalError(
                "approved_by is required."
            )

        approval["approval_status"] = "REJECTED"
        approval["approved_by"] = approved_by.strip()
        approval["approved_at"] = (
            datetime.now(timezone.utc).isoformat()
        )
        approval["decision_reason"] = (
            decision_reason.strip()
            if decision_reason
            else "Human rejected the recommendation."
        )

        return approval


# =============================================================
# TESTS
# =============================================================

if __name__ == "__main__":

    gate = HumanApprovalGate()

    recommendation = {
        "recommendation_status": "READY_FOR_REVIEW",
        "workflow": "simple_factual",
        "question": "What was the revenue in May 2025?",
        "observed_fact": (
            "Total revenue in the analyzed period "
            "was ₹13,30,18,981.00."
        ),
        "business_implication": (
            "The result provides a verified baseline "
            "for the analyzed period."
        ),
        "recommended_action": (
            "Use this verified revenue baseline together "
            "with regional, product, return, and operational "
            "evidence before making business decisions."
        ),
        "reason": (
            "A single overall revenue figure establishes "
            "a baseline but does not explain the drivers "
            "behind performance."
        ),
        "evidence_confidence": "HIGH",
        "recommendation_confidence": "MEDIUM",
        "human_approval_required": True,
        "action_executed": False,
        "source": "verified_database_evidence"
    }

    print("\n========================================")
    print("HUMAN APPROVAL GATE TEST")
    print("========================================")

    # ---------------------------------------------------------
    # Test 1: Create pending approval
    # ---------------------------------------------------------

    print("\nCreating pending approval...")

    approval = gate.create_pending_approval(
        recommendation
    )

    print(approval)

    # ---------------------------------------------------------
    # Test 2: Approve recommendation
    # ---------------------------------------------------------

    print("\nApproving recommendation...")

    approved = gate.approve(
        approval,
        approved_by="Human Reviewer",
        decision_reason=(
            "Recommendation reviewed and approved "
            "for the next workflow stage."
        )
    )

    print(approved)

    # ---------------------------------------------------------
    # Test 3: Verify approved status
    # ---------------------------------------------------------

    print("\nFinal approval status:")

    print(
        approved["approval_status"]
    )

    print(
        "\nHuman approval gate test completed."
    )

