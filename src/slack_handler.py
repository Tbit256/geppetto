import logging
import os
from slack_bolt import App
import certifi
from src.openai_handler import OpenAIHandler

# Set SSL certificate for secure requests
os.environ["SSL_CERT_FILE"] = certifi.where()

# Define global variables
thread_messages = {}

# TODO: maybe use a separate config file with all the dictionaries/descriptions


class SlackHandler:
    def __init__(
        self,
        allowed_users,
        SLACK_BOT_TOKEN,
        SIGNING_SECRET,
        OPENAI_API_KEY,
        DALLE_MODEL,
        CHATGPT_MODEL,
    ):
        self.openai = OpenAIHandler(OPENAI_API_KEY, DALLE_MODEL, CHATGPT_MODEL)
        self.app = App(signing_secret=SIGNING_SECRET, token=SLACK_BOT_TOKEN)
        self.allowed_users = allowed_users

        # Direct Message Event
        @self.app.event("message")
        def handle_direct_messages(body):
            self.handle_event(body)

        # App Mention Event
        @self.app.event("app_mention")
        def handle_app_mentions(body):
            self.handle_event(body)

    def handle_message(self, msg, channel_id, thread_id):
        thread_history = thread_messages.get(thread_id, [])
        thread_history.append({"role": "user", "content": msg})

        response = self.app.client.chat_postMessage(
            channel=channel_id,
            text=":geppetto: ... :thought_balloon: ...",
            thread_ts=thread_id,
        )

        if response["ok"]:
            timestamp = response["message"]["ts"]
            # TODO: use logger here
            print(f"Timestamp of the posted message: {timestamp}")
        else:
            print("Failed to post the message.")

        response_from_chatgpt = self.openai.send_message(thread_history)
        if isinstance(response_from_chatgpt, str):
            thread_history.append(
                {"role": "assistant", "content": response_from_chatgpt}
            )
        thread_messages[thread_id] = thread_history

        try:
            if isinstance(response_from_chatgpt, bytes):
                self.app.client.files_upload_v2(
                    channel=channel_id,
                    thread_ts=thread_id,
                    username="Dall-E",
                    content=response_from_chatgpt,
                    title="Image",
                )
            else:
                self.app.client.chat_update(
                    channel=channel_id,
                    text=response_from_chatgpt,
                    thread_ts=thread_id,
                    ts=timestamp,
                )
        except Exception as e:
            # TODO: use logger here
            print(f"Error posting message: {e}")
        pass

    def handle_event(self, body):
        event = body["event"]
        msg = event["text"]
        channel_id = event["channel"]
        thread_id = event.get("thread_ts", None) or event["ts"]
        user_id = event.get("user")

        # TODO: add logging information about the current event
        logging.info("%s: %s" % (user_id, msg))

        # Check if user is allowed
        if user_id in self.allowed_users.values():
            self.handle_message(msg, channel_id, thread_id)
        else:
            self.app.client.chat_postMessage(
                channel=channel_id,
                text="El usuario solicitante no pertenece a la lista de usuarios permitidos. Solicite permiso para utilizar la aplicación",
                thread_ts=thread_id,
            )