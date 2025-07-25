from typing_extensions import Container
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup, Vertical
from textual.widgets import Button, Label, ProgressBar, Switch, Static
from textual.color import Color
from textual.screen import Screen

from requests import get, post
from dotenv import load_dotenv
import json

import asyncio
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

    async def run_service(self, service: str, data: dict = {}):
        json: dict = {"entity_id": self.id}
        jsonresponse = post(
            f"http://{self.ip}:{self.port}/api/services/{self.domain}/{service}",
            headers=self.headers,
            json=dict(json, **data)
        )
        response: dict = jsonresponse.json()

class ColorBar(HorizontalGroup, can_focus=True):
    BINDINGS = [("left", "decrease", "Decrease value"), ("right", "increase", "Increase value")]
    
    def __init__(self):
        super().__init__()
        self.bar = ProgressBar(total=255, show_percentage=False, show_eta=False)
        self.styles.width = "auto"

    def action_decrease(self):
        if self.bar.progress > 0:
            self.bar.advance(-1)

    def action_increase(self) -> None:
        if self.bar.progress < 255:
            self.bar.advance(1)
    
    def compose(self) -> ComposeResult:
        yield self.bar

class ColorPicker(VerticalGroup):
    def __init__(self, device):
        super().__init__()
        self.device: Device = device
        
        self.red: ColorBar = ColorBar()
        self.green: ColorBar = ColorBar()
        self.blue: ColorBar = ColorBar()

        self.colorbox = Static("█████████")
        self.color = [int, int, int]

        self.styles.width = "auto"
        self.styles.border = ("round", "white")
        self.styles.padding = (1, 1)

    async def read_color(self):
        while True:
            self.colorbox.styles.color = Color(int(self.red.bar.progress), int(self.green.bar.progress), int(self.blue.bar.progress))
            await asyncio.sleep(0.1)

    async def set_color(self):
        while True:
            self.color = [int(self.red.bar.progress), int(self.green.bar.progress), int(self.blue.bar.progress)]
            if self.color != [0, 0, 0]:
                await self.device.run_service("turn_on", data={"rgb_color": self.color})
            await asyncio.sleep(0.1)

    async def kill_workers(self):
        self.read_worker.cancel()
        self.set_worker.cancel()

    async def on_mount(self):
        self.read_worker = self.run_worker(self.read_color(), exclusive=False)
        self.set_worker = self.run_worker(self.set_color(), exclusive=False)

    def compose(self) -> ComposeResult:
        yield self.red
        yield self.green
        yield self.blue
        yield self.colorbox

class PopupScreen(Screen):
    BINDINGS = [("escape", "exit", "exit")]

    def __init__(self, widget):
        super().__init__()
        self.styles.align = ("center", "middle")
        self.styles.background = "black 20%"
        self.popup_widget = widget

    def action_exit(self):
        app.pop_screen()
        self.popup_widget.kill_workers()

    def compose(self) -> ComposeResult:
        yield self.popup_widget

class PickColor(Button):
    def __init__(self, device: Device):
        super().__init__()
        self.device: Device = device
        self.colorpicker = ColorPicker(self.device)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        await app.push_screen(PopupScreen(self.colorpicker))

class ToggleSwitch(Switch):
    def __init__(self, device: Device):
        super().__init__()
        self.device: Device = device
        with self.prevent(self.Changed):
            self.value = self.get_device_state()
        
    def get_device_state(self):
        jsonresponse = get(
            f"http://{self.device.ip}:{self.device.port}/api/states/{self.device.id}",
            headers=self.device.headers
        )
        response: dict = jsonresponse.json()
        return True if response['state'] == 'on' else False

    async def on_switch_changed(self, event: Switch.Changed) -> None:
        await self.device.run_service("turn_off" if self.get_device_state() else "turn_on")
        with self.prevent(self.Changed):
            self.value = not self.get_device_state()

class DeviceWidget(HorizontalGroup):
    def __init__(self, device: Device):
        super().__init__()
        self.device: Device = device
        self.styles.layer = "bottom"
    
    def compose(self) -> ComposeResult:
        yield Label(self.device.name)
        yield ToggleSwitch(self.device)
        yield PickColor(self.device)

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
