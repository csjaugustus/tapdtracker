# TAPD Tracker
Tracks when TAPD updates and then sends a message to target chat windows.<br/>
Can also auto-claim videos containing certain keywords.<br/>
chromedriver.exe only works for Chrome v97. Visit https://chromedriver.chromium.org/downloads to get the correct version.<br/>
Dependencies: Selenium, pyautogui, pygetwindow, Pillow, pynput, pyperclip, pywin32, opencv-python.

## Table of Contents
* [Installation](#installation)
* [Setup](#setup)
* [Main Interface](#main-interface)
* [Inputting Login Details](#inputting-login-details)
* [Managing Send Locations](#managing-send-locations)
* [Manual Send](#manual-send)
* [Auto Claim](#auto-claim)
* [Click Coords](#click-coords)

## Installation
In your command prompt:
```
git clone https://github.com/csjaugustus/tapdtracker.git
```
```
cd tapdtracker
```
```
pip install -r requirements.txt
```
```
main.py
```
Note: If installing from requirements.txt gives you errors, try installing all the dependencies manually.

## Setup
1. Input your login details in settings.<br/>
2. Register at least one target window in settings. You can choose not to activate the registered window.<br/>
3. If you wish to auto claim videos, set keywords in the auto claim menu.<br/>
Note: Target windows and keywords can be edited during runtime. But login details cannot be changed once the program starts running.

## Main Interface
<img src="https://user-images.githubusercontent.com/61149391/153204300-6d32495b-43bb-4e29-b2fa-f0d18ef6dfba.png" width=25% height=25%>
Once program is started, the program will keep tracking for updates. The light indicator will be green if all activated windows are open. Otherwise a red light will be shown. Once an update is detected, an update message will be sent to all activated windows. If auto-claim is on, it will automatically claim videos containing the keywords.

## Inputting Login Details
<img src="https://user-images.githubusercontent.com/61149391/128975645-f6e6de62-37af-40b8-aef3-2598ce0346db.png" width=25% height=25%>

## Managing Send Locations
<img src="https://user-images.githubusercontent.com/61149391/153374062-114f9677-9097-4186-b93b-ce405baa35b0.png" width=25% height=25%>
Program will save window locations for sending messages. To get coords, simply click on "Get Coords", then click your desired area, and the coords will be filled in automatically. Window activation status is updated in real time, even when the program is running.

## Manual Send
<img src="https://user-images.githubusercontent.com/61149391/128976079-54e5a5e5-09c9-4987-836a-baeaa8b87d0c.png" width=25% height=25%>
Allows you to manually send a message to the activated windows. 

## Auto Claim
<img src="https://user-images.githubusercontent.com/61149391/153204636-e5404b1e-cc63-4e0d-9738-bb0bdfbe45ba.png" width=25% height=25%>
Allows you to input keywords to claim and not to claim. There is also a claim-all toggle to claim all videos except those on the not-to-claim list.

## Click Coords
<img src="https://user-images.githubusercontent.com/61149391/153373661-3914c9b4-df4b-402c-8c57-aeae77479317.png" width=25% height=25%>
Provide the coordinates necessary for auto-claim feature. You need to provide 2 sets of coordinates, one of the comment box, one of any area outside the comment box (to close the popup window). Simply click on "Get Coords", then click your desired area, and the coords will be filled in automatically.


