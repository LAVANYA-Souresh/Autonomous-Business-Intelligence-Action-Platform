import time
from typing import Any

from ai.analysis_planner import AnalysisPlanner
from ai.analysis_executor import AnalysisExecutor
from ai.diagnostic_executor import DiagnosticExecutor
from ai.numerical_verifier import (
    NumericalVerifier,
    NumericalVerificationError
)
from ai.evidence_package import EvidencePackageBuilder
from ai.recommendation_engine import RecommendationEngine
from ai.human_approval import HumanApprovalGate
from ai.action_simulator import ActionSimulator
from ai.audit_logger import AuditLogger
from ai.monitoring import MonitoringService
from rag.reasoning import BusinessReasoningEngine


class OrchestrationError(Exception):
    """Raised when orchestration fails."""
    pass


class BusinessOrchestrator:
    """
    Coordinates business analysis workflows.

    The planner determines the analysis type.
    Executors collect trusted evidence.
    The reasoning engine combines SQL evidence
    with relevant business knowledge.
    Numerical verification ensures that the
    LLM does not alter trusted database values.
    Evidence packaging creates an auditable record
    of the complete analysis process.
    Recommendation generation converts verified
    evidence into a human-reviewable recommendation.
    Human approval ensures that recommendations
    require explicit human authorization before
    any action can proceed.
    Action simulation demonstrates what would happen
    after explicit human approval without executing
    a real business operation.
    Audit logging records important pipeline events
    for traceability and accountability.
    Monitoring tracks operational metrics such as
    execution time, workflow counts, success rate,
    verification failures, recommendations,
    approvals, and simulated actions.
    """

    def __init__(
        self,
        analysis_planner: AnalysisPlanner,
        analysis_executor: AnalysisExecutor,
        diagnostic_executor: DiagnosticExecutor,
        reasoning_engine: BusinessReasoningEngine,
    ):
        self.analysis_planner = analysis_planner
        self.analysis_executor = analysis_executor
        self.diagnostic_executor = diagnostic_executor
        self.reasoning_engine = reasoning_engine

        # --------------------------------------
        # Verification component
        # --------------------------------------

        self.numerical_verifier = NumericalVerifier()

        # --------------------------------------
        # Evidence package component
        # --------------------------------------

        self.evidence_package_builder = (
            EvidencePackageBuilder()
        )

        # --------------------------------------
        # Recommendation component
        # --------------------------------------

        self.recommendation_engine = RecommendationEngine()

        # --------------------------------------
        # Human approval component
        # --------------------------------------

        self.human_approval_gate = HumanApprovalGate()

        # --------------------------------------
        # Action simulation component
        # --------------------------------------

        self.action_simulator = ActionSimulator()

        # --------------------------------------
        # Audit logging component
        # --------------------------------------

        self.audit_logger = AuditLogger()

        # --------------------------------------
        # Monitoring component
        # --------------------------------------

        self.monitoring = MonitoringService()

    def run(
        self,
        question: str
    ) -> dict[str, Any]:

        if not question or not question.strip():
            raise OrchestrationError(
                "Business question cannot be empty."
            )

        question = question.strip()

        # --------------------------------------
        # Start execution timer
        # --------------------------------------

        start_time = time.perf_counter()

        try:

            # --------------------------------------
            # Audit: Analysis started
            # --------------------------------------

            self._safe_audit_log(
                event_type="ANALYSIS_STARTED",
                event_data={
                    "question": question
                }
            )

            # --------------------------------------
            # Step 1: Understand the question
            # --------------------------------------

            analysis_plan = self.analysis_planner.plan(
                question
            )

            analysis_type = analysis_plan.get(
                "analysis_type"
            )

            # --------------------------------------
            # Step 2: Execute appropriate workflow
            # --------------------------------------

            if analysis_type == "simple_factual":

                result = self._execute_simple_factual(
                    question
                )

                workflow = "simple_factual"

            elif analysis_type == "trend":

                result = self.analysis_executor.execute(
                    question=question,
                    analysis_plan=analysis_plan
                )

                workflow = "trend"

            elif analysis_type == "diagnostic":

                result = self.diagnostic_executor.execute(
                    question=question,
                    analysis_plan=analysis_plan
                )

                workflow = "diagnostic"

            elif analysis_type == "comparison":

                result = self.analysis_executor.execute(
                    question=question,
                    analysis_plan=analysis_plan
                )

                workflow = "comparison"

            else:

                raise OrchestrationError(
                    f"Unsupported analysis type: {analysis_type}"
                )

            # --------------------------------------
            # Step 3: Convert execution result
            #         into trusted SQL evidence
            # --------------------------------------

            sql_evidence = self._format_sql_evidence(
                result
            )

            # --------------------------------------
            # Step 4: Build RAG + SQL reasoning prompt
            # --------------------------------------

            reasoning_prompt = (
                self.reasoning_engine.build_prompt(
                    question=question,
                    sql_evidence=sql_evidence
                )
            )

            # --------------------------------------
            # Step 5: Generate LLM reasoning answer
            # --------------------------------------

            reasoning_answer = (
                self.reasoning_engine.reason(
                    question=question,
                    sql_evidence=sql_evidence
                )
            )

            # --------------------------------------
            # Step 6: Extract trusted SQL results
            # --------------------------------------

            sql_results = self._extract_sql_results(
                result
            )

            # --------------------------------------
            # Step 7: Numerical verification
            # --------------------------------------

            verification_result = (
                self.numerical_verifier.verify(
                    answer=reasoning_answer,
                    sql_results=sql_results
                )
            )

            # --------------------------------------
            # Step 8: Handle failed verification
            # --------------------------------------

            if verification_result["status"] != "PASSED":

                evidence_package = (
                    self.evidence_package_builder.build(
                        question=question,
                        analysis_plan=analysis_plan,
                        workflow=workflow,
                        result=result,
                        sql_evidence=sql_evidence,
                        reasoning_answer=reasoning_answer,
                        numerical_verification=(
                            verification_result
                        ),
                        status="VERIFICATION_FAILED"
                    )
                )

                # --------------------------------------
                # Audit: Verification failed
                # --------------------------------------

                self._safe_audit_log(
                    event_type="VERIFICATION_FAILED",
                    event_data={
                        "question": question,
                        "workflow": workflow,
                        "status": "VERIFICATION_FAILED",
                        "verification": verification_result
                    }
                )

                # --------------------------------------
                # Monitoring: Verification failure
                # --------------------------------------

                execution_time = (
                    time.perf_counter()
                    - start_time
                )

                self._safe_record_analysis(
                    workflow=workflow,
                    status="VERIFICATION_FAILED",
                    execution_time_seconds=(
                        execution_time
                    )
                )

                return {
                    "status": "VERIFICATION_FAILED",
                    "question": question,
                    "analysis_plan": analysis_plan,
                    "workflow": workflow,
                    "result": result,
                    "sql_evidence": sql_evidence,
                    "reasoning_prompt": reasoning_prompt,
                    "reasoning_answer": reasoning_answer,
                    "numerical_verification": (
                        verification_result
                    ),
                    "evidence_package": evidence_package
                }

            # --------------------------------------
            # Step 9: Build verified evidence package
            # --------------------------------------

            evidence_package = (
                self.evidence_package_builder.build(
                    question=question,
                    analysis_plan=analysis_plan,
                    workflow=workflow,
                    result=result,
                    sql_evidence=sql_evidence,
                    reasoning_answer=reasoning_answer,
                    numerical_verification=(
                        verification_result
                    ),
                    status="VERIFIED"
                )
            )

            # --------------------------------------
            # Step 10: Generate recommendation
            # --------------------------------------

            recommendation = (
                self.recommendation_engine.recommend(
                    evidence_package
                )
            )

            # Add recommendation to evidence package
            evidence_package["recommendation"] = (
                recommendation
            )

            # --------------------------------------
            # Audit: Recommendation created
            # --------------------------------------

            self._safe_audit_log(
                event_type="RECOMMENDATION_CREATED",
                event_data={
                    "question": question,
                    "workflow": workflow,
                    "recommendation_status": (
                        recommendation.get(
                            "recommendation_status"
                        )
                    ),
                    "recommendation_confidence": (
                        recommendation.get(
                            "recommendation_confidence"
                        )
                    ),
                    "human_approval_required": (
                        recommendation.get(
                            "human_approval_required"
                        )
                    )
                }
            )

            # --------------------------------------
            # Monitoring: Recommendation created
            # --------------------------------------

            self._safe_record_recommendation(
                recommendation_status=(
                    recommendation.get(
                        "recommendation_status"
                    )
                )
            )

            # --------------------------------------
            # Step 11: Create human approval request
            # --------------------------------------

            approval = (
                self.human_approval_gate.create_pending_approval(
                    recommendation
                )
            )

            # Add approval request to evidence package
            evidence_package["approval"] = approval

            # --------------------------------------
            # Audit: Approval requested
            # --------------------------------------

            self._safe_audit_log(
                event_type="APPROVAL_REQUESTED",
                event_data={
                    "question": question,
                    "workflow": workflow,
                    "approval_status": (
                        approval.get(
                            "approval_status"
                        )
                    ),
                    "approved_by": (
                        approval.get(
                            "approved_by"
                        )
                    )
                }
            )

            # --------------------------------------
            # Monitoring: Approval requested
            # --------------------------------------

            self._safe_record_approval_request(
                approval_status=(
                    approval.get(
                        "approval_status"
                    )
                )
            )

            # --------------------------------------
            # Calculate total execution time
            # --------------------------------------

            execution_time = (
                time.perf_counter()
                - start_time
            )

            # --------------------------------------
            # Monitoring: Analysis completed
            # --------------------------------------

            self._safe_record_analysis(
                workflow=workflow,
                status="VERIFIED",
                execution_time_seconds=(
                    execution_time
                )
            )

            # --------------------------------------
            # Audit: Analysis completed
            # --------------------------------------

            self._safe_audit_log(
                event_type="ANALYSIS_COMPLETED",
                event_data={
                    "question": question,
                    "workflow": workflow,
                    "status": "VERIFIED",
                    "verification_status": (
                        verification_result.get(
                            "status"
                        )
                    ),
                    "execution_time_seconds": (
                        execution_time
                    )
                }
            )

            # --------------------------------------
            # Step 12: Return complete result
            # --------------------------------------

            return {
                "status": "VERIFIED",
                "question": question,
                "analysis_plan": analysis_plan,
                "workflow": workflow,
                "result": result,
                "sql_evidence": sql_evidence,
                "reasoning_prompt": reasoning_prompt,
                "reasoning_answer": reasoning_answer,
                "numerical_verification": (
                    verification_result
                ),
                "evidence_package": evidence_package,
                "recommendation": recommendation,
                "approval": approval
            }

        except OrchestrationError:
            raise

        except NumericalVerificationError as error:

            # --------------------------------------
            # Calculate execution time
            # --------------------------------------

            execution_time = (
                time.perf_counter()
                - start_time
            )

            # --------------------------------------
            # Monitoring: Failed analysis
            # --------------------------------------

            self._safe_record_analysis(
                workflow="unknown",
                status="FAILED",
                execution_time_seconds=(
                    execution_time
                )
            )

            # --------------------------------------
            # Audit: Numerical verification error
            # --------------------------------------

            self._safe_audit_log(
                event_type="ORCHESTRATION_FAILED",
                event_data={
                    "question": question,
                    "error_type": (
                        "NumericalVerificationError"
                    ),
                    "error": str(error),
                    "execution_time_seconds": (
                        execution_time
                    )
                }
            )

            raise OrchestrationError(
                f"Numerical verification failed: {error}"
            ) from error

        except Exception as error:

            # --------------------------------------
            # Calculate execution time
            # --------------------------------------

            execution_time = (
                time.perf_counter()
                - start_time
            )

            # --------------------------------------
            # Monitoring: Failed analysis
            # --------------------------------------

            self._safe_record_analysis(
                workflow="unknown",
                status="FAILED",
                execution_time_seconds=(
                    execution_time
                )
            )

            # --------------------------------------
            # Audit: Orchestration failed
            # --------------------------------------

            self._safe_audit_log(
                event_type="ORCHESTRATION_FAILED",
                event_data={
                    "question": question,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "execution_time_seconds": (
                        execution_time
                    )
                }
            )

            raise OrchestrationError(
                f"Orchestration failed: {error}"
            ) from error

    def simulate_approved_action(
        self,
        approval: dict[str, Any]
    ) -> dict[str, Any]:

        """
        Simulate a business action after explicit
        human approval.

        The action simulator will reject any
        approval record that is not APPROVED.
        """

        try:

            result = self.action_simulator.simulate(
                approval
            )

            # --------------------------------------
            # Audit: Action simulated
            # --------------------------------------

            self._safe_audit_log(
                event_type="ACTION_SIMULATED",
                event_data={
                    "action_status": (
                        result.get(
                            "action_status"
                        )
                    ),
                    "action_type": (
                        result.get(
                            "action_type"
                        )
                    ),
                    "approved_by": (
                        result.get(
                            "approved_by"
                        )
                    ),
                    "real_action_executed": (
                        result.get(
                            "real_action_executed"
                        )
                    ),
                    "simulation_only": (
                        result.get(
                            "simulation_only"
                        )
                    )
                }
            )

            # --------------------------------------
            # Monitoring: Action simulated
            # --------------------------------------

            self._safe_record_action_simulation(
                action_status=(
                    result.get(
                        "action_status"
                    )
                )
            )

            return result

        except Exception as error:

            # --------------------------------------
            # Audit: Action simulation failed
            # --------------------------------------

            self._safe_audit_log(
                event_type="ACTION_SIMULATION_FAILED",
                event_data={
                    "error_type": type(error).__name__,
                    "error": str(error)
                }
            )

            raise OrchestrationError(
                f"Action simulation failed: {error}"
            ) from error

    # ==================================================
    # SAFE MONITORING HELPERS
    # ==================================================

    def _safe_record_analysis(
        self,
        workflow: str,
        status: str,
        execution_time_seconds: float
    ) -> None:

        """
        Records analysis metrics without allowing
        monitoring failures to interrupt the
        main business pipeline.
        """

        try:

            self.monitoring.record_analysis(
                workflow=workflow,
                status=status,
                execution_time_seconds=(
                    execution_time_seconds
                )
            )

        except Exception as error:

            print(
                f"Monitoring warning: "
                f"analysis metric could not be recorded: "
                f"{error}"
            )

    def _safe_record_recommendation(
        self,
        recommendation_status: str
    ) -> None:

        """
        Records recommendation metrics safely.
        """

        try:

            self.monitoring.record_recommendation(
                recommendation_status=(
                    recommendation_status
                )
            )

        except Exception as error:

            print(
                f"Monitoring warning: "
                f"recommendation metric could not be "
                f"recorded: {error}"
            )

    def _safe_record_approval_request(
        self,
        approval_status: str
    ) -> None:

        """
        Records approval metrics safely.
        """

        try:

            self.monitoring.record_approval_request(
                approval_status=(
                    approval_status
                )
            )

        except Exception as error:

            print(
                f"Monitoring warning: "
                f"approval metric could not be "
                f"recorded: {error}"
            )

    def _safe_record_action_simulation(
        self,
        action_status: str
    ) -> None:

        """
        Records action simulation metrics safely.
        """

        try:

            self.monitoring.record_action_simulation(
                action_status=(
                    action_status
                )
            )

        except Exception as error:

            print(
                f"Monitoring warning: "
                f"action simulation metric could not "
                f"be recorded: {error}"
            )

    # ==================================================
    # SAFE AUDIT HELPER
    # ==================================================

    def _safe_audit_log(
        self,
        event_type: str,
        event_data: dict[str, Any]
    ) -> None:

        """
        Records audit events safely.

        Audit failures must never hide or replace
        the original business pipeline result.
        """

        try:

            self.audit_logger.log_event(
                event_type=event_type,
                event_data=event_data
            )

        except Exception as error:

            print(
                f"Audit logging warning: "
                f"event could not be recorded: "
                f"{error}"
            )

    # ==================================================
    # MONITORING METRICS
    # ==================================================

    def get_monitoring_metrics(
        self
    ) -> dict[str, Any]:

        """
        Returns the current monitoring metrics.
        """

        try:

            return self.monitoring.get_metrics()

        except Exception as error:

            raise OrchestrationError(
                f"Unable to retrieve monitoring metrics: "
                f"{error}"
            ) from error

    # ==================================================
    # SIMPLE FACTUAL EXECUTION
    # ==================================================

    def _execute_simple_factual(
        self,
        question: str
    ) -> dict[str, Any]:

        print(
            "\nExecuting simple factual query..."
        )

        result = (
            self.analysis_executor.sql_service.ask(
                question
            )
        )

        return {
            "status": "EXECUTED",
            "analysis_type": "simple_factual",
            "question": question,
            "sql": result["sql"],
            "results": result["results"],
            "attempts": result["attempts"]
        }

    # ==================================================
    # SQL RESULT EXTRACTION
    # ==================================================

    def _extract_sql_results(
        self,
        result: dict[str, Any]
    ) -> list[dict]:

        if not result:
            return []

        # --------------------------------------
        # Simple factual result
        # --------------------------------------

        if result.get(
            "analysis_type"
        ) == "simple_factual":

            return result.get(
                "results",
                []
            )

        # --------------------------------------
        # Multi-step evidence
        # --------------------------------------

        evidence = result.get(
            "evidence"
        )

        if evidence:

            sql_results = []

            for item in evidence:

                results = item.get(
                    "results",
                    []
                )

                if isinstance(
                    results,
                    list
                ):

                    sql_results.extend(
                        results
                    )

            return sql_results

        return []

    # ==================================================
    # SQL EVIDENCE FORMATTING
    # ==================================================

    def _format_sql_evidence(
        self,
        result: dict[str, Any]
    ) -> str:

        if not result:

            return (
                "No database evidence was produced."
            )

        # --------------------------------------
        # Simple factual result
        # --------------------------------------

        if result.get(
            "analysis_type"
        ) == "simple_factual":

            return (
                f"SQL:\n"
                f"{result.get('sql', '')}\n\n"
                f"RESULTS:\n"
                f"{result.get('results', [])}"
            )

        # --------------------------------------
        # Multi-step evidence
        # --------------------------------------

        evidence = result.get(
            "evidence"
        )

        if evidence:

            sections = []

            for item in evidence:

                evidence_type = item.get(
                    "evidence_type",
                    item.get(
                        "question",
                        "unknown"
                    )
                )

                period = item.get(
                    "period",
                    ""
                )

                results = item.get(
                    "results",
                    []
                )

                sections.append(
                    f"EVIDENCE TYPE: {evidence_type}\n"
                    f"PERIOD: {period}\n"
                    f"RESULTS: {results}"
                )

            return "\n\n---\n\n".join(
                sections
            )

        return str(result)


