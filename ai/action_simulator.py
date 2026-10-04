from datetime import datetime, timezone
from typing import Any


class ActionSimulationError(Exception):
    """Raised when an action cannot be simulated."""
    pass


class ActionSimulator:
    """
    Simulates business actions after human approval.

    This component does not modify the real database,
    send real messages, or perform real operational actions.

    It only records what action would have been executed
    after an explicit human approval.
    """

    def simulate(
        self,
        approval: dict[str, Any]
    ) -> dict[str, Any]:

        # --------------------------------------
        # Validate approval record
        # --------------------------------------

        if not approval:
            raise ActionSimulationError(
                "Approval record is required."
            )

        # --------------------------------------
        # Require explicit human approval
        # --------------------------------------

        if approval.get(
            "approval_status"
        ) != "APPROVED":

            raise ActionSimulationError(
                "Action cannot be simulated unless "
                "the recommendation has been approved."
            )

        # --------------------------------------
        # Extract recommendation
        # --------------------------------------

        recommendation = approval.get(
            "recommendation"
        )

        if not recommendation:
            raise ActionSimulationError(
                "Recommendation is missing from approval record."
            )

        # --------------------------------------
        # Extract recommended action
        # --------------------------------------

        recommended_action = recommendation.get(
            "recommended_action"
        )

        if not recommended_action:
            raise ActionSimulationError(
                "Recommended action is missing."
            )

        # --------------------------------------
        # Create simulated action
        # --------------------------------------

        simulated_at = (
            datetime.now(timezone.utc).isoformat()
        )

        return {
            "action_status": "SIMULATED",
            "action_type": "BUSINESS_OPERATION",
            "simulated_action": recommended_action,
            "simulated_at": simulated_at,
            "approved_by": approval.get(
                "approved_by"
            ),
            "approval_status": approval.get(
                "approval_status"
            ),
            "real_action_executed": False,
            "simulation_only": True,
            "source": "human_approved_recommendation"
        }


if __name__ == "__main__":

    print(
        "\n========== ACTION SIMULATOR TEST ==========\n"
    )

    simulator = ActionSimulator()

    # --------------------------------------
    # Test 1: Reject unapproved action
    # --------------------------------------

    print(
        "Testing unapproved recommendation..."
    )

    pending_approval = {
        "approval_status": "PENDING",
        "approved_by": None,
        "approved_at": None,
        "decision_reason": None,
        "recommendation": {
            "recommendation_status": "READY_FOR_REVIEW",
            "recommended_action": (
                "Review regional performance."
            )
        }
    }

    try:

        simulator.simulate(
            pending_approval
        )

        print(
            "ERROR: Unapproved action was accepted."
        )

    except ActionSimulationError as error:

        print(
            f"Correctly blocked: {error}"
        )

    # --------------------------------------
    # Test 2: Simulate approved action
    # --------------------------------------

    print(
        "\nTesting approved recommendation..."
    )

    approved_approval = {
        "approval_status": "APPROVED",
        "approved_by": "Human Reviewer",
        "approved_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "decision_reason": (
            "Recommendation reviewed and approved."
        ),
        "recommendation": {
            "recommendation_status": "READY_FOR_REVIEW",
            "recommended_action": (
                "Review regional performance."
            )
        }
    }

    result = simulator.simulate(
        approved_approval
    )

    print(
        "\nSimulated Action:"
    )

    print(result)

    print(
        "\nAction status:"
    )

    print(
        result["action_status"]
    )

    print(
        "\nReal action executed:"
    )

    print(
        result["real_action_executed"]
    )

    print(
        "\nSimulation only:"
    )

    print(
        result["simulation_only"]
    )

    print(
        "\nAction simulator test completed."
    )