import requests
import os
api_key="{key}"
print(u"\U0001F948")
print(u"\u26A0")
ciutat = input("Entra la ciutat: ")
parametros={"q":ciutat,"mode":"json","units":"metric","APPID":api_key}
r=requests.get("http://api.openweathermap.org/data/2.5/weather",params=parametros)
r.status_code
r.url
r.json()
datos=r.json()
print(datos)
