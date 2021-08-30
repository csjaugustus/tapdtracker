# TAPD Tracker
Tracks when TAPD updates and then sends a message to target chat windows.
Chrome driver only works for Chrome v92. Visit https://chromedriver.chromium.org/downloads to get the correct version.

## Table of Contents
* [Installation](#installation)
* [Main Interface](#main-interface)
* [Inputting Login Details](#inputting-login-details)
* [Managing Send Locations](#managing-send-locations)
* [Manual Send](#manual-send)

## Installation
```
$ git clone https://github.com/csjaugustus/tapdtracker.git
```
```
$ pip install -r requirements.txt
```
```
$ main.py
```

## Main Interface
<img src="https://user-images.githubusercontent.com/61149391/128975527-03b2944c-b29c-4fe1-b075-4f1c3a071fde.png" width=25% height=25%>
Once program is started, the program will keep tracking for updates. The light indicator will be green if all activated windows are open. Otherwise a red light will be shown. Once an update is detected, an update message will be sent to all activated windows.

## Inputting Login Details
<img src="https://user-images.githubusercontent.com/61149391/128975645-f6e6de62-37af-40b8-aef3-2598ce0346db.png" width=25% height=25%>

## Managing Send Locations
<img src="https://user-images.githubusercontent.com/61149391/128975939-a3a53300-377f-4eb4-ad78-c33c66c256bb.png" width=25% height=25%>
Program will save window locations for sending messages. To get coordinates, launch get_coords.py. Window activation status is updated in real time, even when the program is running.

## Manual Send
<img src="https://user-images.githubusercontent.com/61149391/128976079-54e5a5e5-09c9-4987-836a-baeaa8b87d0c.png" width=25% height=25%>
Allows you to manually send a message to the activated windows. 



