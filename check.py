import requests

response = requests.get("http://192.168.0.105/testing2-hockeypuck-k8s/", timeout = 5)
print(response.status_code)
print(response.text)
