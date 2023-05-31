import requests
r=requests.get("https://swapi.dev/api/people/1/")
r.status_code            
r.json()
datos=r.json()
print(datos["name"])