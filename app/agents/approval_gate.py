from typing import Optional
from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput, current_time_iso

class ApprovalGateInput(AgentInput):
    workflow_id: str
    run_id: str
    required: bool = True
    approver: Optional[str] = None
    action: str = "request" # "request" | "approve" | "reject"
    comments: Optional[str] = ""

class ApprovalGateOutput(AgentOutput):
    workflow_id: str
    run_id: str
    status: str # "awaiting_approval" | "approved" | "rejected" | "bypassed"
    approved_by: Optional[str] = None
    decision_timestamp: Optional[str] = None
    audit_notes: str

class ApprovalGateAgent(BaseAgent[ApprovalGateInput, ApprovalGateOutput]):
    agent_id = "approval-gate"
    name = "Approval Gate"
    department = "Governance"
    description = "Enforces authorized human approval before any external write or publication action."

    async def execute(self, input_data: ApprovalGateInput) -> ApprovalGateOutput:
        if not input_data.required:
            return ApprovalGateOutput(
                success=True,
                workflow_id=input_data.workflow_id,
                run_id=input_data.run_id,
                status="bypassed",
                audit_notes="Approval was not required by configuration."
            )

        if input_data.action == "approve":
            approver = input_data.approver or "admin@workspace.local"
            return ApprovalGateOutput(
                success=True,
                workflow_id=input_data.workflow_id,
                run_id=input_data.run_id,
                status="approved",
                approved_by=approver,
                decision_timestamp=current_time_iso(),
                audit_notes=f"Approved by {approver}. Comment: {input_data.comments or 'No comment provided.'}"
            )
        elif input_data.action == "reject":
            return ApprovalGateOutput(
                success=True,
                workflow_id=input_data.workflow_id,
                run_id=input_data.run_id,
                status="rejected",
                approved_by=input_data.approver,
                decision_timestamp=current_time_iso(),
                audit_notes=f"Rejected. Reason: {input_data.comments or 'Changes requested.'}"
            )

        # Default action is "request"
        return ApprovalGateOutput(
            success=True,
            workflow_id=input_data.workflow_id,
            run_id=input_data.run_id,
            status="awaiting_approval",
            audit_notes="Workflow paused at approval gate awaiting human sign-off."
        )
