import requests

response = requests.post("http://localhost:5000/query", json={"query": "What are the scope and duties?"})
print(response.json())
