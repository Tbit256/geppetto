import os
import requests
import logging
from typing import Callable, List, Dict, Union
from dotenv import load_dotenv

from .llm_api_handler import LLMHandler
from .exceptions import InvalidThreadFormatError

load_dotenv(os.path.join("config", ".env"))

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # default to mistral if not specified
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VERSION = os.getenv("GEPPETTO_VERSION")


class OllamaHandler(LLMHandler):
    def __init__(self, personality):
        """Initialize the Ollama handler with the specified model."""
        super().__init__("Ollama", OLLAMA_MODEL, None)  # No client needed for Ollama
        self.personality = personality
        self.system_role = "system"
        self.assistant_role = "assistant"
        self.user_role = "user"
        self.base_url = OLLAMA_BASE_URL

    def format_messages(self, messages: List[Dict]) -> str:
        """Format messages for Ollama API.
        
        Ollama expects a simple string with role prefixes."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role and content:
                formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    def llm_generate_content(
        self, user_prompt: Union[str, List[Dict]], status_callback: Callable = None, *status_callback_args
    ):
        """Generate content using Ollama API.
        
        Args:
            user_prompt: Either a string prompt or a list of message dictionaries
            status_callback: Optional callback for status updates
            status_callback_args: Additional arguments for the status callback
        """
        try:
            logging.info("Sending message to Ollama: %s", user_prompt)
            
            # Handle both string and list[dict] input types
            if isinstance(user_prompt, str):
                messages = [
                    {
                        "role": self.system_role,
                        "content": self.personality
                    },
                    {
                        "role": self.user_role,
                        "content": user_prompt
                    }
                ]
            else:
                # For list input, add system message at the beginning
                messages = [
                    {
                        "role": self.system_role,
                        "content": self.personality
                    },
                    *user_prompt  # Unpack the user messages
                ]
            
            # Format messages for Ollama
            prompt = self.format_messages(messages)
            logging.info("Formatted prompt for Ollama: %s", prompt)
            
            # Make request to Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            response.raise_for_status()  # Raise an exception for bad status codes
            result = response.json()
            response_text = result.get("response", "")
            
            # Add version and model information
            response_text += f"\n\n_(Geppetto v{VERSION} Source: Ollama Model {self.model})_"
            
            # Return the response text (don't call status_callback)
            return response_text
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error connecting to Ollama API: {str(e)}"
            logging.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"Error generating content with Ollama: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def get_functionalities(self):
        """Return available functionalities for this handler."""
        return {}
