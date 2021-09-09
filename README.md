# MyTube

## Description 

A Python-based Youtube video downloader. <br/>
Provides a GUI for the user to download a single video, an entire channel or playlist with up to 720p resolution.


<br/>

## Table of contents
- [Prerequisites](#prerequisites)
- [Get started](#get-started)
- [Troubleshooting](#troubleshooting)
- [Author](#author)
- [License](#license)

<br/>
<br/>

---

## PREREQUISITES
Besides having Python 3 (made with Python 3.9) installed, you also need:
```bash
pip install helium

pip install beautifulsoup4

pip install pytube
```

<br/>

---

## GET STARTED

<br/>

### **Standalone executable**
Build a standalone executable with PyInstaller: ```pip install pyinstaller```<br/>
Run the following command from project folder<br/> ```pyinstaller --onefile --noconsole -n "MyTube" --icon "icon.ico" --add-data "icon.ico;." --collect-all "helium"  mytube_app.py```

<br/>

---

<br/>

## **Troubleshooting**
This project relies heavily on PyTube.<br/>
Make sure pytube is updated: ```pip install pytube --upgrade```

<br/>

---

## Author
**Kristian Hviid Nielsen** - [Github](https://github.com/kristianhnielsen)

<br/>

---

## License
See [License](https://github.com/kristianhnielsen/MyTube/edit/main/LICENSE)