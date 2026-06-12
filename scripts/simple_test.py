"""
Simple test to check search response
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test search
print("Testing search...")
response = requests.post(
    f"{BASE_URL}/search",
    json={"q": "टमाटर के पत्ते पीले हो रहे हैं"},
    headers={"Content-Type": "application/json"},
    timeout=15
)

print(f"Status: {response.status_code}")
print(f"Response type: {type(response.json())}")
print(f"\nRaw response:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
