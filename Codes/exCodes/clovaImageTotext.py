import json
import base64
from subprocess import call
import requests
import re

filepath = r'C:\Users\netk\Desktop\pyProject\output\text.json'

with open(r"C:\Users\netk\Desktop\pyProject\data\jpmantest.jpg", "rb") as f:
    img = base64.b64encode(f.read())

 # 본인의 APIGW Invoke URL로 치환
URL = "https://07kcy59we0.apigw.ntruss.com/custom/v1/18293/7df69ef5ffb9d844c54a0aa9e3c98e78aaee795d5f08b6c103cb21fd09ad4442/general"
    
 # 본인의 Secret Key로 치환
KEY = "UUV2ekxqdmt6cFpybkZlZ1FCRUFWcW9kcnVjdmxZekI="
    
headers = {
    "Content-Type": "application/json",
    "X-OCR-SECRET": KEY
}
    
data = {
    "version": "V1",
    "requestId": "sample_id", # 요청을 구분하기 위한 ID, 사용자가 정의
    "timestamp": 0, # 현재 시간값
    "images": [
        {
            "name": "sample_image",
            "format": "jpg",
            "data": img.decode('utf-8')
        }
    ]
}
data = json.dumps(data)
# print(data)
response = requests.post(URL, data=data, headers=headers)
# print(response.text)
res = json.loads(response.text)
# print(res)

# print(type(res))
# print(len(res))
# print(res[1])

callText = ""

for key, value in res.items() :
    # print(key)
    if key == 'images' :
        print(value)
        # resulttext = str(value)
        # callText =callText +  re.search('inferText\': \'(.+?)\',', resulttext).group(1)

print(callText)
        

# print(res[3])



with open(filepath, 'w', encoding='UTF8') as f:
    f.write(json.dumps(res, ensure_ascii = False))

