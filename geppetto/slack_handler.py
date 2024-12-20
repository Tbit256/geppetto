import logging
import re
from typing import Optional, Dict, Any
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from .llm_controller import LLMController
from .ai_support_agent import SupportAgent, SupportContext

class SlackHandler:
    def __init__(
        self,
        app: AsyncApp,
        llm_controller: LLMController,
        support_agent: SupportAgent
    ):
        self.app = app
        self.client = app.client
        self.llm_controller = llm_controller
        self.support_agent = support_agent
        
        # Register event handlers
        self.app.event("message")(self.handle_message)
        self.app.event("app_mention")(self.handle_message)

    async def _get_message_context(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from Slack message"""
        event = body["event"]
        channel_id = event["channel"]
        thread_ts = event.get("thread_ts", event.get("ts"))
        user_id = event["user"]
        
        return {
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "user_id": user_id
        }

    async def handle_message(self, body, say):
        """Handle incoming Slack messages"""
        try:
            event = body["event"]
            text = event["text"]
            
            # Extract message context
            context_data = await self._get_message_context(body)
            
            # Get or create support context
            context = await self.support_agent.get_or_create_context(
                user_id=context_data["user_id"],
                channel_id=context_data["channel_id"],
                thread_ts=context_data["thread_ts"]
            )
            
            # Process message through support agent
            response = await self.support_agent.process_message(text, context)
            
            # Format and send response
            await self._send_response(
                say=say,
                context=context,
                response=response
            )
            
        except Exception as e:
            logging.error(f"Error handling Slack message: {str(e)}")
            await say(
                text="I apologize, but I encountered an error while processing your request. "
                     "Please try again or contact support if the issue persists.",
                thread_ts=event.get("thread_ts", event.get("ts"))
            )

    async def _send_response(self, say, context: SupportContext, response):
        """Format and send response to Slack"""
        # Build response blocks
        blocks = []
        
        # Add understanding section
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Understanding:*\n{response.understanding}"
                }
            },
            {"type": "divider"}
        ])
        
        # Add solution if available
        if response.solution:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Solution:*\n{response.solution}"
                }
            })
        
        # Add follow-up questions if any
        if response.follow_up_questions:
            questions = "\n".join(f"• {q}" for q in response.follow_up_questions)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Follow-up Questions:*\n{questions}"
                }
            })
        
        # Add ticket information if available
        if context.ticket_id:
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"*Ticket ID:* #{context.ticket_id}"
                }]
            })
        
        # Send response
        await say(
            blocks=blocks,
            text=response.understanding,  # Fallback text
            thread_ts=context.thread_ts
        )
