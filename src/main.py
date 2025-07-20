from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalScroll
from textual.widgets import Button, Digits, Footer, Header, Label

from requests import get, post
from dotenv import load_dotenv
import tomllib
import pprint
import json

import time
import os

load_dotenv()

class Device():
    def __init__(self, entity_id: str, domain: str, name: str, headers: dict):
        self.id: str = entity_id
        self.domain: str = domain
        self.name: str = name
        self.headers: dict = headers

    def run_service(self, service: str, data: dict):
        json: dict = {"entity_id": self.id}
        jsonresponse = post(
            f"http://100.64.0.1:8123/api/services/{self.domain}/{service}",
            headers=self.headers,
            json=dict(json, **data)
        )
        response: dict = jsonresponse.json()
        pprint.pp(response)

class DeviceWidget(HorizontalGroup):
    def __init__(self, device: Device):
        super().__init__()
        self.device: Device = device

    def compose(self) -> ComposeResult:
        yield Label(self.device.name)

class NeoHomeApp(App):
    def __init__(self):
        super().__init__()
        self.devices: list = []

        self.headers: dict = {
            "Authorization": f"Bearer {os.getenv("token")}",
            "content-type": "application/json",
        }

        url: str = "http://100.64.0.1:8123/api/states"
        jsonresponse = get(url, headers=self.headers)

        self.response: dict = json.loads(jsonresponse.text)
        self.devices: list = self.load_devices()

    def load_devices(self) -> list:
        devices = []

        try:
            with open("neohome.toml", "rb") as f:
                data: dict = tomllib.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("neohome.toml not found")

        try:
            devices: list = [
                Device(f"{domain}.{device}",
                       domain,
                       data[domain][device]['name'],
                       self.headers)
                for domain in data
                for device in data[domain]
                if data[domain][device]['enabled']
            ]
        except KeyError:
            raise tomllib.TOMLDecodeError("toml syntax is poo")
        return devices

    def device_valid(self, device: Device) -> bool:
        devices: list = []
        for resdevice in self.response:
            devices.append(resdevice['entity_id'])
        return True if device.id in devices else False

    def compose(self) -> ComposeResult:
        for device in self.devices:
            if self.device_valid(device):
                yield DeviceWidget(device)

if __name__ == "__main__":
    app = NeoHomeApp()
    app.run()
