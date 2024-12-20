import pytest
from unittest.mock import Mock, AsyncMock

from geppetto.slack_handler import SlackHandler
from geppetto.ai_support_agent.models import (
    ITSupportResponse,
    AgentAction,
    SupportContext
)

@pytest.fixture
def slack_handler(mock_slack_app, mock_llm_controller, support_agent):
    return SlackHandler(
        app=mock_slack_app,
        llm_controller=mock_llm_controller,
        support_agent=support_agent
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
async def test_message_context_extraction(slack_handler, sample_slack_message):
    """Test extraction of context from Slack message"""
    context = await slack_handler._get_message_context(sample_slack_message)
    
    assert context["channel_id"] == "C789012"
    assert context["user_id"] == "U123456"
    assert context["thread_ts"] == "1640995200.000000"

@pytest.mark.asyncio
async def test_handle_message(
    slack_handler,
    sample_slack_message,
    support_agent,
    sample_response
):
    """Test handling of incoming Slack message"""
    mock_say = AsyncMock()
    support_agent.process_message = AsyncMock(return_value=sample_response)
    
    await slack_handler.handle_message(sample_slack_message, mock_say)
    
    # Verify support agent was called
    support_agent.process_message.assert_called_once()
    message_arg = support_agent.process_message.call_args[0][0]
    assert message_arg == "I need help with my network connection"
    
    # Verify response was sent
    mock_say.assert_called_once()
    call_kwargs = mock_say.call_args[1]
    assert "blocks" in call_kwargs
    assert call_kwargs["thread_ts"] == "1640995200.000000"
    
    # Verify blocks structure
    blocks = call_kwargs["blocks"]
    assert len(blocks) >= 2  # At least understanding and solution sections
    assert blocks[0]["type"] == "section"
    assert "Understanding" in blocks[0]["text"]["text"]

@pytest.mark.asyncio
async def test_handle_message_error(slack_handler, sample_slack_message):
    """Test error handling in message processing"""
    mock_say = AsyncMock()
    slack_handler.support_agent.process_message = AsyncMock(
        side_effect=Exception("Test error")
    )
    
    await slack_handler.handle_message(sample_slack_message, mock_say)
    
    # Verify error response was sent
    mock_say.assert_called_once()
    call_kwargs = mock_say.call_args[1]
    assert "error" in call_kwargs["text"].lower()
    assert call_kwargs["thread_ts"] == "1640995200.000000"

@pytest.mark.asyncio
async def test_response_formatting(slack_handler, sample_response):
    """Test formatting of response into Slack blocks"""
    mock_say = AsyncMock()
    context = SupportContext(
        user_id="U123456",
        channel_id="C789012",
        thread_ts="1640995200.000000",
        ticket_id=12345
    )
    
    await slack_handler._send_response(
        say=mock_say,
        context=context,
        response=sample_response
    )
    
    # Verify response structure
    mock_say.assert_called_once()
    blocks = mock_say.call_args[1]["blocks"]
    
    # Check understanding section
    assert blocks[0]["type"] == "section"
    assert "Understanding" in blocks[0]["text"]["text"]
    assert sample_response.understanding in blocks[0]["text"]["text"]
    
    # Check solution section
    solution_block = next(
        b for b in blocks 
        if b["type"] == "section" and "Solution" in b["text"]["text"]
    )
    assert sample_response.solution in solution_block["text"]["text"]
    
    # Check follow-up questions
    questions_block = next(
        b for b in blocks 
        if b["type"] == "section" and "Follow-up Questions" in b["text"]["text"]
    )
    assert sample_response.follow_up_questions[0] in questions_block["text"]["text"]
    
    # Check ticket info
    ticket_block = next(
        b for b in blocks 
        if b["type"] == "context"
    )
    assert "12345" in ticket_block["elements"][0]["text"]
