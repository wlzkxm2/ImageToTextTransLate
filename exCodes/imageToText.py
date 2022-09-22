import re
from unittest import mock
from xml.etree.ElementTree import PI
import pytesseract
from PIL import Image
import PIL.Image
from manga_ocr import MangaOcr

paths = r'C:\Program Files\Tesseract-OCR\tesseract'

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

photo = Image.open(r'C:\Users\netk\Desktop\pyProject\data\jpnmantest02.jpg')
result = pytesseract.image_to_string(photo, lang='jpn_vert_fast')
print(result)

# manga_ocr.MangaOcr(paths)

# mocr = MangaOcr()
# img = PIL.Image.open('./data/jpnmantest02.jpg')
# text = mocr(img)
# print(text)