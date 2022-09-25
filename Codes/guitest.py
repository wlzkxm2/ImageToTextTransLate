from distutils import file_util
from distutils.cmd import Command
from distutils.command.config import config
from fileinput import filename
from textwrap import fill
from tkinter import *
import os
import tkinter

import json
import base64
from subprocess import call
from tkinter import messagebox
from tkinter import ttk
from tkinter.tix import COLUMN
from unittest import result
from xml.etree.ElementPath import findtext
import requests

import urllib.request

import pytesseract as pyt
import cv2
from pytesseract import Output

from PIL import ImageTk, Image
import math
import warnings

from manga_ocr import MangaOcr


# ImageTranslate 기본 디렉토리
# ImageInput 번역할 이미지
# JsonOutput 추출된 Json
# TextOutput 번역된

class AutoScrollbar(ttk.Scrollbar):
    """ A scrollbar that hides itself if it's not needed. Works only for grid geometry manager """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tkinter.TclError('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        raise tkinter.TclError('Cannot use place with the widget ' + self.__class__.__name__)

class CanvasImage:
    """ Display and zoom image """
    def __init__(self, placeholder, path):
        """ Initialize the ImageFrame """
        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes
        self.__delta = 1.3  # zoom magnitude
        self.__filter = Image.ANTIALIAS  # could be: NEAREST, BILINEAR, BICUBIC and ANTIALIAS
        self.__previous_state = 0  # previous state of the keyboard
        self.path = path  # path to the image, should be public for outer classes
        # Create ImageFrame in placeholder widget
        self.__imframe = ttk.Frame(placeholder)  # placeholder of the ImageFrame object
        # Vertical and horizontal scrollbars for canvas
        hbar = AutoScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoScrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')
        # Create canvas and bind it with scrollbars. Public for outer classes
        self.canvas = tkinter.Canvas(self.__imframe, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        hbar.configure(command=self.__scroll_x)  # bind scrollbars to the canvas
        vbar.configure(command=self.__scroll_y)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', lambda event: self.__show_image())  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.__move_from)  # remember canvas position
        self.canvas.bind('<B1-Motion>',     self.__move_to)  # move canvas to the new position
        self.canvas.bind('<MouseWheel>', self.__wheel)  # zoom for Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.__wheel)  # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.__wheel)  # zoom for Linux, wheel scroll up
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # when too many key stroke events in the same time
        self.canvas.bind('<Key>', lambda event: self.canvas.after_idle(self.__keystroke, event))
        # Decide if this image huge or not
        self.__huge = False  # huge or not
        self.__huge_size = 14000  # define size of the huge image
        self.__band_width = 1024  # width of the tile band
        Image.MAX_IMAGE_PIXELS = 1000000000  # suppress DecompressionBombError for the big image
        with warnings.catch_warnings():  # suppress DecompressionBombWarning
            warnings.simplefilter('ignore')
            self.__image = Image.open(self.path)  # open image, but down't load it
        self.imwidth, self.imheight = self.__image.size  # public for outer classes
        if self.imwidth * self.imheight > self.__huge_size * self.__huge_size and \
           self.__image.tile[0][0] == 'raw':  # only raw images could be tiled
            self.__huge = True  # image is huge
            self.__offset = self.__image.tile[0][2]  # initial tile offset
            self.__tile = [self.__image.tile[0][0],  # it have to be 'raw'
                           [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                           self.__offset,
                           self.__image.tile[0][3]]  # list of arguments to the decoder
        self.__min_side = min(self.imwidth, self.imheight)  # get the smaller image side
        # Create image pyramid
        self.__pyramid = [self.smaller()] if self.__huge else [Image.open(self.path)]
        # Set ratio coefficient for image pyramid
        self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size if self.__huge else 1.0
        self.__curr_img = 0  # current image from the pyramid
        self.__scale = self.imscale * self.__ratio  # image pyramide scale
        self.__reduction = 2  # reduction degree of image pyramid
        w, h = self.__pyramid[-1].size
        while w > 512 and h > 512:  # top pyramid image is around 512 pixels in size
            w /= self.__reduction  # divide on reduction degree
            h /= self.__reduction  # divide on reduction degree
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)), self.__filter))
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
        self.__show_image()  # show image on the canvas
        self.canvas.focus_set()  # set focus on the canvas

    def smaller(self):
        """ Resize image proportionally and return smaller image """
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2  # it equals to 1.0
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(w2)  # band length
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1  # compression ratio
            w = int(w2)  # band length
        else:  # aspect_ratio1 < aspect_ration2
            image = Image.new('RGB', (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(h2 * aspect_ratio1)  # band length
        i, j, n = 0, 1, round(0.5 + self.imheight / self.__band_width)
        while i < self.imheight:
            print('\rOpening image: {j} from {n}'.format(j=j, n=n), end='')
            band = min(self.__band_width, self.imheight - i)  # width of the tile band
            self.__tile[1][3] = band  # set band width
            self.__tile[2] = self.__offset + self.imwidth * i * 3  # tile offset (3 bytes per pixel)
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]  # set tile
            cropped = self.__image.crop((0, 0, self.imwidth, band))  # crop tile band
            image.paste(cropped.resize((w, int(band * k)+1), self.__filter), (0, int(i * k)))
            i += band
            j += 1
        print('\r' + 30*' ' + '\r', end='')  # hide printed string
        return image

    def redraw_figures(self):
        """ Dummy function to redraw figures in the children classes """
        pass

    def grid(self, **kw):
        """ Put CanvasImage widget on the parent widget """
        self.__imframe.grid(**kw)  # place CanvasImage widget on the grid
        self.__imframe.grid(sticky='nswe')  # make frame container sticky
        self.__imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """ Exception: cannot use pack with this widget """
        raise Exception('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        """ Exception: cannot use place with this widget """
        raise Exception('Cannot use place with the widget ' + self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def __show_image(self):
        """ Show image on the Canvas. Implements correct image zoom almost like in Google Maps """
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0),  # get visible area of the canvas
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])]
        # Horizontal part of the image is in the visible area
        if  box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0]  = box_img_int[0]
            box_scroll[2]  = box_img_int[2]
        # Vertical part of the image is in the visible area
        if  box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1]  = box_img_int[1]
            box_scroll[3]  = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            if self.__huge and self.__curr_img < 0:  # show huge image
                h = int((y2 - y1) / self.imscale)  # height of the tile band
                self.__tile[1][3] = h  # set the tile band height
                self.__tile[2] = self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                self.__image.close()
                self.__image = Image.open(self.path)  # reopen / reset image
                self.__image.size = (self.imwidth, h)  # set size of the tile band
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:  # show normal image
                image = self.__pyramid[max(0, self.__curr_img)].crop(  # crop current img from pyramid
                                    (int(x1 / self.__scale), int(y1 / self.__scale),
                                     int(x2 / self.__scale), int(y2 / self.__scale)))
            #
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))
            imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

    def __move_from(self, event):
        """ Remember previous coordinates for scrolling with the mouse """
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        """ Drag (move) canvas to the new position """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # zoom tile and show it on the canvas

    def outside(self, x, y):
        """ Checks if the point (x,y) is outside the image area """
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area

    def __wheel(self, event):
        """ Zoom with mouse wheel """
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down, smaller
            if round(self.__min_side * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.__delta
            scale        /= self.__delta
        if event.num == 4 or event.delta == 120:  # scroll up, bigger
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.__delta
            scale        *= self.__delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes
        self.__show_image()

    def __keystroke(self, event):
        """ Scrolling with the keyboard.
            Independent from the language of the keyboard, CapsLock, <Ctrl>+<key>, etc. """
        if event.state - self.__previous_state == 4:  # means that the Control key is pressed
            pass  # do nothing if Control key is pressed
        else:
            self.__previous_state = event.state  # remember the last keystroke state
            # Up, Down, Left, Right keystrokes
            if event.keycode in [68, 39, 102]:  # scroll right: keys 'D', 'Right' or 'Numpad-6'
                self.__scroll_x('scroll',  1, 'unit', event=event)
            elif event.keycode in [65, 37, 100]:  # scroll left: keys 'A', 'Left' or 'Numpad-4'
                self.__scroll_x('scroll', -1, 'unit', event=event)
            elif event.keycode in [87, 38, 104]:  # scroll up: keys 'W', 'Up' or 'Numpad-8'
                self.__scroll_y('scroll', -1, 'unit', event=event)
            elif event.keycode in [83, 40, 98]:  # scroll down: keys 'S', 'Down' or 'Numpad-2'
                self.__scroll_y('scroll',  1, 'unit', event=event)

    def crop(self, bbox):
        """ Crop rectangle from the image and return it """
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3  # set offset of the band
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # image is totally in RAM
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ ImageFrame destructor """
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # close all pyramid images
        del self.__pyramid[:]  # delete pyramid list
        del self.__pyramid  # delete pyramid variable
        self.canvas.destroy()
        self.__imframe.destroy()

class MainWindow(ttk.Frame):
    """ Main window class """
    def __init__(self, mainframe, path):
        """ Initialize the main Frame """
        ttk.Frame.__init__(self, master=mainframe)
        # self.master.title('Advanced Zoom v3.0')
        # self.master.geometry('1280x720')  # size of the main window
        self.master.rowconfigure(0, weight=100) # make the CanvasImage widget expandable
        self.master.columnconfigure(0, weight=100)
        canvas = CanvasImage(self.master, path)  # create widget
        
        canvas.grid(column = 1, row = 3, rowspan = 10, columnspan = 10, padx = 20, pady = 20)  # show widget


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
    # window.geometry("800x800")
    window.resizable(False, False)

def DirectoryCheak():
    createDirectory("ImageTranslate")
    createDirectory("ImageTranslate\ImageInput")
    createDirectory("ImageTranslate\JsonOutput")
    createDirectory("ImageTranslate\TextOutput")
    createDirectory("data")
    

# 클로바 OCR 추출
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

    # print(callText)
            

    # print(res[3])


    # Json 파일로 덤프
    with open(filepath, 'w', encoding='UTF8') as f:
        f.write(json.dumps(res, ensure_ascii = False))

    # 덤프한 파일을 불러옴
    path = './ImageTranslate/JsonOutput/' + filenameNotdot + '.json'
    with open(path , 'r', encoding='UTF8') as file:
        data = json.load(file)

    # Json 파일 내부 텍스트를 담기위한 string
    json_ImageText = ""

    # Json 텍스트 정보 담기
    for j in range(len(data['images'][0]['fields'])) :
        for i in data['images'][0]['fields'][j]['inferText']:
            json_ImageText += i
        json_ImageText += "/"

    # 텍스트 정보가 담긴 string 을 텍스트 파일로 추출
    with open("./ImageTranslate/JsonOutput/" + filenameNotdot + "_OCR.txt", "w", encoding="UTF-8") as file :
        # for name in json_ImageText :
        file.write(json_ImageText)

def PapagoTranslateWork(filename) :
    # filename : ex.jpg 
    # filenameNotdot : ex
    global TransOutputText

    position = filename.find(".")
    filenameNotdot = filename[:position]  
    # print(f"input : {filename}")      
    # print(f"filenameNotdot : {filenameNotdot}")      

    # path = './ImageTranslate/JsonOutput/' + filenameNotdot + '.json'
    path = './ImageTranslate/JsonOutput/' + filenameNotdot + '_OCR.txt'
    file_path = r'\ImageTranslate\JsonOutput\\' + filenameNotdot + '.json'

    TransOutputText = []
    # with open(path , 'r', encoding='UTF8') as file:
    #     data = json.load(file)

    target_OCRImgText = ""     # 텍스트를 담기위한 string

    # OCR 텍스트 파일 불러오기
    OCRText = open(path, "r", encoding="UTF-8")
    # while True :
    #     target_OCRImgText = OCRText.read()
    #     if not target_OCRImgText: break
    #     print(target_OCRImgText)
    # OCRText.close()
    target_OCRImgText = OCRText.read()
    
    print(type(target_OCRImgText))
    print(target_OCRImgText)

    # print("---------------------------------------------------------")
    # print(f"fileType : {type(data)}")
    # print("---------------------------------------------------------")

    # if(type(data) == dict):
    #     for j in range(len(data['images'][0]['fields'])) :
    #         for i in data['images'][0]['fields'][j]['inferText']:
    #             json_ImageText += i
    #         json_ImageText += "\n"
    # else:
    #     json_ImageText = data 
  

    # JAtoKO(json_ImageText)
    client_id = Client_ID # 개발자센터에서 발급받은 Client ID 값
    client_secret = Client_Secret # 개발자센터에서 발급받은 Client Secret 값
    jatext = urllib.parse.quote(target_OCRImgText)
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
    position = filename.find(".")
    filenameNotdot = filename[:position]  
    pyt.pytesseract.tesseract_cmd = r"data\tesseract-ocr\tesseract"
    imgPath = r"ImageTranslate\ImageInput\\" + filename
    # config = ("-l jpn-vert --oem 3 --psm 11")
    text = pyt.image_to_string(imgPath, lang = "jpn_vert")
    print("-----------------------------")
    print(text)
    print("-----------------------------")

    with open("./ImageTranslate/JsonOutput/" + filenameNotdot + "_OCR.txt", "w", encoding="UTF-8") as file :
        for name in TransOutputText :
            file.write(name + '/')

    # json 생성
    # Tesser_json = Orderedict()

    
    # imgRead = cv2.imread(imgPath)
    # imgResult = pyt.image_to_data(imgRead, output_type=Output.DICT)
    # print(imgResult)

    # json_imgInfo = {
    #     "text" : findtext,
    #     "x" : x,
    #     "y" : y,
    #     "w" : w,
    #     "h" : h
    # }

    # print(json_imgInfo.values)

    # for i in range(0, len(imgResult["text"])):
    #     x = imgResult["left"][i]
    #     y = imgResult["top"][i]

    #     w = imgResult["width"][i]
    #     h = imgResult["height"][i]

    #     imgtext = imgResult["text"][i]
    #     conf = int(imgResult["conf"][i])
    #     if conf < 0:
    #         imgtext = "".join([c if ord(c) < 128 else "" for c in imgtext]).strip()
    #         cv2.rectangle(imgRead, (x, y), (x + w, y + h), (0, 255, 0), 1)
    # cv2.imshow('cutom', imgRead)
    # cv2.waitKey(0)  


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


def ItemView():
    imgPath = r"ImageTranslate\ImageInput\\" + list.get(list.curselection())
    # 선택한 아이템의 이름을 불러오기
    print(f"{list.get(list.curselection())}")
    # selectedImgView = ImageTk.PhotoImage(Image.open(imgPath))    
    # imgCanv.create_image([0, 0], anchor = tkinter.NW, image = selectedImgView)
    # mocr = MangaOcr()
    # text = mocr(imgPath)
    # print(text)
    

window = tkinter.Tk()

TkinterSet()
DirectoryCheak()
getKeys()

print(f"{Secret_Key} / {APIGW_key} / {Client_ID} / {Client_Secret}")


frame = tkinter.Frame(window)

scrollbar = tkinter.Scrollbar(frame)
# scrollbar.pack(side = "right", fill = "y")
scrollbar.grid(column = 1, row = 3, padx = 5, pady = 5 )        # 스크롤바

list = tkinter.Listbox(frame, yscrollcommand = scrollbar.set, selectmode="extended")

title = tkinter.Label(window, text = "파일 목록")
# line = tkinter.Label(window, text = "----------------------------------------")
tkinter.ttk.Separator(window, orient=HORIZONTAL).grid(column=0, row=2, columnspan=1, sticky='ew')

# title.pack()
# line.pack()

title.grid(column = 0, row = 1, padx = 5, pady = 5 )
# line.grid(column = 0, row = 2, padx = 5, pady = 5 )

# 이미지를 폴더 안에서 찾는 과정
with os.scandir("./ImageTranslate/ImageInput") as entries:
    for entry in entries:
        print(entry.name)
        findFiles = entry.name
        if findFiles.endswith(".jpg") or findFiles.endswith(".png") or findFiles.endswith(".PNG") or findFiles.endswith(".JPG") :
            list.insert(END, entry.name)
            findFileLists.append(entry.name)
        # label = tkinter.Label(window, json_ImageText = entry.name)
        # label.pack()

# print(f"list : {findFileLists}")

# list.pack(side = "left")
list.grid(column = 0, row = 3, padx = 5, pady = 5 )

scrollbar["command"] = list.yview

# frame.pack(side = "left")
frame.grid(column = 0, row = 4, padx = 5, pady = 5 )

# 이미지 출력을 위한 캠버스
# imgCanv = tkinter.Canvas(window, width = 500, height = 300, bg = "white")
# imgCanv.grid(column = 2, row = 4, padx = 5, pady = 5)
# selectedImgView = ImageTk.PhotoImage(Image.open(r"ImageTranslate\ImageInput\mantest03.jpg"))    
# imgCanv.create_image(0, 0, anchor = tkinter.NW, image = selectedImgView)

tkinter.ttk.Separator(window, orient=HORIZONTAL).grid(column=1, row=17, columnspan=3, sticky='ew')
# tkinter.ttk.Separator(window, orient=VERTICAL).grid(column=1, row=7, rowspan=2, sticky='ns')

Clova_transLate_btn = tkinter.Button(window, text = "Clova번역", command = Clova_Trans_Start)
Clova_transLate_btn.grid(column = 1, row = 18, padx = 5, pady = 5 )

Tesser_transLate_btn = tkinter.Button(window, text = "Tesseract번역", command = Tessrract_Trans_Start)
Tesser_transLate_btn.grid(column = 2, row = 18, padx = 5, pady = 5 )


tkinter.ttk.Separator(window, orient=HORIZONTAL).grid(column=1, row=19, columnspan=3, sticky='ew')

transLate_btn = tkinter.Button(window, text = "번역하기", command = trans_start)
transLate_btn.grid(column = 2, row = 20, padx = 5, pady = 5 )

openFolder = tkinter.Button(window, text = "이미지 경로 열기", command = lambda : OpenDirectory("ImageInput"))
openFolder.grid(column = 1, row = 21, padx = 5, pady = 5 )

openTextFolder = tkinter.Button(window, text = "번역 텍스트 경로 열기", command = lambda : OpenDirectory("TextOutput"))
openTextFolder.grid(column = 3, row = 21, padx = 5, pady = 5 )

openTextFolder = tkinter.Button(window, text = "아이템 이름", command = ItemView)
openTextFolder.grid(column = 2, row = 22, padx = 5, pady = 5 )

refreshBtn = tkinter.Button(window, text = "새로고침", command = refresh)
refreshBtn.grid(column = 0, row = 5, padx = 5, pady = 5 )




currProgrssbar = tkinter.DoubleVar()
progressbar = tkinter.ttk.Progressbar(window, maximum = 100, variable = currProgrssbar)
# progressbar.pack()
progressbar.grid(column = 0, row = 6, padx = 5, pady = 5 )



# for FileName in findFileLists:
#     PapagoTranslateWork(FileName)

# for FileName in findFileLists : 
#     PapagoTranslateWork(FileName)

# app = MainWindow(window, path = "ImageTranslate\ImageInput\mantest03.jpg")
# app.grid(column = 3, row = 4, padx = 5, pady = 5)

window.mainloop()