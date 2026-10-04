import pytest

from ai.human_approval import (
    HumanApprovalError,
    HumanApprovalGate
)

from ai.action_simulator import (
    ActionSimulationError,
    ActionSimulator
)


def create_recommendation():
    return {
        "recommendation_status": "READY_FOR_REVIEW",
        "workflow": "simple_factual",
        "question": "What was the revenue in May 2025?",
        "observed_fact": (
            "Total revenue was ₹13,30,18,981.00."
        ),
        "business_implication": (
            "The result provides a verified baseline."
        ),
        "recommended_action": (
            "Review regional and product performance."
        ),
        "reason": (
            "A single revenue figure does not explain "
            "the drivers behind performance."
        ),
        "evidence_confidence": "HIGH",
        "recommendation_confidence": "MEDIUM",
        "human_approval_required": True,
        "action_executed": False,
        "source": "verified_database_evidence"
    }


def test_create_pending_approval():
    gate = HumanApprovalGate()

    recommendation = create_recommendation()

    approval = gate.create_pending_approval(
        recommendation
    )

    assert approval["approval_status"] == "PENDING"
    assert approval["approved_by"] is None
    assert approval["approved_at"] is None
    assert approval["recommendation"] == recommendation


def test_approve_recommendation():
    gate = HumanApprovalGate()

    recommendation = create_recommendation()

    approval = gate.create_pending_approval(
        recommendation
    )

    approved = gate.approve(
        approval=approval,
        approved_by="Human Reviewer",
        decision_reason="Approved after review."
    )

    assert approved["approval_status"] == "APPROVED"
    assert approved["approved_by"] == "Human Reviewer"
    assert approved["approved_at"] is not None
    assert approved["decision_reason"] == (
        "Approved after review."
    )


def test_reject_recommendation():
    gate = HumanApprovalGate()

    recommendation = create_recommendation()

    approval = gate.create_pending_approval(
        recommendation
    )

    rejected = gate.reject(
        approval=approval,
        approved_by="Human Reviewer",
        decision_reason="Rejected after review."
    )

    assert rejected["approval_status"] == "REJECTED"
    assert rejected["approved_by"] == "Human Reviewer"
    assert rejected["approved_at"] is not None
    assert rejected["decision_reason"] == (
        "Rejected after review."
    )


def test_cannot_approve_without_reviewer():
    gate = HumanApprovalGate()

    recommendation = create_recommendation()

    approval = gate.create_pending_approval(
        recommendation
    )

    with pytest.raises(HumanApprovalError):
        gate.approve(
            approval=approval,
            approved_by=""
        )


def test_action_blocked_without_approval():
    gate = HumanApprovalGate()
    simulator = ActionSimulator()

    recommendation = create_recommendation()

    approval = gate.create_pending_approval(
        recommendation
    )

    with pytest.raises(ActionSimulationError):
        simulator.simulate(approval)


def test_action_blocked_after_rejection():
    gate = HumanApprovalGate()
    simulator = ActionSimulator()

    recommendation = create_recommendation()

    approval = gate.create_pending_approval(
        recommendation
    )

    rejected = gate.reject(
        approval=approval,
        approved_by="Human Reviewer"
    )

    with pytest.raises(ActionSimulationError):
        simulator.simulate(rejected)


def test_action_allowed_after_approval():
    gate = HumanApprovalGate()
    simulator = ActionSimulator()

    recommendation = create_recommendation()

    approval = gate.create_pending_approval(
        recommendation
    )

    approved = gate.approve(
        approval=approval,
        approved_by="Human Reviewer"
    )

    result = simulator.simulate(
        approved
    )

    assert result["action_status"] == "SIMULATED"
    assert result["simulation_only"] is True
    assert result["real_action_executed"] is False
    assert result["approved_by"] == "Human Reviewer"
    assert result["approval_status"] == "APPROVED"


def test_simulated_action_contains_recommended_action():
    gate = HumanApprovalGate()
    simulator = ActionSimulator()

    recommendation = create_recommendation()

    approval = gate.create_pending_approval(
        recommendation
    )

    approved = gate.approve(
        approval=approval,
        approved_by="Human Reviewer"
    )

    result = simulator.simulate(
        approved
    )

    assert result["simulated_action"] == (
        recommendation["recommended_action"]
    )