from fnmatch import translate
import json
import pandas as pd
import os
import sys
import urllib.request

path = './output/text.json'
file_path = r'C:\Users\netk\Desktop\pyProject\output\text.json'

TransOutputText = []

def JAtoKO(text):
    client_id = "QRAMv2UL07BmEx67cKxb" # 개발자센터에서 발급받은 Client ID 값
    client_secret = "KNqoL6cgN8" # 개발자센터에서 발급받은 Client Secret 값
    jatext = urllib.parse.quote(text)
    data = "source=ja&target=ko&text=" + jatext
    url = "https://openapi.naver.com/v1/papago/n2mt"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id",client_id)
    request.add_header("X-Naver-Client-Secret",client_secret)
    response = urllib.request.urlopen(request, data=data.encode("utf-8"))
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        # print(response_body.decode('utf-8'))
        transjson = response_body.decode('utf-8')
        AfterTreatment(transjson)
    else:
        print("Error Code:" + rescode)


def AfterTreatment(TransText):
    global TransOutputText
    findTextPosition = 0
    findTextfinalPosition = 0
    findTextPosition += TransText.find("translatedText")

    findTextPosition += TransText[findTextPosition:].find(":\"")

    findTextPosition += TransText[findTextPosition:].find("\"")

    findTextfinalPosition = findTextPosition + TransText[findTextPosition:].find("\",")
    resultText = TransText[findTextPosition+1:findTextfinalPosition+1]

    TransOutputText.append(resultText)

def outputData():
    global TransOutputText
    with open("JA_to_KO_Trans.txt", "w", encoding="UTF-8") as file :
        for name in TransOutputText :
            file.write(name + '\n')
    print("추출이 완료되었습니다")



with open('./output/text.json', 'r', encoding='UTF8') as file:
    data = json.load(file)

# print(json.dumps(data, ensure_ascii = False))

# print(pd.json_normalize(data['images']))
# pd.json_normalize(data)

for key, value in data.items() :
    # print(key)
    # print('---------------------------------------------')
    if key == 'images' :
        print('------------------------')


# print(data['images']['fields'])d

# print(type(data['images']))

# print(data.get('images'))

# print(len(data['images'][0]['fields']))     # 길이
json_ImageText = ""
for j in range(len(data['images'][0]['fields'])) :
    for i in data['images'][0]['fields'][j]['inferText']:
        json_ImageText += i 

JAtoKO(json_ImageText)

outputData()

# for i in data['images'].items() :
    # print(i)

