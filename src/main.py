from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Button, Label, Switch

from requests import get, post
from dotenv import load_dotenv
import tomllib
import json

import os

from config import Config

load_dotenv()

class Device():
    def __init__(self, entity_id: str, domain: str, name: str, headers: dict, ip: str, port: str):
        self.id: str = entity_id
        self.domain: str = domain
        self.name: str = name
        self.headers: dict = headers
        self.ip: str = ip
        self.port: str = port

    def run_service(self, service: str, data: dict = {}):
        json: dict = {"entity_id": self.id}
        jsonresponse = post(
            f"http://{self.ip}:{self.port}/api/services/{self.domain}/{service}",
            headers=self.headers,
            json=dict(json, **data)
        )
        response: dict = jsonresponse.json()

class ToggleSwitch(Switch):
    def __init__(self, device: Device):
        super().__init__()
        self.device: Device = device
        self.value = True if self.get_device_state() == 'on' else False
        
    def get_device_state(self):
        jsonresponse = get(
            f"http://{self.device.ip}:{self.device.port}/api/states/{self.device.id}",
            headers=self.device.headers
        )
        response: dict = jsonresponse.json()
        return response['state']

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.device.run_service("turn_on" if self.get_device_state() == "off" else "turn_off")
        self.value = True if self.get_device_state() == 'off' else False

class DeviceWidget(HorizontalGroup):
    def __init__(self, device: Device):
        super().__init__()
        self.device: Device = device
    
    def compose(self) -> ComposeResult:
        yield Label(self.device.name)
        yield ToggleSwitch(self.device)

class NeoHomeApp(App):
    def __init__(self):
        super().__init__()
        self.devices: list = []

        self.headers: dict = {
            "Authorization": f"Bearer {os.getenv("token")}",
            "content-type": "application/json",
        }

        configclass = Config(self)
        self.config = configclass.config

        self.devices: list = self.load_devices()

    def load_devices(self) -> list:
        devices = []

        devices: list = [
            Device(f"{domain}.{device}",
                   domain,
                   self.config[domain][device]['name'],
                   self.headers,
                   self.config['ip'],
                   self.config.get('port') or '8123',
            )
            for domain in self.config
            for device in self.config[domain]
            if isinstance(self.config[domain], dict)
            if self.config[domain][device]['enabled']
        ]
        return devices

    def device_valid(self, device: Device) -> bool:
        url: str = f"http://{device.ip}:{device.port}/api/states"
        jsonresponse = get(url, headers=self.headers)

        self.response: dict = json.loads(jsonresponse.text)
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
