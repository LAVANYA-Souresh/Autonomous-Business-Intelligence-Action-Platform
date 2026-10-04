import json

import pytest

from ai.audit_logger import (
    AuditLogError,
    AuditLogger
)

from ai.monitoring import (
    MonitoringError,
    MonitoringService
)


def test_audit_logger_creates_event(tmp_path):
    log_file = tmp_path / "audit.log"

    logger = AuditLogger(
        log_file=str(log_file)
    )

    event = logger.log_event(
        event_type="ANALYSIS_COMPLETED",
        event_data={
            "question": "What was the revenue?"
        }
    )

    assert event["event_type"] == (
        "ANALYSIS_COMPLETED"
    )

    assert event["event_id"].startswith(
        "AUDIT-"
    )

    assert "timestamp" in event
    assert event["data"]["question"] == (
        "What was the revenue?"
    )

    assert log_file.exists()


def test_audit_logger_writes_valid_json(tmp_path):
    log_file = tmp_path / "audit.log"

    logger = AuditLogger(
        log_file=str(log_file)
    )

    logger.log_event(
        event_type="RECOMMENDATION_CREATED",
        event_data={
            "status": "READY_FOR_REVIEW"
        }
    )

    content = log_file.read_text(
        encoding="utf-8"
    ).strip()

    event = json.loads(content)

    assert event["event_type"] == (
        "RECOMMENDATION_CREATED"
    )

    assert event["data"]["status"] == (
        "READY_FOR_REVIEW"
    )


def test_audit_logger_supports_multiple_events(
    tmp_path
):
    log_file = tmp_path / "audit.log"

    logger = AuditLogger(
        log_file=str(log_file)
    )

    logger.log_event(
        event_type="ANALYSIS_STARTED",
        event_data={
            "question": "Test question"
        }
    )

    logger.log_event(
        event_type="ANALYSIS_COMPLETED",
        event_data={
            "status": "VERIFIED"
        }
    )

    lines = log_file.read_text(
        encoding="utf-8"
    ).strip().splitlines()

    assert len(lines) == 2

    first_event = json.loads(lines[0])
    second_event = json.loads(lines[1])

    assert first_event["event_type"] == (
        "ANALYSIS_STARTED"
    )

    assert second_event["event_type"] == (
        "ANALYSIS_COMPLETED"
    )


def test_audit_logger_rejects_empty_event_type(
    tmp_path
):
    log_file = tmp_path / "audit.log"

    logger = AuditLogger(
        log_file=str(log_file)
    )

    with pytest.raises(AuditLogError):
        logger.log_event(
            event_type="",
            event_data={}
        )


def test_monitoring_records_successful_analysis():
    monitoring = MonitoringService()

    event = monitoring.record_analysis(
        workflow="simple_factual",
        status="VERIFIED",
        execution_time_seconds=2.5
    )

    assert event["event_type"] == (
        "ANALYSIS_RECORDED"
    )

    metrics = monitoring.get_metrics()

    assert metrics["total_runs"] == 1
    assert metrics["successful_runs"] == 1
    assert metrics["failed_runs"] == 0
    assert metrics["verification_failures"] == 0
    assert metrics["success_rate_percent"] == 100.0


def test_monitoring_records_verification_failure():
    monitoring = MonitoringService()

    monitoring.record_analysis(
        workflow="trend",
        status="VERIFICATION_FAILED",
        execution_time_seconds=5.0
    )

    metrics = monitoring.get_metrics()

    assert metrics["total_runs"] == 1
    assert metrics["successful_runs"] == 0
    assert metrics["failed_runs"] == 1
    assert metrics["verification_failures"] == 1
    assert metrics["success_rate_percent"] == 0.0


def test_monitoring_tracks_workflows():
    monitoring = MonitoringService()

    monitoring.record_analysis(
        workflow="simple_factual",
        status="VERIFIED",
        execution_time_seconds=2.0
    )

    monitoring.record_analysis(
        workflow="diagnostic",
        status="VERIFIED",
        execution_time_seconds=8.0
    )

    monitoring.record_analysis(
        workflow="trend",
        status="VERIFIED",
        execution_time_seconds=4.0
    )

    metrics = monitoring.get_metrics()

    assert metrics["workflow_counts"] == {
        "simple_factual": 1,
        "diagnostic": 1,
        "trend": 1
    }


def test_monitoring_calculates_average_execution_time():
    monitoring = MonitoringService()

    monitoring.record_analysis(
        workflow="simple_factual",
        status="VERIFIED",
        execution_time_seconds=2.0
    )

    monitoring.record_analysis(
        workflow="diagnostic",
        status="VERIFIED",
        execution_time_seconds=8.0
    )

    metrics = monitoring.get_metrics()

    assert metrics[
        "average_execution_time_seconds"
    ] == 5.0


def test_monitoring_rejects_negative_execution_time():
    monitoring = MonitoringService()

    with pytest.raises(MonitoringError):
        monitoring.record_analysis(
            workflow="simple_factual",
            status="VERIFIED",
            execution_time_seconds=-1.0
        )