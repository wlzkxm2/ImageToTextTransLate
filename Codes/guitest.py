from distutils import file_util
from distutils.command.config import config
from fileinput import filename
from tkinter import *
import os
import tkinter

import json
import base64
from subprocess import call
from tkinter import messagebox
import tkinter.ttk
from unittest import result
from xml.etree.ElementPath import findtext
import requests

import urllib.request

import pytesseract as pyt
import cv2
from pytesseract import Output
import pickle

# ImageTranslate 기본 디렉토리
# ImageInput 번역할 이미지
# JsonOutput 추출된 Json
# TextOutput 번역된


findFileLists = []

allData = ''
Secret_Key = ''
APIGW_key = ''
Client_ID = ''
Client_Secret = ''

def refresh():
    print("refresh")
    list.delete(0, END)

    with os.scandir("./ImageTranslate/ImageInput") as entries:
        for entry in entries:
            print(entry.name)
            findFiles = entry.name
            if findFiles.endswith(".jpg") or findFiles.endswith(".png") :
                list.insert(END, entry.name)
                findFileLists.append(entry.name)

def createDirectory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print("Error: Failed to create the directory.")

def getKeys():
    global allData
    global Secret_Key
    global APIGW_key
    global Client_ID
    global Client_Secret
    try :
        with open(r'ImageTranslate\keys.txt', 'r') as file :
            allData = file.read()
    except:
        default_Keys = "Secret Key = 'Input_Secret_Key'\nAPIGW = 'Input_APIGW_Key'\nClient ID = 'Input_Client ID'\nClient Secret = 'Input_Client_Secret_Key'"
        keyFile = open(r'ImageTranslate\keys.txt', "w")
        keyFile.write(default_Keys)
        keyFile.close()
        messagebox.showinfo("키가 없음",  "네이버 Clova Key 또는 Papago Key가 없습니다. Keys.txt 파일을 확인해 주세요")
    
    position = allData.find("\'") + 1
    back_position = position + allData[position:].find("\'")
    print("-------------------------------------------------")
    print("Secret Key : " + allData[position : back_position])

    Secret_Key = allData[position : back_position]

    position = back_position + 2
    position = position + allData[position:].find("\'") + 1
    back_position = position + allData[position:].find("\'")
    print("-------------------------------------------------")
    print("APIGW : " + allData[position : back_position])

    APIGW_key = allData[position : back_position]

    position = back_position + 2
    position = position + allData[position:].find("\'") + 1
    back_position = position + allData[position:].find("\'")
    print("Client ID : " + allData[position : back_position])

    Client_ID = allData[position : back_position]

    position = back_position + 2
    position = position + allData[position:].find("\'") + 1
    back_position = position + allData[position:].find("\'")
    print("Client Secret : " + allData[position : back_position])

    Client_Secret = allData[position : back_position]

def OpenDirectory(where):
    directory = "ImageTranslate\\" + where
    try:
        if os.path.exists(directory):
            os.startfile(directory)
    except OSError:
        messagebox.showinfo("폴더가 없음", "해당 폴더를 찾을 수 없습니다. 프로그램을 재시작해주세요")

def TkinterSet():
    window.title("ImageTranslate")
    window.geometry("800x800")
    window.resizable(False, False)

def DirectoryCheak():
    createDirectory("ImageTranslate")
    createDirectory("ImageTranslate\ImageInput")
    createDirectory("ImageTranslate\JsonOutput")
    createDirectory("ImageTranslate\TextOutput")
    createDirectory("data")
    

    
def ClovaFindImageToTextWork(filename) :
    position = filename.find(".")
    filenameNotdot = filename[:position]
    print(filenameNotdot)

    filepath = r'ImageTranslate\JsonOutput\\' + filenameNotdot + ".json"

    with open(r"ImageTranslate\ImageInput\\" + filename , "rb") as f:
        img = base64.b64encode(f.read())

    # 본인의 APIGW Invoke URL로 치환
    URL = APIGW_key
        
    # 본인의 Secret Key로 치환
    KEY = Secret_Key
        
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
    # print(response.json_ImageText)
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

def PapagoTranslateWork(filename) :
    # filename : ex.jpg 
    # filenameNotdot : ex
    global TransOutputText

    position = filename.find(".")
    filenameNotdot = filename[:position]  
    # print(f"input : {filename}")      
    # print(f"filenameNotdot : {filenameNotdot}")      

    path = './ImageTranslate/JsonOutput/' + filenameNotdot + '.json'
    path = './ImageTranslate/JsonOutput/' + filenameNotdot + '.txt'
    file_path = r'\ImageTranslate\JsonOutput\\' + filenameNotdot + '.json'

    TransOutputText = []
    with open(path , 'r', encoding='UTF8') as file:
        data = json.load(file)

    json_ImageText = ""     # 텍스트를 담기위한 string

    # print("---------------------------------------------------------")
    # print(f"fileType : {type(data)}")
    # print("---------------------------------------------------------")

    if(type(data) == dict):
        for j in range(len(data['images'][0]['fields'])) :
            for i in data['images'][0]['fields'][j]['inferText']:
                json_ImageText += i
    else:
        json_ImageText = data 
  

    # JAtoKO(json_ImageText)
    client_id = Client_ID # 개발자센터에서 발급받은 Client ID 값
    client_secret = Client_Secret # 개발자센터에서 발급받은 Client Secret 값
    jatext = urllib.parse.quote(json_ImageText)
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
        # AfterTreatment(transjson)
        findTextPosition = 0
        findTextfinalPosition = 0
        findTextPosition += transjson.find("translatedText")

        findTextPosition += transjson[findTextPosition:].find(":\"")

        findTextPosition += transjson[findTextPosition:].find("\"")

        findTextfinalPosition = findTextPosition + transjson[findTextPosition:].find("\",")
        resultText = transjson[findTextPosition+1:findTextfinalPosition+1]

        TransOutputText.append(resultText)

    else:
        print("Error Code:" + rescode)

    # outputData()
    with open("./ImageTranslate/TextOutput/" + filenameNotdot + ".txt", "w", encoding="UTF-8") as file :
        for name in TransOutputText :
            file.write(name + '\n')
    print("추출이 완료되었습니다")

