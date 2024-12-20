import pytest
from datetime import datetime
from uuid import UUID
from geppetto.ai_support_agent.models import (
    IssueCategory,
    IssueUrgency,
    WorkflowState,
    SupportContext,
    TicketAction,
    AgentAction,
    ITSupportResponse,
    SupportEvent
)

def test_support_context_creation():
    """Test creation and validation of SupportContext"""
    context = SupportContext(
        user_id="U123456",
        channel_id="C789012"
    )
    
    assert isinstance(context.conversation_id, UUID)
    assert context.user_id == "U123456"
    assert context.channel_id == "C789012"
    assert context.current_state == WorkflowState.INITIAL
    assert isinstance(context.last_updated, datetime)
    assert context.ticket_id is None
    assert context.gathered_info == {}
    assert context.missing_info == []

def test_ticket_action_validation():
    """Test TicketAction validation"""
    # Valid action
    action = TicketAction(
        action="create",
        priority=2,
        subject="Test ticket",
        description="Test description",
        reasoning="User reported critical issue"
    )
    assert action.action == "create"
    assert action.priority == 2
    
    # Invalid priority
    with pytest.raises(ValueError):
        TicketAction(
            action="create",
            priority=5,  # Invalid: must be 1-4
            subject="Test ticket"
        )
    
    # Invalid action
    with pytest.raises(ValueError):
        TicketAction(
            action="invalid_action",  # Invalid action type
            subject="Test ticket"
        )

def test_agent_action_validation():
    """Test AgentAction validation"""
    # Valid action
    action = AgentAction(
        action_type="ask_question",
        parameters={"question": "What is the error message?"},
        reasoning="Need more information to diagnose",
        confidence=0.85
    )
    assert action.action_type == "ask_question"
    assert action.confidence == 0.85
    
    # Invalid confidence
    with pytest.raises(ValueError):
        AgentAction(
            action_type="ask_question",
            reasoning="Test",
            confidence=1.5  # Invalid: must be 0-1
        )
    
    # Invalid action type
    with pytest.raises(ValueError):
        AgentAction(
            action_type="invalid_action",  # Invalid action type
            reasoning="Test",
            confidence=0.8
        )

def test_support_response_validation():
    """Test ITSupportResponse validation"""
    # Valid response
    response = ITSupportResponse(
        understanding="User is having network connectivity issues",
        solution="Check network settings and restart router",
        needs_human_intervention=False,
        confidence=0.92,
        follow_up_questions=["Have you tried restarting your computer?"],
        agent_action=AgentAction(
            action_type="provide_solution",
            reasoning="Clear network issue with standard solution",
            confidence=0.92
        )
    )
    assert response.understanding
    assert response.solution
    assert response.confidence == 0.92
    assert len(response.follow_up_questions) == 1
    
    # Invalid confidence
    with pytest.raises(ValueError):
        ITSupportResponse(
            understanding="Test",
            confidence=-0.1,  # Invalid: must be 0-1
            agent_action=AgentAction(
                action_type="ask_question",
                reasoning="Test",
                confidence=0.8
            )
        )

def test_support_event_logging():
    """Test SupportEvent creation and validation"""
    event = SupportEvent(
        event_type="message_processed",
        user_id="U123456",
        channel_id="C789012",
        conversation_id=UUID('12345678-1234-5678-1234-567812345678'),
        ticket_id=12345,
        workflow_state=WorkflowState.GATHERING_INFO,
        action_taken="ask_follow_up",
        details={"question": "What browser are you using?"}
    )
    
    assert event.event_type == "message_processed"
    assert event.ticket_id == 12345
    assert event.workflow_state == "gathering_info"  # Tests enum value conversion
    assert isinstance(event.timestamp, datetime)

def test_issue_categorization():
    """Test issue categorization enums"""
    assert IssueCategory.ACCESS.value == "access_management"
    assert IssueCategory.SOFTWARE.value == "software_issue"
    assert IssueCategory.HARDWARE.value == "hardware_issue"
    
    assert IssueUrgency.LOW.value == "low"
    assert IssueUrgency.CRITICAL.value == "critical"
    
    assert WorkflowState.INITIAL.value == "initial"
    assert WorkflowState.RESOLVED.value == "resolved"
