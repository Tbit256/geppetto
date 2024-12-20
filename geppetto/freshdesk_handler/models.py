from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import Optional, List, Dict

class TicketStatus(IntEnum):
    """Freshdesk ticket status codes"""
    OPEN = 2
    PENDING = 3
    RESOLVED = 4
    CLOSED = 5

class TicketPriority(IntEnum):
    """Freshdesk ticket priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class TicketMetadata:
    """Represents a Freshdesk ticket's metadata"""
    ticket_id: int
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    requester_id: int
    created_at: datetime
    updated_at: datetime
    tags: List[str] = None
    custom_fields: Dict = None

    @classmethod
    def from_api_response(cls, data: dict) -> 'TicketMetadata':
        """Create a TicketMetadata instance from Freshdesk API response"""
        return cls(
            ticket_id=data['id'],
            subject=data['subject'],
            description=data['description'],
            status=TicketStatus(data['status']),
            priority=TicketPriority(data['priority']),
            requester_id=data['requester_id'],
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
            tags=data.get('tags', []),
            custom_fields=data.get('custom_fields', {})
        )

@dataclass
class Conversation:
    """Represents a conversation within a ticket"""
    ticket_id: int
    messages: List[dict]
    summary: Optional[str] = None
    
    def format_for_ticket(self) -> str:
        """Format the conversation for ticket content"""
        ticket_content = []
        
        if self.summary:
            ticket_content.extend([
                "# Issue Summary",
                self.summary,
                "",
                "# Conversation History"
            ])
        else:
            ticket_content.append("# Conversation History")
        
        for msg in self.messages:
            ticket_content.append(f"[{msg['role']}]: {msg['content']}")
        
        return "\n".join(ticket_content)
