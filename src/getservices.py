import requests
import dotenv
import pprint
import os

dotenv.load_dotenv()

headers = {
    "Authorization": f"Bearer {os.getenv("token")}",
    "content-type": "application/json",
}

jsonresponse = requests.get(
    f"http://100.64.0.1:8123/api/services",
    headers=headers,
)
response = jsonresponse.json()
for service in response:
    if service['domain'] == 'light':
        pprint.pp(service)
