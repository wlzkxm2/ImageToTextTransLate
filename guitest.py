from distutils import file_util
from fileinput import filename
from tkinter import *
import os
import tkinter

import json
import base64
from subprocess import call
from tkinter import messagebox
import requests
import re

from fnmatch import translate
import pandas as pd
import sys
import urllib.request

# ImageTranslate 기본 디렉토리
# ImageInput 번역할 이미지
# JsonOutput 추출된 Json
# TextOutput 번역된


findFileLists = []

def createDirectory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print("Error: Failed to create the directory.")

def OpenDirectory(where):
    directory = "ImageTranslate\\" + where
    try:
        if os.path.exists(directory):
            os.startfile(directory)
    except OSError:
        messagebox.showinfo("폴더가 없음", "해당 폴더를 찾을 수 없습니다. 프로그램을 재시작해주세요")

def TkinterSet():
    window.title("ImageTranslate")
    window.geometry("300x300")
    window.resizable(False, False)

def Main():
    global findFileLists
    createDirectory("ImageTranslate")
    createDirectory("ImageTranslate\ImageInput")
    createDirectory("ImageTranslate\JsonOutput")
    createDirectory("ImageTranslate\TextOutput")

    # file_list = glob.glob(r"data\*.jpg")
    # print(file_list)
    # file_list += glob.glob(r"data\*.png")
    # print(file_list)

    frame = tkinter.Frame(window)

    scrollbar = tkinter.Scrollbar(frame)
    scrollbar.pack(side = "right", fill = "y")

    list = tkinter.Listbox(frame, yscrollcommand = scrollbar.set)

    title = tkinter.Label(window, text = "파일 목록")
    line = tkinter.Label(window, text = "----------------------------------------")

    title.pack()
    line.pack()

    with os.scandir("data") as entries:
        for entry in entries:
            print(entry.name)
            findFiles = entry.name
            if findFiles.endswith(".jpg") or findFiles.endswith(".png") :
                list.insert(END, entry.name)
                findFileLists.append(entry.name)
            # label = tkinter.Label(window, text = entry.name)
            # label.pack()

    # print(f"list : {findFileLists}")

    list.pack(side = "left")

    scrollbar["command"] = list.yview

    frame.pack()

    transLate_btn = tkinter.Button(window, text = "번역하기")
    openFolder = tkinter.Button(window, text = "이미지 경로 열기", command = lambda : OpenDirectory("ImageInput"))
    openTextFolder = tkinter.Button(window, text = "번역 텍스트 경로 열기", command = lambda : OpenDirectory("TextOutput"))
    # openTextFolder = tkinter.Button(window, text = "Json 경로 열기", command = lambda : OpenDirectory("JsonOutput"))
    # openFolder.config(command = OpenDirectory("ImageTranslate\ImageInput"))
    # btn.config(TransLate)
    transLate_btn.pack()
    openFolder.pack()
    openTextFolder.pack()

def FindImageToTextWork(filename) :
    position = filename.find(".")
    filenameNotdot = filename[:position]
    # print(filenameNotdot)

    filepath = r'ImageTranslate\JsonOutput\\' + filenameNotdot + ".json"

    with open(r"C:\Users\netk\Desktop\pyProject\data\\" + filename , "rb") as f:
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

class TranslateWork(filename) :
    position = filename.find(".")
    filenameNotdot = filename[:position]

    path = './ImageTranslate/JsonOutput/' + filenameNotdot + '.json'
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
            TranslateWork.AfterTreatment(transjson)
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


        

window = tkinter.Tk()

TkinterSet()
Main()

# for FileName in findFileLists:
#     TranslateWork(FileName)


window.mainloop()