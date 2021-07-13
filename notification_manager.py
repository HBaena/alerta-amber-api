import requests
import json
from icecream import ic

class NotificationsManager:
    """docstring for NotificationsManager"""
    def __init__(self, filename):
        self.headers = None
        self.language = None
        self.url = None
        self.app_id = None
        with open(filename, "r") as file:
            config = json.loads(file.read())
            self.headers = {
                "Content-Type": config["Content-Type"],
                "Authorization": config["Authorization"]}
            self.language = config["language"]
            self.url = config["url"]
            self.app_id = config["app_id"]

    def send_notification_tag_base(self, data: dict):
        data = dict(
            app_id=self.app_id,
            filters=data['filters'],
            data=data['params'],
            contents={self.language: data["contents"]}
        )
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))
        ic(response.json())
        return response.status_code

    def send_notification_idx_base(self, data: dict):
        data = dict(
            app_id=self.app_id,
            include_external_user_ids=data['ids'],
            channel_for_external_user_ids="push",
            contents={self.language:data["contents"]}
        )
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))
        ic(response.json())
        return response.status_code