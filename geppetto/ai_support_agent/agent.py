import logging
from typing import Optional, Dict, List
from datetime import datetime, timezone
from uuid import UUID

import logfire
from pydantic import BaseModel

from ..llm_controller import LLMController
from ..freshdesk_handler import FreshdeskAPI
from .models import (
    SupportContext,
    ITSupportResponse,
    AgentAction,
    TicketAction,
    SupportEvent,
    WorkflowState
)

class ChatMessage(BaseModel):
    role: str
    content: str

class SupportAgent:
    def __init__(
        self,
        llm_controller: LLMController,
        freshdesk_handler: FreshdeskAPI
    ):
        self.llm = llm_controller
        self.freshdesk = freshdesk_handler
        self.contexts: Dict[UUID, SupportContext] = {}

    def _log_event(
        self,
        event_type: str,
        context: SupportContext,
        action: str,
        details: Optional[Dict] = None
    ):
        """Log a support event"""
        event = SupportEvent(
            event_type=event_type,
            user_id=context.user_id,
            channel_id=context.channel_id,
            conversation_id=context.conversation_id,
            ticket_id=context.ticket_id,
            workflow_state=context.current_state,
            action_taken=action,
            details=details
        )
        logfire.info(
            "Support agent event: {event_type}",
            event_type=event_type,
            event=event.model_dump()
        )

    async def get_or_create_context(
        self,
        user_id: str,
        channel_id: str,
        thread_ts: Optional[str] = None,
        conversation_id: Optional[UUID] = None
    ) -> SupportContext:
        """Get existing context or create new one"""
        if conversation_id and conversation_id in self.contexts:
            return self.contexts[conversation_id]
        
        context = SupportContext(
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts
        )
        self.contexts[context.conversation_id] = context
        
        self._log_event("context_created", context, "create_context")
        return context

    async def process_message(
        self,
        message: str,
        context: SupportContext
    ) -> ITSupportResponse:
        """Process a user message and determine next action"""
        try:
            # Update context
            context.last_updated = datetime.now(timezone.utc)
            
            # Prepare conversation history
            messages = [
                ChatMessage(
                    role="system",
                    content=(
                        "You are an IT support agent. Analyze the user's issue "
                        "and provide structured responses to help resolve their problem."
                    )
                ),
                ChatMessage(role="user", content=message)
            ]
            
            # Get structured response from LLM
            response = await self.llm.generate_with_schema(
                messages=messages,
                output_schema=ITSupportResponse
            )
            
            # Update context based on response
            if response.ticket_action:
                await self._handle_ticket_action(context, response.ticket_action)
            
            # Log the interaction
            self._log_event(
                "message_processed",
                context,
                response.agent_action.action_type,
                details={
                    "confidence": response.confidence,
                    "needs_human": response.needs_human_intervention
                }
            )
            
            return response
            
        except Exception as e:
            logfire.error(
                "Error processing message: {error}",
                error=str(e),
                exc_info=True
            )
            self._log_event(
                "processing_error",
                context,
                "error",
                details={"error": str(e)}
            )
            raise

    async def _handle_ticket_action(
        self,
        context: SupportContext,
        action: TicketAction
    ):
        """Handle ticket-related actions"""
        try:
            if action.action == "create" and not context.ticket_id:
                ticket = await self.freshdesk.create_ticket(
                    subject=action.subject,
                    description=action.description,
                    email="user@example.com",  # TODO: Get from user profile
                    status=action.status,
                    priority=action.priority,
                    tags=action.tags
                )
                context.ticket_id = ticket.ticket_id
                self._log_event(
                    "ticket_created",
                    context,
                    "create_ticket",
                    details={"ticket_id": ticket.ticket_id}
                )
                
            elif action.action == "update" and context.ticket_id:
                await self.freshdesk.update_ticket(
                    ticket_id=context.ticket_id,
                    status=action.status,
                    priority=action.priority
                )
                self._log_event(
                    "ticket_updated",
                    context,
                    "update_ticket",
                    details={"ticket_id": context.ticket_id}
                )
                
        except Exception as e:
            logfire.error(
                "Error handling ticket action: {error}",
                error=str(e),
                exc_info=True
            )
            self._log_event(
                "ticket_error",
                context,
                "error",
                details={"error": str(e)}
            )
            raise
