import os
import requests
from dotenv import load_dotenv

load_dotenv()


class WebhookSender:
    def __init__(self, url=None):
        self.webhook_url = url or os.getenv("DISCORD_WEBHOOK")

    def send_text(self, message):
        try:
            requests.post(self.webhook_url, json={
                          "content": message}, timeout=60)
        except Exception as e:
            print(f"[Webhook Text Error] {e}")

    def send_file(self, file_path, message=""):
        try:
            with open(file_path, "rb") as f:
                file_name = os.path.basename(file_path)
                response = requests.post(
                    self.webhook_url,
                    data={"content": message},
                    files={"file": (file_name, f)},
                    timeout=60
                )

            if response.status_code not in (200, 204):
                print(
                    f"[Webhook File Error] Status: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"[Webhook File Exception] {e}")
