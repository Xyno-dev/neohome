from requests import get, post
from dotenv import load_dotenv
import tomllib
import pprint
import json
import time
import os

load_dotenv()

class Device():
    def __init__(self, entity_id: str, domain: str, headers: dict):
        self.id = entity_id
        self.domain = domain
        self.headers = headers

    def run_service(self, service):
        jsonresponse = post(
            f"http://100.64.0.1:8123/api/services/{self.domain}/{service}",
            headers=self.headers,
            json={"entity_id": self.id}
        )
        response = jsonresponse.json()
        pprint.pp(response)

def load_device(data, headers) -> list:
    devices = []
    try:
        devices = [
            Device(f"{domain}.{device}", domain, headers)
            for domain in data
            for device in data[domain]
            if data[domain][device]['enabled']
        ]
    except KeyError:
        raise tomllib.TOMLDecodeError("toml syntax is poo")
    return devices

def device_valid(device, response) -> bool:
    devices = []
    for resdevice in response:
        devices.append(resdevice['entity_id'])
    if device.id in devices:
        return True
    else:
        return False

def main():
    devices = []

    url = "http://100.64.0.1:8123/api/states"
    headers = {
        "Authorization": f"Bearer {os.getenv("token")}",
        "content-type": "application/json",
    }

    jsonresponse = get(url, headers=headers)
    response = json.loads(jsonresponse.text)

    try:
        with open("neohome.toml", "rb") as f:
            data = tomllib.load(f)
            devices = load_device(data, headers)
    except FileNotFoundError:
        raise FileNotFoundError("neohome.toml not found")
           
    while True:
        for device in devices:
            if device_valid(device, response):
                device.run_service("turn_off")
                time.sleep(1)
                device.run_service("turn_on")
                time.sleep(1)

if __name__ == "__main__":
    main()
