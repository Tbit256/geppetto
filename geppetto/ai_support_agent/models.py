from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from datetime import timezone as tz

class IssueCategory(str, Enum):
    ACCESS = "access_management"
    SOFTWARE = "software_issue"
    HARDWARE = "hardware_issue"
    NETWORK = "network_issue"
    SECURITY = "security_incident"
    OTHER = "other"

class IssueUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class WorkflowState(str, Enum):
    INITIAL = "initial"
    GATHERING_INFO = "gathering_info"
    ANALYZING = "analyzing"
    RESOLVING = "resolving"
    VERIFYING = "verifying"
    ESCALATING = "escalating"
    RESOLVED = "resolved"
    CLOSED = "closed"

class SupportContext(BaseModel):
    """Maintains state and context across the support interaction"""
    model_config = ConfigDict(use_enum_values=True)
    
    conversation_id: UUID = Field(default_factory=uuid4)
    user_id: str
    channel_id: str
    thread_ts: Optional[str] = None
    ticket_id: Optional[int] = None
    
    # State tracking
    current_state: WorkflowState = Field(default=WorkflowState.INITIAL)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(tz.utc))
    
    # Issue details
    category: Optional[IssueCategory] = None
    urgency: Optional[IssueUrgency] = None
    summary: Optional[str] = None
    
    # Information management
    gathered_info: Dict = Field(default_factory=dict)
    missing_info: List[str] = Field(default_factory=list)

class TicketAction(BaseModel):
    """Represents actions to be taken on a ticket"""
    action: Literal["create", "update", "resolve", "escalate"]
    priority: Optional[int] = Field(None, ge=1, le=4)
    status: Optional[int] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Reasoning and next steps
    reasoning: str = Field(description="Explanation for the action")
    next_steps: List[str] = Field(default_factory=list)

class AgentAction(BaseModel):
    """Defines the next action the agent should take"""
    action_type: Literal[
        "create_ticket",
        "update_ticket",
        "ask_question",
        "provide_solution",
        "escalate",
        "verify_solution"
    ]
    parameters: Dict = Field(default_factory=dict)
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)

class ITSupportResponse(BaseModel):
    """Structured response from the IT support agent"""
    understanding: str = Field(description="Agent's understanding of the issue")
    solution: Optional[str] = Field(None, description="Proposed solution if available")
    needs_human_intervention: bool = Field(
        default=False,
        description="Whether human support is needed"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level in the response"
    )
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Questions to clarify the issue"
    )
    ticket_action: Optional[TicketAction] = None
    agent_action: AgentAction

class SupportEvent(BaseModel):
    """Event logging model for Logfire"""
    model_config = ConfigDict(use_enum_values=True)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz.utc))
    event_type: str
    user_id: str
    channel_id: str
    conversation_id: UUID
    ticket_id: Optional[int] = None
    workflow_state: WorkflowState
    action_taken: str
    details: Optional[Dict] = None
