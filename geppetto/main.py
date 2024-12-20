import os
import logging
from typing import Dict
from slack_bolt.async_app import AsyncApp
import logfire

from .llm_controller import LLMController
from .slack_handler import SlackHandler
from .openai_handler import OpenAIHandler
from .gemini_handler import GeminiHandler
from .claude_handler import ClaudeHandler
from .ollama_handler import OllamaHandler
from .freshdesk_handler import FreshdeskAPI
from .ai_support_agent import SupportAgent
from .utils import load_json

# Load environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SIGNING_SECRET = os.getenv("SIGNING_SECRET")
FRESHDESK_DOMAIN = os.getenv("FRESHDESK_DOMAIN")
FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")

# Load default responses and configurations
DEFAULT_RESPONSES = load_json("default_responses.json")
ALLOWED_USERS = load_json("allowed-slack-ids.json")

# Initialize Logfire
logfire.configure(
    api_key=os.getenv("LOGFIRE_API_KEY"),
    service_name="geppetto-support"
)

def initialize_app() -> AsyncApp:
    """Initialize and configure the Slack app"""
    return AsyncApp(
        token=SLACK_BOT_TOKEN,
        signing_secret=SIGNING_SECRET
    )

def initialize_llm_controller() -> LLMController:
    """Initialize and configure the LLM controller"""
    return LLMController([
        {
            "name": "Ollama",
            "handler": OllamaHandler,
            "handler_args": {
                "personality": DEFAULT_RESPONSES["features"]["personality"]
            }
        }
    ])

def initialize_freshdesk() -> FreshdeskAPI:
    """Initialize and configure the Freshdesk API client"""
    return FreshdeskAPI(
        domain=FRESHDESK_DOMAIN,
        api_key=FRESHDESK_API_KEY
    )

def initialize_support_agent(
    llm_controller: LLMController,
    freshdesk: FreshdeskAPI
) -> SupportAgent:
    """Initialize and configure the Support Agent"""
    return SupportAgent(
        llm_controller=llm_controller,
        freshdesk_handler=freshdesk
    )

async def main():
    """Initialize and start the application"""
    try:
        # Initialize components
        app = initialize_app()
        llm_controller = initialize_llm_controller()
        freshdesk = initialize_freshdesk()
        support_agent = initialize_support_agent(llm_controller, freshdesk)
        
        # Initialize Slack handler with support agent
        slack_handler = SlackHandler(
            app=app,
            llm_controller=llm_controller,
            support_agent=support_agent
        )
        
        # Start the app
        await app.start(port=int(os.getenv("PORT", 3000)))
        
    except Exception as e:
        logfire.error(
            "Failed to start application: {error}",
            error=str(e),
            exc_info=True
        )
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
