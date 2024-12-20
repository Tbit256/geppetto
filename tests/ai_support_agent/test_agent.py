import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import UUID

import logfire
from pydantic import BaseModel

from geppetto.ai_support_agent.agent import SupportAgent, ChatMessage
from geppetto.ai_support_agent.models import (
    SupportContext,
    ITSupportResponse,
    AgentAction,
    WorkflowState
)

@pytest.fixture
def mock_llm_controller():
    controller = Mock()
    controller.generate_with_schema = AsyncMock()
    return controller

@pytest.fixture
def mock_freshdesk():
    freshdesk = Mock()
    freshdesk.create_ticket = AsyncMock()
    freshdesk.update_ticket = AsyncMock()
    return freshdesk

@pytest.fixture
def support_agent(mock_llm_controller, mock_freshdesk):
    return SupportAgent(
        llm_controller=mock_llm_controller,
        freshdesk_handler=mock_freshdesk
    )

@pytest.fixture
def sample_context():
    return SupportContext(
        user_id="U123456",
        channel_id="C789012",
        thread_ts="1640995200.000000"
    )

@pytest.fixture
def sample_response():
    return ITSupportResponse(
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

@pytest.mark.asyncio
async def test_get_or_create_context(support_agent):
    """Test context creation and retrieval"""
    # Test creation
    context = await support_agent.get_or_create_context(
        user_id="U123456",
        channel_id="C789012"
    )
    assert isinstance(context, SupportContext)
    assert context.user_id == "U123456"
    assert context.channel_id == "C789012"
    
    # Test retrieval
    same_context = await support_agent.get_or_create_context(
        user_id="U123456",
        channel_id="C789012",
        conversation_id=context.conversation_id
    )
    assert same_context == context

@pytest.mark.asyncio
async def test_process_message(
    support_agent,
    mock_llm_controller,
    sample_context,
    sample_response
):
    """Test message processing workflow"""
    message = "I can't connect to the internet"
    mock_llm_controller.generate_with_schema.return_value = sample_response
    
    response = await support_agent.process_message(message, sample_context)
    
    # Verify LLM was called correctly
    mock_llm_controller.generate_with_schema.assert_called_once()
    call_args = mock_llm_controller.generate_with_schema.call_args
    messages = call_args[1]["messages"]
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert messages[1].content == message
    
    # Verify response
    assert response == sample_response
    assert response.understanding == "User is having network connectivity issues"
    assert response.confidence == 0.92

@pytest.mark.asyncio
async def test_handle_ticket_creation(
    support_agent,
    mock_freshdesk,
    sample_context
):
    """Test ticket creation workflow"""
    mock_freshdesk.create_ticket.return_value = Mock(ticket_id=12345)
    
    await support_agent._handle_ticket_action(
        context=sample_context,
        action=Mock(
            action="create",
            subject="Test Ticket",
            description="Test Description",
            status=2,
            priority=1,
            tags=["network"]
        )
    )
    
    # Verify ticket was created
    mock_freshdesk.create_ticket.assert_called_once()
    assert sample_context.ticket_id == 12345

@pytest.mark.asyncio
async def test_handle_ticket_update(
    support_agent,
    mock_freshdesk,
    sample_context
):
    """Test ticket update workflow"""
    sample_context.ticket_id = 12345
    
    await support_agent._handle_ticket_action(
        context=sample_context,
        action=Mock(
            action="update",
            status=3,
            priority=2
        )
    )
    
    # Verify ticket was updated
    mock_freshdesk.update_ticket.assert_called_once_with(
        ticket_id=12345,
        status=3,
        priority=2
    )

@pytest.mark.asyncio
async def test_error_handling(support_agent, mock_llm_controller, sample_context):
    """Test error handling in message processing"""
    mock_llm_controller.generate_with_schema.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        await support_agent.process_message("test message", sample_context)
