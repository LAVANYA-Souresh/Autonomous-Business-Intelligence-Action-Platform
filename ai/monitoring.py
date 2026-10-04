from collections import Counter
from datetime import datetime, timezone
from typing import Any


class MonitoringError(Exception):
    """Raised when monitoring data cannot be recorded."""
    pass


class MonitoringService:
    """
    Tracks operational metrics for the AI business
    operations pipeline.

    This component provides lightweight in-memory
    monitoring for portfolio and development use.

    It does not replace production monitoring systems.
    """

    def __init__(self):
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.verification_failures = 0

        self.recommendations_created = 0
        self.approval_requests = 0
        self.simulated_actions = 0

        self.workflow_counts = Counter()

        self.execution_times = []

        self.last_event = None

    def record_analysis(
        self,
        workflow: str,
        status: str,
        execution_time_seconds: float
    ) -> dict[str, Any]:

        if not workflow or not workflow.strip():
            raise MonitoringError(
                "workflow is required."
            )

        if not status or not status.strip():
            raise MonitoringError(
                "status is required."
            )

        if execution_time_seconds < 0:
            raise MonitoringError(
                "execution_time_seconds cannot be negative."
            )

        self.total_runs += 1

        self.workflow_counts[
            workflow.strip()
        ] += 1

        self.execution_times.append(
            execution_time_seconds
        )

        if status == "VERIFIED":
            self.successful_runs += 1

        elif status == "VERIFICATION_FAILED":
            self.failed_runs += 1
            self.verification_failures += 1

        else:
            self.failed_runs += 1

        self.last_event = {
            "event_type": "ANALYSIS_RECORDED",
            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "workflow": workflow.strip(),
            "status": status.strip(),
            "execution_time_seconds": (
                execution_time_seconds
            )
        }

        return self.last_event

    def record_recommendation(
        self,
        recommendation_status: str
    ) -> dict[str, Any]:

        if not recommendation_status:
            raise MonitoringError(
                "recommendation_status is required."
            )

        self.recommendations_created += 1

        self.last_event = {
            "event_type": "RECOMMENDATION_RECORDED",
            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "recommendation_status": (
                recommendation_status
            )
        }

        return self.last_event

    def record_approval_request(
        self,
        approval_status: str
    ) -> dict[str, Any]:

        if not approval_status:
            raise MonitoringError(
                "approval_status is required."
            )

        self.approval_requests += 1

        self.last_event = {
            "event_type": "APPROVAL_REQUEST_RECORDED",
            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "approval_status": approval_status
        }

        return self.last_event

    def record_action_simulation(
        self,
        action_status: str
    ) -> dict[str, Any]:

        if not action_status:
            raise MonitoringError(
                "action_status is required."
            )

        self.simulated_actions += 1

        self.last_event = {
            "event_type": "ACTION_SIMULATION_RECORDED",
            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "action_status": action_status
        }

        return self.last_event

    def get_metrics(self) -> dict[str, Any]:

        average_execution_time = 0.0

        if self.execution_times:
            average_execution_time = (
                sum(self.execution_times)
                / len(self.execution_times)
            )

        success_rate = 0.0

        if self.total_runs:
            success_rate = (
                self.successful_runs
                / self.total_runs
                * 100
            )

        return {
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "verification_failures": (
                self.verification_failures
            ),
            "success_rate_percent": round(
                success_rate,
                2
            ),
            "recommendations_created": (
                self.recommendations_created
            ),
            "approval_requests": (
                self.approval_requests
            ),
            "simulated_actions": (
                self.simulated_actions
            ),
            "workflow_counts": dict(
                self.workflow_counts
            ),
            "average_execution_time_seconds": round(
                average_execution_time,
                4
            ),
            "last_event": self.last_event
        }


if __name__ == "__main__":

    print(
        "\n========== MONITORING SERVICE TEST ==========\n"
    )

    monitoring = MonitoringService()

    # --------------------------------------
    # Test 1: Successful analysis
    # --------------------------------------

    print(
        "Recording successful analysis..."
    )

    monitoring.record_analysis(
        workflow="simple_factual",
        status="VERIFIED",
        execution_time_seconds=2.5
    )

    # --------------------------------------
    # Test 2: Diagnostic analysis
    # --------------------------------------

    print(
        "Recording diagnostic analysis..."
    )

    monitoring.record_analysis(
        workflow="diagnostic",
        status="VERIFIED",
        execution_time_seconds=8.2
    )

    # --------------------------------------
    # Test 3: Verification failure
    # --------------------------------------

    print(
        "Recording verification failure..."
    )

    monitoring.record_analysis(
        workflow="trend",
        status="VERIFICATION_FAILED",
        execution_time_seconds=5.1
    )

    # --------------------------------------
    # Test 4: Recommendation
    # --------------------------------------

    print(
        "Recording recommendation..."
    )

    monitoring.record_recommendation(
        recommendation_status="READY_FOR_REVIEW"
    )

    # --------------------------------------
    # Test 5: Approval
    # --------------------------------------

    print(
        "Recording approval request..."
    )

    monitoring.record_approval_request(
        approval_status="PENDING"
    )

    # --------------------------------------
    # Test 6: Action simulation
    # --------------------------------------

    print(
        "Recording simulated action..."
    )

    monitoring.record_action_simulation(
        action_status="SIMULATED"
    )

    # --------------------------------------
    # Display metrics
    # --------------------------------------

    print(
        "\n========== CURRENT METRICS ==========\n"
    )

    metrics = monitoring.get_metrics()

    for key, value in metrics.items():
        print(
            f"{key}: {value}"
        )

    print(
        "\nMonitoring service test completed."
    )