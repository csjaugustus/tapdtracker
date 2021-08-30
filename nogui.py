from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pyautogui
import pygetwindow as gw

class ChatWindow():
	def __init__(self, window_title, coords):
		self.title = window_title
		self.window = gw.getWindowsWithTitle(self.title)[0]
		self.x = coords[0]
		self.y = coords[1]

	def update_status(self):
		if gw.getWindowsWithTitle(self.title):
			self.open = True
		else:
			self.open = False

	def send_message(self, msg, times):
		all_windows = gw.getAllWindows()

		for window in all_windows:
			window.minimize()
		self.window.maximize()
		pyautogui.moveTo(self.x, self.y)
		pyautogui.click()
		for i in range(times):
			pyautogui.write(msg)
			pyautogui.press('enter')
		self.window.minimize()

def get_count(text):
	pattern = re.compile("\\d+")
	return pattern.findall(text)[0]

#creating chat windows
while True:
	try:
		duskblade = ChatWindow("Duskblade Critics' Summit", (28,1200))
		qq = ChatWindow("我的Android手机", (28, 1240))
	except IndexError:
		print("One of the required windows is not open. Please ensure they are open.")
		input("Press any key to continue.\n")
	else:
		break
to_send = [duskblade, qq]

#launch webdriver
driver = webdriver.Chrome()
driver.get("https://www.tapd.cn/43882502")

try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
finally:
	username_box = driver.find_element_by_id("username")
	password_box = driver.find_element_by_id("password_input")
	username_box.send_keys("15578073443")
	password_box.send_keys("antifuckingh4ck!")
	login_button = driver.find_element_by_id("tcloud_login_button")
	login_button.click()

try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "list-count"))
    )
finally:
	list_count_el = driver.find_element_by_class_name('list-count')
	initial_count = get_count(list_count_el.text)
	

n = 0
while True:
	try:
	    WebDriverWait(driver, 10).until(
	        EC.presence_of_element_located((By.CLASS_NAME, "list-count"))
	        )
	finally:
		for cw in to_send:
			cw.update_status()

		ready = []
		for cw in to_send:
			if cw.open:
				ready.append(cw)
		print(f"Windows ready: {', '.join(cw.title for cw in ready)}")
		print(f"Initial count: {initial_count}")


		list_count_el = driver.find_element_by_class_name('list-count')
		unclaimed_count = get_count(list_count_el.text)
		print(f"Current count: {unclaimed_count}")
		if unclaimed_count != initial_count:
			if unclaimed_count == "0":
				for cw in to_send:
					if cw.open:
						cw.send_message('UNCLAIMED VIDEOS HAVE BEEN CLEARED TO 0. STANDBY FOR UPDATE.')
			elif unclaimed_count > initial_count:
				print("UPDATED")
				for cw in to_send:
					if cw.open:
						cw.send_message('TAPD HAS BEEN UPDATED. https://www.tapd.cn/43882502', 3)
				tapd_window = gw.getWindowsWithTitle('看板-人人视频线上翻译-TAPD平台 - Google Chrome')[0]
				tapd_window.maximize()				
				break
		print(f"REFRESHING{n%2*'*'}")
		driver.refresh()
		n += 1