def TesseractFindImageToTextWork(filename):
    global imgRead
    pyt.pytesseract.tesseract_cmd = r"data\tesseract-ocr\tesseract"
    imgPath = r"ImageTranslate\ImageInput\\" + filename
    # config = ("-l jpn-vert --oem 3 --psm 11")
    text = pyt.image_to_string(imgPath, lang = "jpn_vert")
    print("-----------------------------")
    print(text)
    print("-----------------------------")
    imgRead = cv2.imread(imgPath)
    imgResult = pyt.image_to_data(imgRead, output_type=Output.DICT)

    # json_imgInfo = {
    #     "text" : findtext,
    #     "x" : x,
    #     "y" : y,
    #     "w" : w,
    #     "h" : h
    # }

    print(json_imgInfo.values)

    for i in range(0, len(imgResult["text"])):
        textPositionInfo = ""
        x = imgResult["left"][i]
        textPositionInfo += x
        y = imgResult["top"][i]
        textPositionInfo += y

        w = imgResult["width"][i]
        textPositionInfo += w
        h = imgResult["height"][i]
        textPositionInfo += x

        imgtext = imgResult["text"][i]
        conf = int(imgResult["conf"][i])
        if conf > 0:
            imgtext = "".join([c if ord(c) < 128 else "" for c in imgtext]).strip()
            cv2.rectangle(imgRead, (x, y), (x + w, y + h), (0, 255, 0), 1)
            # cv2.putText(imgRead, text, (x, y -10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 200), 2)
        json_imgInfo = {"text" : imgtext, "x" : x, "y" : y, "w" : w, "h" : h, "conf" : conf}
    cv2.imshow('cutom', imgRead)
    cv2.waitKey(0)  






    

def trans_start():
    print("start")
    for FileName in findFileLists : 
        PapagoTranslateWork(FileName)
    messagebox.showinfo("작업완료", "작업이 완료되었습니다")

def Clova_Trans_Start():
    size = 0
    for FileName in findFileLists:
        ClovaFindImageToTextWork(FileName)
        size += 100 / len(findFileLists)
        currProgrssbar.set(size)
        progressbar.update()

def Tessrract_Trans_Start():
    size = 0
    for FileName in findFileLists:
        TesseractFindImageToTextWork(FileName) 
        size += 100 / len(findFileLists)
        currProgrssbar.set(size)
        progressbar.update()


window = tkinter.Tk()

TkinterSet()
DirectoryCheak()
getKeys()

print(f"{Secret_Key} / {APIGW_key} / {Client_ID} / {Client_Secret}")


frame = tkinter.Frame(window)

scrollbar = tkinter.Scrollbar(frame)
scrollbar.pack(side = "right", fill = "y")

list = tkinter.Listbox(frame, yscrollcommand = scrollbar.set)

title = tkinter.Label(window, text = "파일 목록")
line = tkinter.Label(window, text = "----------------------------------------")

title.pack()
line.pack()

with os.scandir("./ImageTranslate/ImageInput") as entries:
    for entry in entries:
        print(entry.name)
        findFiles = entry.name
        if findFiles.endswith(".jpg") or findFiles.endswith(".png") :
            list.insert(END, entry.name)
            findFileLists.append(entry.name)
        # label = tkinter.Label(window, json_ImageText = entry.name)
        # label.pack()

# print(f"list : {findFileLists}")

list.pack(side = "left")

scrollbar["command"] = list.yview

frame.pack()

Clova_transLate_btn = tkinter.Button(window, text = "Clova번역", command = Clova_Trans_Start)
Tesser_transLate_btn = tkinter.Button(window, text = "Tesseract번역", command = Tessrract_Trans_Start)
transLate_btn = tkinter.Button(window, text = "번역하기", command = trans_start)

openFolder = tkinter.Button(window, text = "이미지 경로 열기", command = lambda : OpenDirectory("ImageInput"))

openTextFolder = tkinter.Button(window, text = "번역 텍스트 경로 열기", command = lambda : OpenDirectory("TextOutput"))
refreshBtn = tkinter.Button(window, text = "새로고침", command = refresh)

# openTextFolder = tkinter.Button(window, json_ImageText = "Json 경로 열기", command = lambda : OpenDirectory("JsonOutput"))
# openFolder.config(command = OpenDirectory("ImageTranslate\ImageInput"))
# btn.config(TransLate)
Clova_transLate_btn.pack()
Tesser_transLate_btn.pack()
transLate_btn.pack()
openFolder.pack()
openTextFolder.pack()
refreshBtn.pack()


currProgrssbar = tkinter.DoubleVar()
progressbar = tkinter.ttk.Progressbar(window, maximum = 100, variable = currProgrssbar)
progressbar.pack()



# for FileName in findFileLists:
#     PapagoTranslateWork(FileName)

# for FileName in findFileLists : 
#     PapagoTranslateWork(FileName)


window.mainloop()