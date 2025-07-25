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
for domain in response:
    if domain['domain'] == 'light':
        if 'rgb_color' in domain['services']['turn_on']:
            pprint.pp(domain['services']['turn_on'])
