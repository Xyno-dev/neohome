from requests import get, post
from dotenv import load_dotenv
import tomllib
import pprint
import json
import time
import os

load_dotenv()

url = "http://100.64.0.1:8123/api/states"
headers = {
    "Authorization": f"Bearer {os.getenv("token")}",
    "content-type": "application/json",
}

jsonresponse = get(url, headers=headers)
response = json.loads(jsonresponse.text)
'''
for device in response:
    pprint.pp(device["entity_id"])
'''

def load_device(data):
    devices = []
    try:
        for devtype in data:
            for device in data[devtype]:
                if data[devtype][device]['enabled']:
                    devices.append(devtype + "." + device)
    except KeyError:
        raise tomllib.TOMLDecodeError("toml syntax is poo")
    return devices

def device_valid(device, response):
    devices = []
    for resdevice in response:
        devices.append(resdevice['entity_id'])
    if device in devices:
        return True
    else:
        return False

def turn_on(device):
    print(device, device.split(".")[0])
    jsonresponse = post(
        f"http://100.64.0.1:8123/api/services/{device.split(".")[0]}/turn_on",
        headers=headers,
        json={"entity_id": device}
    )
    response = jsonresponse.json()
    pprint.pp(response)

def turn_off(device):
    print(device, device.split(".")[0])
    jsonresponse = post(
        f"http://100.64.0.1:8123/api/services/{device.split(".")[0]}/turn_off",
        headers=headers,
        json={"entity_id": device}
    )
    response = jsonresponse.json()
    pprint.pp(response)
        
def main():
    try:
        with open("neohome.toml", "rb") as f:
            data = tomllib.load(f)
            devices = load_device(data)
            while True:
                for device in devices:
                    if device_valid(device, response):
                            turn_off(device)
                            time.sleep(1)
                            turn_on(device)
                            time.sleep(1)

    except FileNotFoundError:
        raise FileNotFoundError("neohome.toml not found")

if __name__ == "__main__":
    main()
