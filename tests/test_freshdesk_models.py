import unittest
from datetime import datetime
from geppetto.freshdesk_handler.models import (
    TicketStatus,
    TicketPriority,
    TicketMetadata,
    Conversation
)

class TestTicketModels(unittest.TestCase):
    def setUp(self):
        self.sample_ticket_data = {
            'id': 1,
            'subject': 'Test Ticket',
            'description': 'Test Description',
            'status': 2,
            'priority': 1,
            'requester_id': 42,
            'created_at': '2024-12-19T12:00:00Z',
            'updated_at': '2024-12-19T12:00:00Z',
            'tags': ['test', 'sample'],
            'custom_fields': {'field1': 'value1'}
        }

    def test_ticket_status_enum(self):
        """Test TicketStatus enum values"""
        self.assertEqual(TicketStatus.OPEN.value, 2)
        self.assertEqual(TicketStatus.PENDING.value, 3)
        self.assertEqual(TicketStatus.RESOLVED.value, 4)
        self.assertEqual(TicketStatus.CLOSED.value, 5)

    def test_ticket_priority_enum(self):
        """Test TicketPriority enum values"""
        self.assertEqual(TicketPriority.LOW.value, 1)
        self.assertEqual(TicketPriority.MEDIUM.value, 2)
        self.assertEqual(TicketPriority.HIGH.value, 3)
        self.assertEqual(TicketPriority.URGENT.value, 4)

    def test_ticket_metadata_from_api_response(self):
        """Test creating TicketMetadata from API response"""
        metadata = TicketMetadata.from_api_response(self.sample_ticket_data)
        
        self.assertEqual(metadata.ticket_id, 1)
        self.assertEqual(metadata.subject, 'Test Ticket')
        self.assertEqual(metadata.description, 'Test Description')
        self.assertEqual(metadata.status, TicketStatus.OPEN)
        self.assertEqual(metadata.priority, TicketPriority.LOW)
        self.assertEqual(metadata.requester_id, 42)
        self.assertIsInstance(metadata.created_at, datetime)
        self.assertIsInstance(metadata.updated_at, datetime)
        self.assertEqual(metadata.tags, ['test', 'sample'])
        self.assertEqual(metadata.custom_fields, {'field1': 'value1'})

class TestConversation(unittest.TestCase):
    def setUp(self):
        self.sample_messages = [
            {'role': 'user', 'content': 'Hello, I need help'},
            {'role': 'assistant', 'content': 'How can I assist you?'}
        ]

    def test_conversation_without_summary(self):
        """Test conversation formatting without summary"""
        conv = Conversation(ticket_id=1, messages=self.sample_messages)
        formatted = conv.format_for_ticket()
        
        expected = (
            "# Conversation History\n"
            "[user]: Hello, I need help\n"
            "[assistant]: How can I assist you?"
        )
        self.assertEqual(formatted, expected)

    def test_conversation_with_summary(self):
        """Test conversation formatting with summary"""
        conv = Conversation(
            ticket_id=1,
            messages=self.sample_messages,
            summary="User requesting assistance"
        )
        formatted = conv.format_for_ticket()
        
        expected = (
            "# Issue Summary\n"
            "User requesting assistance\n"
            "\n"
            "# Conversation History\n"
            "[user]: Hello, I need help\n"
            "[assistant]: How can I assist you?"
        )
        self.assertEqual(formatted, expected)

if __name__ == '__main__':
    unittest.main()
