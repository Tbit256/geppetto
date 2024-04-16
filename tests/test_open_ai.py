import json
import os
import sys
import logging
import unittest
from unittest.mock import Mock, patch

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

from geppetto.openai_handler import OpenAIHandler

TEST_PERSONALITY = "Your AI assistant"

def OF(**kw):
    class OF:
        pass

    instance = OF()
    for k, v in kw.items():
        setattr(instance, k, v)
    return instance


class TestOpenAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patcher = patch("geppetto.openai_handler.OpenAI")
        cls.mock_openai = cls.patcher.start()
        cls.openai_handler = OpenAIHandler(personality=TEST_PERSONALITY)

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_personality(self):
        self.assertEqual(self.openai_handler.personality, TEST_PERSONALITY)

    def test_send_text_message(self):
        user_prompt = [{"role": "user", "content": "Hello"}]

        mock_chat_completion_response = Mock()
        mock_chat_completion_response.choices = [
            OF(message=OF(content="Mocked ChatGPT Response", tool_calls=[]))
        ]
        self.mock_openai().chat.completions.create.return_value = (
            mock_chat_completion_response
        )
        response = self.openai_handler.llm_generate_content(user_prompt, self.my_callback, None)
        self.assertEqual(response, "Mocked ChatGPT Response")

    def my_callback(self, *args):
        logging.info("Image sent successfully")

    @patch("geppetto.openai_handler.OpenAIHandler.download_image")
    def test_send_image_message(self, mock_download_image):
        mock_download_image.return_value = b"Mocked Image Bytes"
        mock_tool_call = Mock()
        mock_tool_call.function.name = "generate_image"
        mock_tool_call.function.arguments = json.dumps(
            {"prompt": "Generate an image of a mountain", "size": "1024x1024"}
        )

        mock_chat_completion_response = Mock()
        mock_chat_completion_response.choices = [
            OF(
                message=OF(
                    content="Generate an image of a mountain",
                    tool_calls=[mock_tool_call],
                )
            )
        ]
        self.mock_openai().chat.completions.create.return_value = (
            mock_chat_completion_response
        )

        user_prompt = [{"role": "user", "content": "Generate an image of a mountain"}]

        response = self.openai_handler.llm_generate_content(user_prompt, self.my_callback, None)

        # Assuming download_image returns bytes
        self.assertIsInstance(response, bytes)


if __name__ == "__main__":
    unittest.main()
