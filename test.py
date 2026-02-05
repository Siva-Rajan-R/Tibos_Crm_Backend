import requests


print(requests.post("https://countriesnow.space/api/v0.1/countries/state/cities",json={'state':'Tamil Nadu','city':'Madurai'}).json())