if __name__ == "__main__":

    print(
        "\n========== ORCHESTRATOR TEST ==========\n"
    )

    from ai.llm_client import OllamaLLMClient
    from ai.nl_to_sql_service import NLToSQLService

    # --------------------------------------
    # Initialize LLM
    # --------------------------------------

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    # --------------------------------------
    # Initialize SQL service
    # --------------------------------------

    sql_service = NLToSQLService(
        llm_client=llm_client
    )

    # --------------------------------------
    # Initialize analysis planner
    # --------------------------------------

    planner = AnalysisPlanner(
        llm_client=llm_client
    )

    # --------------------------------------
    # Initialize analysis executor
    # --------------------------------------

    analysis_executor = AnalysisExecutor(
        sql_service=sql_service
    )

    # --------------------------------------
    # Initialize diagnostic executor
    # --------------------------------------

    diagnostic_executor = DiagnosticExecutor(
        sql_service=sql_service
    )

    # --------------------------------------
    # Initialize reasoning engine
    # --------------------------------------

    reasoning_engine = BusinessReasoningEngine(
        llm_client=llm_client
    )

    # --------------------------------------
    # Initialize orchestrator
    # --------------------------------------

    orchestrator = BusinessOrchestrator(
        analysis_planner=planner,
        analysis_executor=analysis_executor,
        diagnostic_executor=diagnostic_executor,
        reasoning_engine=reasoning_engine
    )

    # --------------------------------------
    # Test question
    # --------------------------------------

    question = (
        "What was the revenue in May 2025?"
    )

    try:

        result = orchestrator.run(
            question
        )

        # --------------------------------------
        # Display orchestration result
        # --------------------------------------

        print(
            "\n========== ORCHESTRATION RESULT ==========\n"
        )

        print(
            f"\nStatus: "
            f"{result['status']}"
        )

        print(
            f"\nWorkflow: "
            f"{result['workflow']}"
        )

        print(
            f"\nQuestion: "
            f"{result['question']}"
        )

        # --------------------------------------
        # Display reasoning answer
        # --------------------------------------

        print(
            "\nLLM Reasoning Answer:"
        )

        print(
            result.get(
                "reasoning_answer",
                "No reasoning answer generated."
            )
        )

        # --------------------------------------
        # Display numerical verification
        # --------------------------------------

        print(
            "\nNumerical Verification:"
        )

        print(
            result.get(
                "numerical_verification",
                "Not available."
            )
        )

        # --------------------------------------
        # Display recommendation
        # --------------------------------------

        print(
            "\nRecommendation:"
        )

        print(
            result.get(
                "recommendation",
                "Not available."
            )
        )

        # --------------------------------------
        # Display human approval
        # --------------------------------------

        print(
            "\nHuman Approval:"
        )

        print(
            result.get(
                "approval",
                "Not available."
            )
        )

        # --------------------------------------
        # Display action simulation status
        # --------------------------------------

        print(
            "\nAction Simulation:"
        )

        print(
            "Not executed automatically."
        )

        print(
            "Human approval is required before "
            "an action can be simulated."
        )

        # --------------------------------------
        # Display monitoring metrics
        # --------------------------------------

        print(
            "\nMonitoring Metrics:"
        )

        print(
            orchestrator.get_monitoring_metrics()
        )

        # --------------------------------------
        # Display evidence package
        # --------------------------------------

        print(
            "\nEvidence Package:"
        )

        print(
            result.get(
                "evidence_package",
                "Not available."
            )
        )

    except OrchestrationError as error:

        print(
            "\nORCHESTRATION FAILED:"
        )

        print(error)