import pytest
from unittest.mock import Mock, AsyncMock, patch
from slack_bolt.async_app import AsyncApp

from geppetto.llm_controller import LLMController
from geppetto.freshdesk_handler import FreshdeskAPI
from geppetto.ai_support_agent import SupportAgent

@pytest.fixture(autouse=True)
def mock_logfire():
    with patch('logfire.info') as mock_info, \
         patch('logfire.error') as mock_error:
        yield {
            'info': mock_info,
            'error': mock_error
        }

@pytest.fixture
def mock_slack_app():
    app = Mock(spec=AsyncApp)
    app.client = Mock()
    app.event = Mock(return_value=lambda x: x)
    return app

@pytest.fixture
def mock_llm_controller():
    controller = Mock(spec=LLMController)
    controller.generate_with_schema = AsyncMock()
    return controller

@pytest.fixture
def mock_freshdesk():
    api = Mock(spec=FreshdeskAPI)
    api.create_ticket = AsyncMock()
    api.update_ticket = AsyncMock()
    return api

@pytest.fixture
def support_agent(mock_llm_controller, mock_freshdesk):
    return SupportAgent(
        llm_controller=mock_llm_controller,
        freshdesk_handler=mock_freshdesk
    )

@pytest.fixture
def sample_slack_message():
    return {
        "event": {
            "type": "message",
            "user": "U123456",
            "channel": "C789012",
            "ts": "1640995200.000000",
            "text": "I need help with my network connection"
        }
    }

@pytest.fixture
def sample_slack_thread_message():
    return {
        "event": {
            "type": "message",
            "user": "U123456",
            "channel": "C789012",
            "thread_ts": "1640995200.000000",
            "ts": "1640995300.000000",
            "text": "Yes, I've tried restarting my computer"
        }
    }
