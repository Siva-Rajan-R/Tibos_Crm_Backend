import requests

url = "https://control.msg91.com/api/v5/widget/verifyAccessToken"
AUTH_KEY="532522A5MXEI40n56a310b0fP1"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

payload = {
    "authkey":AUTH_KEY,
    "access-token": "532522TZmwtnN4OySC6a310c6eP1"
}

response = requests.post(
    url,
    headers=headers,
    json=payload
)

print(response.status_code)
print(response.json())