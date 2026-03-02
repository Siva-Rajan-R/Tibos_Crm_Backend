import requests
from datetime import datetime, timezone
import json

datas = [
    {'title': 'siva','description':"Hii Hello",'url':""},
    {'title': 'jeeva','description':"Hii Hello",'url':""},
    {'title': 'dhanush','description':"Hii Hello",'url':""},
]

for data in datas:
    res=requests.post(
        "http://127.0.0.1:8000/notify",
        json={
            "datas": data,
            "datetime": datetime.now(timezone.utc).isoformat(),
            "type": "text"
        }
    )

    print(res.text)