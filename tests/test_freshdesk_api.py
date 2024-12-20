import unittest
from unittest.mock import patch, Mock
import json
from datetime import datetime

from geppetto.freshdesk_handler.api import (
    FreshdeskAPI,
    FreshdeskError,
    FreshdeskAPIError,
    FreshdeskDataError
)
from geppetto.freshdesk_handler.models import TicketStatus, TicketPriority, TicketMetadata

class TestFreshdeskAPI(unittest.TestCase):
    def setUp(self):
        self.api = FreshdeskAPI('test-domain.freshdesk.com', 'test-api-key')
        self.sample_ticket_response = {
            'id': 1,
            'subject': 'Test Ticket',
            'description': 'Test Description',
            'status': 2,
            'priority': 1,
            'requester_id': 42,
            'created_at': '2024-12-19T12:00:00Z',
            'updated_at': '2024-12-19T12:00:00Z',
            'tags': ['test'],
            'custom_fields': {}
        }

    def test_api_initialization(self):
        """Test API client initialization"""
        self.assertEqual(self.api.domain, 'test-domain.freshdesk.com')
        self.assertEqual(self.api.base_url, 'https://test-domain.freshdesk.com/api/v2')
        self.assertIn('Authorization', self.api.headers)
        self.assertIn('Content-Type', self.api.headers)

    @patch('requests.post')
    def test_create_ticket_success(self, mock_post):
        """Test successful ticket creation"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = self.sample_ticket_response
        mock_post.return_value = mock_response

        ticket = self.api.create_ticket(
            subject='Test Ticket',
            description='Test Description',
            email='test@example.com',
            status=TicketStatus.OPEN,
            priority=TicketPriority.LOW
        )

        self.assertIsInstance(ticket, TicketMetadata)
        self.assertEqual(ticket.ticket_id, 1)
        self.assertEqual(ticket.subject, 'Test Ticket')
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.api.base_url}/tickets")
        
        # Verify request payload
        request_data = call_args[1]['json']
        self.assertEqual(request_data['subject'], 'Test Ticket')
        self.assertEqual(request_data['email'], 'test@example.com')
        self.assertEqual(request_data['status'], TicketStatus.OPEN.value)

    @patch('requests.get')
    def test_get_ticket_success(self, mock_get):
        """Test successful ticket retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_ticket_response
        mock_get.return_value = mock_response

        ticket = self.api.get_ticket(1)
        
        self.assertIsInstance(ticket, TicketMetadata)
        self.assertEqual(ticket.ticket_id, 1)
        mock_get.assert_called_once_with(
            f"{self.api.base_url}/tickets/1",
            headers=self.api.headers
        )

    @patch('requests.put')
    def test_update_ticket_success(self, mock_put):
        """Test successful ticket update"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_ticket_response
        mock_put.return_value = mock_response

        ticket = self.api.update_ticket(
            ticket_id=1,
            status=TicketStatus.PENDING
        )
        
        self.assertIsInstance(ticket, TicketMetadata)
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        self.assertEqual(call_args[0][0], f"{self.api.base_url}/tickets/1")
        
        # Verify request payload
        request_data = call_args[1]['json']
        self.assertEqual(request_data['status'], TicketStatus.PENDING.value)

    @patch('requests.post')
    def test_add_note_success(self, mock_post):
        """Test successful note addition"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 1, 'body': 'Test note'}
        mock_post.return_value = mock_response

        note = self.api.add_note(1, 'Test note', is_private=True)
        
        self.assertEqual(note['body'], 'Test note')
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.api.base_url}/tickets/1/notes")
        
        # Verify request payload
        request_data = call_args[1]['json']
        self.assertEqual(request_data['body'], 'Test note')
        self.assertTrue(request_data['private'])

    def test_api_errors(self):
        """Test API error handling"""
        # Rate limit error
        mock_response = Mock()
        mock_response.status_code = 429
        
        with self.assertRaises(FreshdeskAPIError):
            self.api._validate_response(mock_response)
        
        # Authentication error
        mock_response.status_code = 401
        with self.assertRaises(FreshdeskAPIError):
            self.api._validate_response(mock_response)
        
        # Server error
        mock_response.status_code = 500
        with self.assertRaises(FreshdeskAPIError):
            self.api._validate_response(mock_response)

    @patch('requests.post')
    def test_upload_attachment_success(self, mock_post):
        """Test successful file attachment"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 1, 'name': 'test.txt'}
        mock_post.return_value = mock_response

        result = self.api.upload_attachment(
            ticket_id=1,
            file_data="Test content",
            file_name="test.txt"
        )
        
        self.assertEqual(result['name'], 'test.txt')
        mock_post.assert_called_once()
        
        # Verify multipart form data
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.api.base_url}/tickets/1/attachments")
        self.assertIn('files', call_args[1])
        self.assertNotIn('Content-Type', call_args[1]['headers'])

if __name__ == '__main__':
    unittest.main()
