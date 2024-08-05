import requests
import os

url = "https://api.vapi.ai/call/phone"

payload = {
    "assistantId": "2c18f737-cb7a-4bef-8126-7f1c6117c423",
    "assistant": {
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en"
        },
        "model": {
            "model": "mixtral-8x7b-32768",
            "messages": [{"content": "Hello, I am Mira."}],
            "provider": "groq",
            "temperature": 0,
            "maxTokens": 200
        }
    }
}
headers = {
    "Authorization": f"Bearer {os.getenv('VAPI_API_KEY')}",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)