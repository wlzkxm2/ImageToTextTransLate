# please install pip

```py

pip install opencv-contrib-python
pip install requests

pip install pillow
pip install pytesseract

```
---
## ***※주의사항※***

**0. 네이버 클로버를 통한 이미지 텍스트추출입니다.**

**1. 네이버 클로버 OCR (이미지 텍스트 추출) 은 100회 이하 무료 이며 그 이상은 회당 3원입니다.**

**2. Papago 번역으로 한 번에 번역할 수 있는 분량은 최대 5,000자이며, 하루 번역 처리 한도는 10,000자입니다.**

**3. 사용자의 과도한 호출및 번역으로 인한 피해는 개발자 본인은 책임지지 않습니다**

**4. 사용자의 프로그램 사용으로 발생하는 모든 피해 는 개발자 본인은 책임지지 않습니다** 

---

---
## 이미지 번역 프로그램 다운로드

[다운로드](https://github.com/wlzkxm2/ImageToTextTransLate/raw/main/ImageTranslator.exe)

---

---
## **프로그램 사용방법**

0. 프로그램을 최초 실행시 키가 없다며 확인해 달라고 합니다. 
그 경우에는 **실행 파일이 있는 곳에 ImageTranslate 폴더에 가시면 Keys.txt 가 있습니다.** 그곳에 키를 넣어주세요

1. 이미지는 \ImageTranslate\ImageInput 폴더에 넣어주세요. 이미지를 인식하는거라 폰트 가독성에 따라서 추출이 제대로 안될 수도 있습니다

2. 추출은 이미지에서 텍스트 추출 -> Json저장 -> Json을 불러와서 번역 -> 번역한 데이터 txt 로 변환 순입니다.

---

---
## **네이버 클로버 키 및 파파고 API키 발급 방법입니다**

[네이버_클로버](https://guide-fin.ncloud-docs.com/docs/ocr-ocr-1-2)

[네이버_클로버_키_발급방법](https://yunwoong.tistory.com/153)

[파파고API](https://developers.naver.com/products/papago/nmt/nmt.md)

[파파고API_키_발급방법01](https://boksup.tistory.com/notice/21)

[파파고API_키_발급방법02](https://developers.naver.com/docs/papago/papago-nmt-overview.md#papago-%EB%B2%88%EC%97%AD)

---

---

## **Change Log**
v1.01
  - tesserect 번역 방법 추가
  - json 출력후 바로 번역하지 않고 txt 파일 출력후 번역
  - gui 변경

---

