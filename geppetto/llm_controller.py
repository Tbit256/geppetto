import logging
from typing import List, Dict, Type, Optional, Any
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class LLMController:
    def __init__(self, handlers):
        self.handlers = {}
        self.current_handler = None
        self.default_handler = None

        for handler in handlers:
            name = handler["name"]
            handler_class = handler["handler"]
            handler_args = handler.get("handler_args", {})
            
            try:
                self.handlers[name] = handler_class(**handler_args)
                if self.default_handler is None:
                    self.default_handler = name
            except Exception as e:
                logging.error(f"Failed to initialize {name} handler: {str(e)}")

        if self.default_handler:
            self.current_handler = self.handlers[self.default_handler]
        else:
            raise ValueError("No handlers were successfully initialized")

    def switch_handler(self, handler_name):
        if handler_name in self.handlers:
            self.current_handler = self.handlers[handler_name]
            return True
        return False

    async def generate_content(self, user_prompt, status_callback=None, *status_callback_args):
        if not self.current_handler:
            raise ValueError("No handler is currently set")
            
        try:
            return await self.current_handler.llm_generate_content(
                user_prompt,
                status_callback,
                *status_callback_args
            )
        except Exception as e:
            logging.error(f"Error generating content: {str(e)}")
            raise

    async def generate_with_schema(
        self,
        messages: List[ChatMessage],
        output_schema: Type[BaseModel],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> BaseModel:
        """Generate a response using PydanticAI schema validation
        
        Args:
            messages: List of ChatMessage objects
            output_schema: Pydantic model class for response validation
            model: Optional model override
            temperature: Model temperature (default: 0.7)
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            Validated instance of output_schema
        """
        if not self.current_handler:
            raise ValueError("No handler is currently set")
            
        try:
            # Create OpenAI chat model
            chat_model = OpenAIChatModel(
                model=model or self.current_handler.model,
                temperature=temperature
            )
            
            # Generate response with schema validation
            response = await chat_model.generate(
                messages=messages,
                output_schema=output_schema,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logging.error(f"Error generating structured content: {str(e)}")
            raise

    def get_current_handler(self):
        return self.current_handler

    def get_handler_name(self):
        for name, handler in self.handlers.items():
            if handler == self.current_handler:
                return name
        return None
