import requests
headers = {
    'Authorization': 'Bearer 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'
}
response = requests.get('https://api.github.com/users/zelalem3', headers=headers)
data = response.json()
print(data)