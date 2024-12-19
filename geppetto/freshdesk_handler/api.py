import os
import logging
import requests
from typing import Optional, List, Union
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from base64 import b64encode

from .models import TicketMetadata, Conversation, TicketStatus, TicketPriority

class FreshdeskError(Exception):
    """Base exception for Freshdesk errors"""
    pass

class FreshdeskAPIError(FreshdeskError):
    """API-related errors (rate limits, authentication)"""
    pass

class FreshdeskDataError(FreshdeskError):
    """Data validation errors"""
    pass

class FreshdeskAPI:
    def __init__(self, domain: str, api_key: str):
        """Initialize Freshdesk API client
        
        Args:
            domain: Freshdesk domain (e.g., 'company.freshdesk.com')
            api_key: Freshdesk API key
        """
        self.domain = domain.rstrip('/')
        self.api_key = api_key
        self.base_url = f"https://{self.domain}/api/v2"
        
        # Basic auth header using API key
        auth = b64encode(f"{self.api_key}:X".encode()).decode()
        self.headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json'
        }

    def _validate_response(self, response: requests.Response) -> dict:
        """Validate API response and handle errors"""
        if response.status_code == 429:
            raise FreshdeskAPIError("Rate limit exceeded")
        elif response.status_code == 401:
            raise FreshdeskAPIError("Authentication failed")
        elif response.status_code >= 500:
            raise FreshdeskAPIError(f"Freshdesk server error: {response.status_code}")
        elif response.status_code >= 400:
            raise FreshdeskAPIError(f"API error: {response.text}")
        
        try:
            return response.json()
        except ValueError:
            raise FreshdeskDataError("Invalid JSON response")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def create_ticket(
        self,
        subject: str,
        description: str,
        email: str,
        status: TicketStatus = TicketStatus.OPEN,
        priority: TicketPriority = TicketPriority.MEDIUM,
        tags: List[str] = None,
        **kwargs
    ) -> TicketMetadata:
        """Create a new ticket
        
        Args:
            subject: Ticket subject
            description: Ticket description/content
            email: Requester's email
            status: Ticket status (default: OPEN)
            priority: Ticket priority (default: MEDIUM)
            tags: List of tags to apply
            **kwargs: Additional ticket fields
        
        Returns:
            TicketMetadata object
        """
        data = {
            'subject': subject,
            'description': description,
            'email': email,
            'status': status.value,
            'priority': priority.value,
            'tags': tags or []
        }
        data.update(kwargs)
        
        response = requests.post(
            f"{self.base_url}/tickets",
            headers=self.headers,
            json=data
        )
        
        result = self._validate_response(response)
        return TicketMetadata.from_api_response(result)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_ticket(self, ticket_id: int) -> TicketMetadata:
        """Retrieve ticket details
        
        Args:
            ticket_id: Ticket ID to retrieve
            
        Returns:
            TicketMetadata object
        """
        response = requests.get(
            f"{self.base_url}/tickets/{ticket_id}",
            headers=self.headers
        )
        
        result = self._validate_response(response)
        return TicketMetadata.from_api_response(result)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def update_ticket(
        self,
        ticket_id: int,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        **kwargs
    ) -> TicketMetadata:
        """Update an existing ticket
        
        Args:
            ticket_id: Ticket ID to update
            status: New ticket status
            priority: New ticket priority
            **kwargs: Additional fields to update
            
        Returns:
            Updated TicketMetadata object
        """
        data = {}
        if status is not None:
            data['status'] = status.value
        if priority is not None:
            data['priority'] = priority.value
        data.update(kwargs)
        
        response = requests.put(
            f"{self.base_url}/tickets/{ticket_id}",
            headers=self.headers,
            json=data
        )
        
        result = self._validate_response(response)
        return TicketMetadata.from_api_response(result)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def add_note(
        self,
        ticket_id: int,
        body: str,
        is_private: bool = False
    ) -> dict:
        """Add a note to a ticket
        
        Args:
            ticket_id: Ticket ID to add note to
            body: Note content
            is_private: Whether the note is private
            
        Returns:
            Note data from API
        """
        data = {
            'body': body,
            'private': is_private
        }
        
        response = requests.post(
            f"{self.base_url}/tickets/{ticket_id}/notes",
            headers=self.headers,
            json=data
        )
        
        return self._validate_response(response)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def upload_attachment(
        self,
        ticket_id: int,
        file_data: Union[str, bytes],
        file_name: str
    ) -> dict:
        """Upload an attachment to a ticket
        
        Args:
            ticket_id: Ticket ID to attach file to
            file_data: File content (string or bytes)
            file_name: Name of the file
            
        Returns:
            Attachment data from API
        """
        # Convert string to bytes if necessary
        if isinstance(file_data, str):
            file_data = file_data.encode('utf-8')
            
        files = {
            'attachments[]': (file_name, file_data)
        }
        
        # Remove Content-Type from headers for multipart upload
        headers = self.headers.copy()
        headers.pop('Content-Type', None)
        
        response = requests.post(
            f"{self.base_url}/tickets/{ticket_id}/attachments",
            headers=headers,
            files=files
        )
        
        return self._validate_response(response)
