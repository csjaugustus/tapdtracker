from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pyautogui
import pygetwindow as gw
import tkinter as tk
from tkinter import ttk
import threading
import json
import os
from PIL import Image, ImageTk
import time
import datetime
import traceback
import pyperclip
from pynput import mouse
import webbrowser
from image_copying import list_to_image
from image_detection import detect_image, crop_full, click_image
from screen_record import start_record

def login(url, driver, username, password):
	"""Uses a driver to log onto a TAPD board."""
	driver.get(url)
	try:
		WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, "username"))
		)
	finally:
		username_box = driver.find_element(By.ID, "username")
		password_box = driver.find_element(By.ID, "password_input")
		username_box.send_keys(username)
		password_box.send_keys(password)
		login_button = driver.find_element(By.ID, "tcloud_login_button")
		login_button.click()

def popupMessage(title, message, windowToClose=None):
	"""
	Sends a popup message. 
	By default, acknowledging the popup message only closes the popup message itself. 
	But you can pass in what other windows to close too.
	For a fatal error that should close all windows, pass in 'all'.
	"""

	popupWindow = tk.Toplevel()
	popupWindow.resizable(False, False)
	popupWindow.title(title)
	if not windowToClose:
		close = popupWindow.destroy
	elif windowToClose == 'all':
		close = popupWindow.quit
	else:
		def close():
			popupWindow.destroy()
			windowToClose.destroy()
	msg = ttk.Label(popupWindow, text=message)
	ok = ttk.Button(popupWindow, text="Ok", command=close)
	msg.pack(padx=10, pady=10)
	ok.pack(padx=10, pady=10)

class ChatWindow:
	"""
	A chat window class that manages chat windows.
	It can store attributes of a chat window, including its coordinates and open status.
	It also has methods to update its status, or send messages to it.
	"""

	def __init__(self, window_title, coords):
		self.title = window_title
		self.x = coords[0]
		self.y = coords[1]

	def update_status(self):
		if gw.getWindowsWithTitle(self.title):
			self.open = True
		else:
			self.open = False

	def send(self, msg, times, to_img_list=False, img_title=None, user_imgs=None):
		window = gw.getWindowsWithTitle(self.title)[0]
		all_windows = gw.getAllWindows()

		for w in all_windows:
			w.minimize()
		window.maximize()
		pyautogui.moveTo(self.x, self.y)
		pyautogui.click()
		if not to_img_list:
			for i in range(times):
				pyautogui.write(msg)
				pyautogui.press('enter')
		else:
			if user_imgs and img_title:
				list_to_image(msg, img_title, user_imgs)
			elif img_title:
				list_to_image(msg, img_title) #copies image to clipboard
			else:
				list_to_image(msg)
			for i in range(times):
				pyautogui.hotkey("ctrl", "v")
				pyautogui.press('enter')

		window.minimize()

class App(ttk.Frame):
	"""
	The main application window.
	Tracking and auto-claiming happen here.
	"""

	def __init__(self, parent):
		ttk.Frame.__init__(self, parent)
		self.parent = parent
		self.t = threading.Thread(target=self.track)

		#variables
		self.pin = tk.BooleanVar(value=False)
		self.status = tk.StringVar(value="Status: Program not running.")
		self.output = tk.StringVar(value="No output.")

		self.load_imgs()
		self.setup_widgets()

	def initial_check(self):
		"""Checks that all the necessary information is ready before starting."""

		login_details = Database("login_details.json")
		windows_info = Database("windows_info.json")
		auto_claim_info = Database("auto_claim_info.json")
		click_coords = Database("click_coords.json")

		errors = []
		if not login_details.data:
			errors.append("Please input login details.")
		elif not any(login_details.data[p]["selected"] for p in login_details.data):
			errors.append("No preset selected in login details.")
		if not auto_claim_info.data:
			auto_claim_info.data = {
			"all_state" : False,
			"keywords" : [],
			"negative_keywords" :[],
			}
			auto_claim_info.save()

			if not any(windows_info.data[name]['activated'] for name in windows_info.data):
				errors.append("Please have at least one activated window to send messages to.")
		else:
			if not click_coords.data:
				errors.append("Please input click coords for auto claim.")

		if errors:
			popupMessage("Error(s)", "\n\n".join(e for e in errors))
			return False

		for p in login_details.data:
			if login_details.data[p]["selected"]:
				self.name = p
				self.username = login_details.data[p]['username']
				self.password = login_details.data[p]['password']
				self.url = f"https://www.tapd.cn/{login_details.data[p]['tapd_id']}"
		self.comment_x_coord = click_coords.data['comment_x_coord']
		self.comment_y_coord = click_coords.data['comment_y_coord']
		self.close_x_coord = click_coords.data['close_x_coord']
		self.close_y_coord = click_coords.data['close_y_coord']
		return True

	def start(self):
		if self.initial_check():
			self.t.start()

	def load_imgs(self):
		self.red_light = Image.open("files\\redlight.png")
		self.red_light = self.red_light.resize((20, 20))
		self.red_light = ImageTk.PhotoImage(self.red_light)
		self.green_light = Image.open("files\\greenlight.png")
		self.green_light = self.green_light.resize((20, 20))
		self.green_light = ImageTk.PhotoImage(self.green_light)		

	def setup_widgets(self):
		self.light_label = tk.Label(self, image=self.red_light)
		self.pin_button = ttk.Checkbutton(self, text="Pin", variable=self.pin, style="Switch.TCheckbutton")
		self.status_label = ttk.Label(self,textvariable=self.status)
		self.output_label = ttk.Label(self, textvariable=self.output, borderwidth=10, relief="groove")
		self.start_button = ttk.Button(self, text="Start", command=self.start)
		self.pb = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=300, mode="indeterminate")

		self.pin_button.bind("<Button-1>", self.pin_window)

		self.light_label.grid(row=0, column=0, sticky=tk.W)
		self.pin_button.grid(row=0, column=2, sticky=tk.E)
		self.status_label.grid(row=1, column=0, columnspan=3, padx=20,pady=10)
		self.output_label.grid(row=2, column=0, columnspan=3, padx=20, pady=10)
		self.start_button.grid(row=4, column=0, columnspan=3, pady=10)

	def update_to_send(self):
		"""Updates send list during runtime."""
		self.to_send = []

		windows_info = Database("windows_info.json")
		for name, attrs in windows_info.data.items():
			activated = attrs['activated']
			if activated:
				coords = attrs['coords']
				cw = ChatWindow(name, coords)
				self.to_send.append(cw)

	def update_kw_list(self):
		"""Updates keyword list during runtime."""
		self.auto_claim_info = Database("auto_claim_info.json")
		self.all_state = self.auto_claim_info.data["all_state"]
		if self.all_state:
			self.keywords = "all"
		else:
			self.keywords = self.auto_claim_info.data["keywords"]
		self.negative_keywords = self.auto_claim_info.data["negative_keywords"]


	def pin_window(self, event):
		if not self.pin.get():
			self.parent.attributes("-topmost", True)
		else:
			self.parent.attributes("-topmost", False)

	def change_light(self, colour):
		if colour == "red":
			self.light_label.configure(image=self.red_light)
			self.light_label.image = self.red_light
			self.light_label.grid(row=0, column=0, sticky=tk.W)
		elif colour == "green":
			self.light_label.configure(image=self.green_light)
			self.light_label.image = self.green_light
			self.light_label.grid(row=0, column=0, sticky=tk.W)

	def track(self):
		def get_count(text):
			pattern = re.compile("\\d+")
			return int(pattern.findall(text)[0])

		self.status.set("Status: Program is launching.")
		self.start_button.config(state=tk.DISABLED)
		self.output.set("Logging in...")

		self.driver = webdriver.Chrome()
		self.driver.minimize_window()
		login(self.url, self.driver, self.username, self.password)
		self.output.set("Logged in.")
		self.status.set(f"Status: Logged into {self.name} account.")

		try:
			WebDriverWait(self.driver, 10).until(
				EC.presence_of_element_located((By.CLASS_NAME, "list-count"))
			)
		finally:
			list_count_el = self.driver.find_element(By.CLASS_NAME, 'list-count')
			initial_count = get_count(list_count_el.text)
		
		t1 = 0
		t2 = 0
		latency = 0
		latencies = []

		while True:
			try:
				WebDriverWait(self.driver, 10).until(
					EC.presence_of_element_located((By.CLASS_NAME, "list-count"))
					)
			finally:
				list_count_el = self.driver.find_element(By.CLASS_NAME, 'list-count')
				unclaimed_count = get_count(list_count_el.text)

				#get latest send list and keyword list
				self.update_to_send()
				self.update_kw_list()

				#check which ones are still open
				for cw in self.to_send:
					cw.update_status()

				ready = []
				if not self.to_send:
					msg = "No target window!"
				elif not any(cw.open for cw in self.to_send):
					msg = "No target window open!"
				else:
					for cw in self.to_send:
						if cw.open:
							ready.append(cw)

				if ready == self.to_send:
					self.change_light("green")
				else:
					self.change_light("red")

				output = ""
				if ready:
					output += f"Windows ready: {', '.join(cw.title for cw in ready)}"
				else:
					output += msg
				output += f"\nCurrent video count: {unclaimed_count}"
				output += f"\nCurrent refresh delay: {round(latency, 2)}s"

				if not latencies:
					avg_lat = 0
				else:
					avg_lat = sum(latencies)/len(latencies)

				output += f"\nAverage refresh delay: {round(avg_lat, 2)}s\n"
				if not self.keywords:
					output += "\nAuto-claim off."
				elif self.keywords == "all":
					output += "\nWill auto-claim all videos."
				else:
					kws = ", ".join(kw for kw in self.keywords)
					output += f"\nWill claim videos with keyword(s): {kws}"
				if self.keywords and self.negative_keywords:
					nkws = ", ".join(nkw for nkw in self.negative_keywords)
					output += f"\nWill not claim videos with keyword(s): {nkws}"
				self.output.set(output)
				self.pb.grid(row=3, column=0, columnspan=3, pady=10)
				self.pb.start()

				if unclaimed_count != initial_count:
					if unclaimed_count == 0:
						for cw in ready:
							cw.send('UNCLAIMED VIDEOS HAVE BEEN CLEARED TO 0. STANDBY FOR UPDATE.', 3)
					elif unclaimed_count > initial_count:
						recorder = start_record()
						t3 = datetime.datetime.now()
						self.driver.maximize_window()

						def get_to_click():
							to_click = []
							self.driver.switch_to.default_content()
							sections = self.driver.find_elements(By.CLASS_NAME, "title-name")
							for x in sections:
								if x.text == "待领取":
									main_box_el = x.find_element(By.XPATH, "..").find_element(By.XPATH, "..").find_element(By.XPATH, "..")
									found_elements = main_box_el.find_elements(By.CLASS_NAME, "card-name")
									total_indexes = len(found_elements)
							if self.keywords == "all":
								to_click = [e for e in found_elements if not any(nkw in e.text for nkw in self.negative_keywords)]
							else:
								indexes = []
								for e in found_elements:
									if any(kw in e.text for kw in self.keywords) and not any(nkw in e.text for nkw in self.negative_keywords):
										to_click.append(e)
										indx = found_elements.index(e)
										indexes.append(indx)
								in_first_half = sum(1 for i in indexes if i < total_indexes/2)
								in_second_half = sum(1 for i in indexes if i >= total_indexes/2)
								if in_second_half > in_first_half:
									to_click.reverse()
							return to_click

						#auto claim
						def add_comment():
							pyautogui.moveTo(self.comment_x_coord, self.comment_y_coord)
							pyautogui.click()
							pyautogui.press("1")
							pyautogui.press("enter")

						def close_comment():
							pyautogui.moveTo(self.close_x_coord, self.close_y_coord)
							pyautogui.click()

						#testing purposes
						# def add_movie(name):
						# 	try:
						# 		add_button = WebDriverWait(self.driver, 10).until(
						# 			EC.element_to_be_clickable((By.CLASS_NAME, "add-card-placeholder"))
						# 		)
						# 	finally:
						# 		add_button.click()
						# 	try:
						# 		comment_box = WebDriverWait(self.driver, 10).until(
						# 			EC.element_to_be_clickable((By.CLASS_NAME, "control-add-card"))
						# 		)
						# 	finally:
						# 		comment_box.click()			
						# 	pyperclip.copy(name)
						# 	pyautogui.hotkey("ctrl", "v")
						# 	pyautogui.press("enter")
						# 	click_image("cancel.png")

						timings = {}
						loop_times = 0

						if self.keywords:
							missed = []
							user_imgs = []
							claimed = []
							
							while True:
								to_click = get_to_click()
								if all(e.text in claimed+missed for e in to_click) and len(to_click) <= len(claimed)+len(missed):
									break
								elif claimed or missed:
									to_click = [e for e in to_click if (e.text not in claimed and e.text not in missed)]
									print(f"On loop {loop_times+1}, new videos: {', '.join(e.text for e in to_click)} were added.")

								loop_times += 1

								for e in to_click:
									e.click()
									try:
										WebDriverWait(self.driver, 10).until(
										EC.element_to_be_clickable((By.CLASS_NAME, "editor-area"))
										)
									finally:
										result = detect_image("files\\1.png")
										if result:
											missed.append(e.text)
											user_imgs.append(crop_full(result))
										else:
											add_comment()
											claimed.append(e.text)
										close_comment()
								
								timings[loop_times] = datetime.datetime.now()
								self.driver.refresh()

							t4 = timings[loop_times]
							print(f"Loops: {loop_times}")

						self.output.set("TAPD has been updated!")
						for cw in ready:
							cw.send('TAPD HAS BEEN UPDATED. https://www.tapd.cn/43882502', 1)

						output = ""
						if claimed:
							for cw in ready:
								cw.send(claimed, 1, to_img_list=True, img_title=f"Claimed {len(claimed)} video(s):")
							output = f"Detected update at {t3.strftime('%H:%M:%S')}hrs.\nClaimed {len(claimed)} video(s) in {round((t4-t3).total_seconds(), 2)}s.\n"
						if missed:
							for cw in ready:
								cw.send(missed, 1, to_img_list=True, img_title=f"Did not claim the following {len(missed)} video(s) because someone else commented:", user_imgs=user_imgs)
							output += f"Missed {len(missed)} video(s)."

						if output:
							self.output.set(output)

						self.pb.stop()
						self.status.set("Status: Program has finished.")

						gw.getWindowsWithTitle(self.driver.title)[0].maximize()
						recorder.stop()
						print("stopped")
						exit()
					else:
						initial_count = unclaimed_count

				self.driver.refresh()

				t2 = datetime.datetime.now()

				if t1 == 0:
					t1 = t2
				else:
					latency = (t2-t1).total_seconds()
					latencies.append(latency)
					if len(latencies) > 10:
						latencies = latencies[:-10]
					t1 = t2

class Database:
	"""
	Easily creates and manages save files.
	Will create file if it does not exist.
	Save file easily save() method.
	"""

	def __init__(self, save_file):
		self.path = f"files\\{save_file}"
		self.load()

	def load(self):
		try:
			with open(self.path, "r") as f:
				self.data = json.load(f)
		except FileNotFoundError:
			if "files" not in os.listdir():
				os.mkdir("files")
			with open(self.path, "w") as f:
				self.data = {}
				json.dump(self.data, f)

	def save(self):
		with open(self.path, "w") as f:
			json.dump(self.data, f, indent=4)

class LoginDetails:
	"""Stores login details for TAPD."""

	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
		self.load()
		self.setup_widgets()

	def load(self):
		self.preset_var = tk.StringVar(value="— Select a preset —")
		self.login_details = Database("login_details.json")
		if self.login_details.data:
			self.presets = self.login_details.data
			for p in self.login_details.data:
				if self.login_details.data[p]["selected"]:
					self.preset_var.set(p)
		else:
			self.presets = ["— Select a preset —"]

	def setup_widgets(self):
		l = ttk.Label(self.t, text="Login Details")
		preset_label = ttk.Label(self.t, text="Select Preset: ")
		option_menu = tk.OptionMenu(self.t, self.preset_var, *self.presets)
		add_button = ttk.Button(self.t, text="Add Preset", command=self.add_preset)
		save_button = ttk.Button(self.t, text="Save", command=self.save)

		l.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
		preset_label.grid(row=1, column=0, padx=10, pady=10)
		option_menu.grid(row=1, column=1, padx=10, pady=10)
		add_button.grid(row=2, column=0, padx=10, pady=10)
		save_button.grid(row=2, column=1, padx=10, pady=10)

	def add_preset(self):
		self.p = tk.Toplevel()
		self.p.resizable(False, False)

		l = ttk.Label(self.p, text="Add Preset")
		preset_label = ttk.Label(self.p, text="Preset Name: ")
		username_label = ttk.Label(self.p, text="Username: ")
		password_label = ttk.Label(self.p, text="Password: ")
		id_label = ttk.Label(self.p, text="TAPD Board ID: ")
		self.preset_entry = ttk.Entry(self.p, width=20)
		self.username_entry = ttk.Entry(self.p, width=20)
		self.password_entry = ttk.Entry(self.p, width=20, show="*")
		self.id_entry = ttk.Entry(self.p, width=20)
		save_button = ttk.Button(self.p, text="Save", command=self.save_preset)

		l.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
		preset_label.grid(row=1, column=0, padx=10, pady=10)
		self.preset_entry.grid(row=1, column=1, padx=10, pady=10)
		username_label.grid(row=2, column=0, padx=10, pady=10)
		self.username_entry.grid(row=2, column=1, padx=10, pady=10)		
		password_label.grid(row=3, column=0, padx=10, pady=10)
		self.password_entry.grid(row=3, column=1, padx=10, pady=10)
		id_label.grid(row=4, column=0, padx=10, pady=10)
		self.id_entry.grid(row=4, column=1, padx=10, pady=10)
		save_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

	def save_preset(self):
		preset_name = self.preset_entry.get()
		username = self.username_entry.get()
		password = self.password_entry.get()
		tapd_id = self.id_entry.get()

		if not (preset_name and username and password and tapd_id):
			popupMessage("Error", "Please input all fields.")
		else:
			self.login_details.data[preset_name] = {
			"username" : username,
			"password" : password,
			"tapd_id" : tapd_id,
			"selected" : False,
			}
			self.login_details.save()
			popupMessage("Successful", "Login details saved.", windowToClose=self.p)
			self.update_presets()

	def save(self):
		preset_name = self.preset_var.get()
		if preset_name == "— Select a preset —":
			popupMessage("Error", "Please select a preset.")
		else:
			self.login_details.data[preset_name]["selected"] = True
			for p in self.login_details.data:
				if p != preset_name:
					self.login_details.data[p]["selected"] = False
			self.login_details.save()
			popupMessage("Successful", "Login details saved.", windowToClose=self.t)

	def update_presets(self):
		self.t.destroy()
		self.t = tk.Toplevel()
		self.load()
		self.setup_widgets()

class ClickCoords:
	"""
	Stores coordinates for auto-claiming.
	It takes 2 coords: the coords of the comment box, and coords to close the popup window.
	"""

	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
		self.t.attributes("-topmost", True)
		self.setup_widgets()
		self.load()

	def load(self):
		self.click_coords = Database("click_coords.json")
		if self.click_coords.data:
			comment_x_coord = self.click_coords.data['comment_x_coord']
			comment_y_coord = self.click_coords.data['comment_y_coord']
			self.comment_x_entry.insert(0, comment_x_coord)
			self.comment_y_entry.insert(0, comment_y_coord)

			close_x_coord = self.click_coords.data['close_x_coord']
			close_y_coord = self.click_coords.data['close_y_coord']
			self.close_x_entry.insert(0, close_x_coord)
			self.close_y_entry.insert(0, close_y_coord)

	def setup_widgets(self):
		self.l1 = ttk.Label(self.t, text="Comment Box Coords")
		self.b1 = ttk.Button(self.t, text="Get Coords", command=self.get1)
		self.comment_x_label = ttk.Label(self.t, text="X Coord: ")
		self.comment_y_label = ttk.Label(self.t, text="Y Coord: ")
		self.comment_x_entry = ttk.Entry(self.t, width=20)
		self.comment_y_entry = ttk.Entry(self.t, width=20)
		self.save_button1 = ttk.Button(self.t, text="Save", command=self.save1)

		self.l1.grid(row=0, column=0, padx=10, pady=10)
		self.b1.grid(row=0, column=1, padx=10, pady=10)
		self.comment_x_label.grid(row=1, column=0, padx=10, pady=10)
		self.comment_x_entry.grid(row=1, column=1, padx=10, pady=10)
		self.comment_y_label.grid(row=2, column=0, padx=10, pady=10)
		self.comment_y_entry.grid(row=2, column=1, padx=10, pady=10)
		self.save_button1.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

		self.l2 = ttk.Label(self.t, text="Close Box Coords")
		self.b2 = ttk.Button(self.t, text="Get Coords", command=self.get2)
		self.close_x_label = ttk.Label(self.t, text="X Coord: ")
		self.close_y_label = ttk.Label(self.t, text="Y Coord: ")
		self.close_x_entry = ttk.Entry(self.t, width=20)
		self.close_y_entry = ttk.Entry(self.t, width=20)
		self.save_button2 = ttk.Button(self.t, text="Save", command=self.save2)

		self.l2.grid(row=4, column=0, padx=10, pady=10)
		self.b2.grid(row=4, column=1, padx=10, pady=10)
		self.close_x_label.grid(row=5, column=0, padx=10, pady=10)
		self.close_x_entry.grid(row=5, column=1, padx=10, pady=10)
		self.close_y_label.grid(row=6, column=0, padx=10, pady=10)
		self.close_y_entry.grid(row=6, column=1, padx=10, pady=10)
		self.save_button2.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

	def get_coords(self, x_entry, y_entry):
		def on_click(x, y, button, pressed):
			if button == mouse.Button.left:
				if x_entry.get():
					x_entry.delete(0, tk.END)
				if y_entry.get():
					y_entry.delete(0, tk.END)
				x_entry.insert(0, x)
				y_entry.insert(0, y)
				return False 

		listener = mouse.Listener(on_click=on_click)
		listener.start()
		listener.join()

	def get1(self):
		t = threading.Thread(target= lambda x_entry=self.comment_x_entry, y_entry=self.comment_y_entry: self.get_coords(x_entry, y_entry))
		t.start()

	def get2(self):
		t = threading.Thread(target= lambda x_entry=self.close_x_entry, y_entry=self.close_y_entry: self.get_coords(x_entry, y_entry))
		t.start()

	def save1(self):
		comment_x_coord = int(self.comment_x_entry.get())
		comment_y_coord = int(self.comment_y_entry.get())

		if not (comment_x_coord and comment_y_coord):
			popupMessage("Error", "Please input all fields.")
		else:
			self.click_coords.data["comment_x_coord"] = comment_x_coord
			self.click_coords.data["comment_y_coord"] = comment_y_coord
			self.click_coords.save()
			popupMessage("Successful", "Click box coords saved.")

	def save2(self):
		close_x_coord = int(self.close_x_entry.get())
		close_y_coord = int(self.close_y_entry.get())

		if not (close_x_coord and close_y_coord):
			popupMessage("Error", "Please input all fields.")
		else:
			self.click_coords.data["close_x_coord"] = close_x_coord
			self.click_coords.data["close_y_coord"] = close_y_coord
			self.click_coords.save()
			popupMessage("Successful", "Close box coords saved.")
			
class SendMessageLocations:
	"""Manages where update messages are sent."""

	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
		self.t.attributes("-topmost", True)
		self.setup_widgets()
		self.load()

	def setup_widgets(self):
		self.l = ttk.Label(self.t , text="Enter window name and coordinates for input box.")
		self.name_label = ttk.Label(self.t, text="Window Name: ")
		self.name_entry = ttk.Entry(self.t, width=20)
		self.x_label = ttk.Label(self.t, text="X: ")
		self.x_entry = ttk.Entry(self.t, width=5)
		self.y_label = ttk.Label(self.t, text="Y: ")
		self.y_entry = ttk.Entry(self.t, width=5)
		self.save_button = ttk.Button(self.t, text="Save", command=self.save)
		self.get_button = ttk.Button(self.t, text="Get Coords", command=self.get)

		self.l.grid(row=0, column=0, columnspan=4)
		self.name_label.grid(row=1, column=0, padx=10, pady=10)
		self.name_entry.grid(row=1, column=1, columnspan=3, padx=10, pady=10)
		self.x_label.grid(row=2, column=0, padx=10, pady=10)
		self.x_entry.grid(row=2, column=1, padx=10, pady=10)
		self.y_label.grid(row=2, column=2, padx=10, pady=10)
		self.y_entry.grid(row=2, column=3, padx=10, pady=10)
		self.save_button.grid(row=3, column=1, padx=10, pady=10)
		self.get_button.grid(row=3, column=3, padx=10, pady=10)

	def load(self):
		self.entries = {}
		self.r = 4

		self.windows_info = Database("windows_info.json")
		if self.windows_info.data:
			for name, attrs in self.windows_info.data.items():
				cb_var = tk.BooleanVar(value=False)
				cb = ttk.Checkbutton(self.t, text=name, variable=cb_var, style="Switch.TCheckbutton")
				cb.bind("<Button-1>", self.toggle)
				del_button = ttk.Button(self.t, text="Delete", command= lambda x=name: self.delete(x))

				#saving references to widgets
				self.entries[name] = {
				"cb" : cb,
				"cb_var" : cb_var,
				"del_button" : del_button,
				}

				cb.grid(row=self.r, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W)
				del_button.grid(row=self.r, column=3, padx=10, pady=10)

				#initial cb state
				activated = attrs['activated']
				if activated:
					cb_var.set(True)

				self.r += 1

	def get(self):
		def get_coords(x_entry, y_entry):
			def on_click(x, y, button, pressed):
				if button == mouse.Button.left:
					if x_entry.get():
						x_entry.delete(0, tk.END)
					if y_entry.get():
						y_entry.delete(0, tk.END)
					x_entry.insert(0, x)
					y_entry.insert(0, y)
					return False 

			listener = mouse.Listener(on_click=on_click)
			listener.start()
			listener.join()

		t = threading.Thread(target= lambda x_entry=self.x_entry, y_entry=self.y_entry: get_coords(x_entry, y_entry))
		t.start()

	def toggle(self, event):
		cb = event.widget
		name = cb.cget("text")
		activated = self.entries[name]['cb_var'].get()

		if not activated:
			self.windows_info.data[name]['activated'] = True
		else:
			self.windows_info.data[name]['activated'] = False
		self.windows_info.save()

	def delete(self, name):
		#destroy widgets
		self.entries[name]['cb'].destroy()
		self.entries[name]['del_button'].destroy()

		#update data
		del self.windows_info.data[name]
		self.windows_info.save()

	def save(self):
		name = self.name_entry.get()
		x_coord = self.x_entry.get()
		y_coord = self.y_entry.get()

		if not (name and x_coord and y_coord):
			popupMessage("Error", "Please input all fields.")

		elif not (x_coord.isdigit() and y_coord.isdigit()):
			popupMessage("Error", "Please only enter numbers for coords fields.")

		else:
			#save data
			coords = (int(x_coord), int(y_coord))
			attrs = {
			"coords": coords,
			"activated": False,
			}
			self.windows_info.data[name] = attrs
			self.windows_info.save()

			#add widgets
			cb_var = tk.BooleanVar(value=False)
			cb = ttk.Checkbutton(self.t, text=name, variable=cb_var, style="Switch.TCheckbutton")
			cb.bind("<Button-1>", self.toggle)
			del_button = ttk.Button(self.t, text="Delete", command= lambda x=name: self.delete(x))

			#saving references to widgets
			self.entries[name] = {
			"cb" : cb,
			"cb_var" : cb_var,
			"del_button" : del_button,
			}

			cb.grid(row=self.r, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W)
			del_button.grid(row=self.r, column=3, padx=10, pady=10)
			self.r += 1

			#clear input boxes
			self.name_entry.delete(0, 'end')
			self.x_entry.delete(0, 'end')
			self.y_entry.delete(0, 'end')

class ManualSend:
	"""
	Manually sends a given message to activated windows for a certain number of times.
	Mainly for testing purposes.
	"""

	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
		self.setup_widgets()

	def setup_widgets(self):
		self.l1 = ttk.Label(self.t, text="Text: ")
		self.tb = tk.Text(self.t, width=30, height=5)
		self.l2 = ttk.Label(self.t, text="Times to send: ")
		self.e = ttk.Entry(self.t, width=10)
		b = ttk.Button(self.t, text="Send", command=self.send)

		self.l1.grid(row=0, column=0, padx=10, pady=10)
		self.tb.grid(row=0, column=1, padx=10, pady=10)
		self.l2.grid(row=1, column=0, padx=10, pady=10)
		self.e.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
		b.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

	def load(self):
		self.ready = []
		windows_info = Database("windows_info.json")
		for name, attrs in windows_info.data.items():
			activated = attrs['activated']
			if activated:
				coords = attrs['coords']
				cw = ChatWindow(name, coords)
				cw.update_status()
				if cw.open:
					self.ready.append(cw)

	def send(self):
		if not (self.tb.get("1.0", "end") and self.e.get()):
			popupMessage("Error", "Please input all fields.")
			return

		def cfm_send():
			text = self.tb.get("1.0", "end")
			times = int(self.e.get())
			for cw in self.ready:
				cw.send(text, times)
			self.tb.delete("1.0", "end")
			self.e.delete(0, "end")

		self.load()
		names = '\n'.join(wn.title for wn in self.ready)
		if names:
			cfm = tk.Toplevel()
			cfm.resizable(False, False)
			cfm.title("Confirmation")
			l = ttk.Label(cfm, text=f"Text will be sent to the following windows:\n{names}")
			y = ttk.Button(cfm, text="Yes", command=cfm_send)
			n = ttk.Button(cfm, text="No", command=cfm.destroy)

			l.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
			y.grid(row=1, column=0, padx=10, pady=10)
			n.grid(row=1, column=1, padx=10, pady=10)
		else:
			popupMessage("Error", "No target window found. Activate at least one window.")

class AutoClaim:
	"""Sets keywords for videos to automatically claim/not to claim."""

	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
		self.r1 = 4
		self.r2 = 4
		self.refs = {}
		self.load()
		self.setup_widgets()

	def load(self):
		self.auto_claim_info = Database("auto_claim_info.json")

		#initialize auto claim data if empty
		if not self.auto_claim_info.data:
			self.auto_claim_info.data = {
			"all_state" : False,
			"keywords" : [],
			"negative_keywords" : [],
			}
			self.auto_claim_info.save()

		self.all_state = self.auto_claim_info.data["all_state"]
		self.keywords = self.auto_claim_info.data["keywords"]
		self.negative_keywords = self.auto_claim_info.data["negative_keywords"]

	def setup_widgets(self):
		self.pin_var = tk.BooleanVar(value=False)

		self.pin_button = ttk.Checkbutton(self.t, text="Claim All", variable=self.pin_var, style="Switch.TCheckbutton")
		self.l1 = ttk.Label(self.t, text="Claim movies with keyword:")
		self.e1 = ttk.Entry(self.t, width=20)
		self.b1 = ttk.Button(self.t, text="Add", command=self.add_kw)

		self.pin_button.bind("<Button-1>", self.toggle)

		self.pin_button.grid(row=0, column=0, sticky=tk.E)
		self.l1.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
		self.e1.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
		self.b1.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

		if self.keywords:
			for kw in self.keywords:
				kw_label = ttk.Label(self.t, text=kw)
				del_button = ttk.Button(self.t, text="Delete", command= lambda x=kw: self.delete(x))

				#saving references to widgets
				self.refs[kw] = {
				"kw_label" : kw_label,
				"del_button" : del_button,
				}

				kw_label.grid(row=self.r1, column=0, padx=10, pady=10, sticky=tk.W)
				del_button.grid(row=self.r1, column=1, padx=10, pady=10)

				self.r1 += 1

		self.l2 = ttk.Label(self.t, text="Don't claim movies with keyword:")
		self.e2 = ttk.Entry(self.t, width=20)
		self.b2 = ttk.Button(self.t, text="Add", command=self.add_nkw)

		self.l2.grid(row=1, column=2, columnspan=2, padx=10, pady=10)
		self.e2.grid(row=2, column=2, columnspan=2, padx=10, pady=10)
		self.b2.grid(row=3, column=2, columnspan=2, padx=10, pady=10)

		if self.negative_keywords:
			for kw in self.negative_keywords:
				kw_label = ttk.Label(self.t, text=kw)
				del_button = ttk.Button(self.t, text="Delete", command= lambda x=kw: self.delete(x))

				#saving references to widgets
				self.refs[kw] = {
				"kw_label" : kw_label,
				"del_button" : del_button,
				}

				kw_label.grid(row=self.r2, column=2,padx=10, pady=10, sticky=tk.W)
				del_button.grid(row=self.r2, column=3, padx=10, pady=10)

				self.r2 += 1

		if self.all_state:
			self.pin_var.set(True)
			
			self.e.config(state=tk.DISABLED)
			self.b.config(state=tk.DISABLED)
			for kw in self.keywords:
				self.refs[kw]["del_button"].config(state=tk.DISABLED)
			self.all_state = True
			self.auto_claim_info.data["all_state"] = True
			self.auto_claim_info.save()

	def toggle(self, event):
		if not self.pin_var.get(): #state before press
			self.e1.config(state=tk.DISABLED)
			self.b1.config(state=tk.DISABLED)
			for kw in self.keywords:
				self.refs[kw]["del_button"].config(state=tk.DISABLED)
			self.all_state = True
			self.auto_claim_info.data["all_state"] = True
			self.auto_claim_info.save()
		else:
			self.e1.config(state=tk.NORMAL)
			self.b1.config(state=tk.NORMAL)
			for kw in self.keywords:
				self.refs[kw]["del_button"].config(state=tk.NORMAL)
			self.all_state = False
			self.auto_claim_info.data["all_state"] = False
			self.auto_claim_info.save()

	def delete(self, kw):
		self.refs[kw]["kw_label"].destroy()
		self.refs[kw]["del_button"].destroy()
		if kw in self.keywords:
			self.keywords.remove(kw)
			self.auto_claim_info.data["keywords"] = self.keywords
		elif kw in self.negative_keywords:
			self.negative_keywords.remove(kw)
			self.auto_claim_info.data["negative_keywords"] = self.negative_keywords
		self.auto_claim_info.save()

	def add_kw(self):
		kw = self.e1.get()
		if not kw:
			popupMessage("Error", "Please input keyword.")
			return
		elif kw in self.keywords:
			popupMessage("Error", "Keyword already exists.")
			return
		elif kw in self.negative_keywords:
			popupMessage("Error", "Can't contradict keywords not to claim.")
			return

		kw_label = ttk.Label(self.t, text=kw)
		del_button = ttk.Button(self.t, text="Delete", command= lambda x=kw: self.delete(x))

		#save references
		self.refs[kw] = {
		"kw_label" : kw_label,
		"del_button" : del_button,
		}
		
		kw_label.grid(row=self.r1, column=0, padx=10, pady=10, stick=tk.W)
		del_button.grid(row=self.r1, column=1, padx=10, pady=10, stick=tk.E)
		self.r1 += 1
		self.keywords.append(kw)
		self.e1.delete(0, 'end')
		self.auto_claim_info.data["keywords"] = self.keywords
		self.auto_claim_info.save()

	def add_nkw(self):
		kw = self.e2.get()
		if not kw:
			popupMessage("Error", "Please input keyword.")
			return
		elif kw in self.negative_keywords:
			popupMessage("Error", "Keyword already exists.")
			return
		elif kw in self.keywords:
			popupMessage("Error", "Can't contradict keywords to claim.")
			return

		kw_label = ttk.Label(self.t, text=kw)
		del_button = ttk.Button(self.t, text="Delete", command= lambda x=kw: self.delete(x))

		#save references
		self.refs[kw] = {
		"kw_label" : kw_label,
		"del_button" : del_button,
		}
		
		kw_label.grid(row=self.r2, column=2, padx=10, pady=10, stick=tk.W)
		del_button.grid(row=self.r2, column=3, padx=10, pady=10, stick=tk.E)
		self.r2 += 1
		self.negative_keywords.append(kw)
		self.e2.delete(0, 'end')
		self.auto_claim_info.data["negative_keywords"] = self.negative_keywords
		self.auto_claim_info.save()

class About:
	"""Gives link to GitHub Page."""

	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
		self.setup_widgets()

	def setup_widgets(self):
		l = ttk.Label(self.t, text="For more information, visit the program's GitHub page.")
		b = ttk.Button(self.t, text="Click to Visit", command=self.visit)

		l.grid(row=0, column=0, padx=20, pady=10)
		b.grid(row=1, column=0, padx=20, pady=10)

	def visit(self):
		webbrowser.open_new_tab("https://github.com/csjaugustus/tapdtracker")

class TestRun:
	"""Automatically does a test run on Test Run preset."""
	
	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
		self.setup_widgets()

	def setup_widgets(self):
		l = ttk.Label(self.t, text="Click below to launch a test run.\nMake sure you are logged into the Test Run account, and wait for program to run first.")
		b = ttk.Button(self.t, text="Go", command=self.test_run)

		l.grid(row=0, column=0, padx=50, pady=10)
		b.grid(row=1, column=0, padx=50, pady=10)

	def initial_check(self):
		login_details = Database("login_details.json")
		try:
			login_details.data["Test Run"]
		except KeyError:
			popupMessage("Error", "Test Run preset not created.", windowToClose=self.t)
			return False
		if not login_details.data or not login_details.data["Test Run"]["selected"]:
			popupMessage("Error", "Test Run preset not created or not selected.", windowToClose=self.t)
			return False
		return True

	def test_run(self):
		def run():
			driver = webdriver.Chrome()
			login("https://www.tapd.cn/64747886", driver, "15578073443", "antifuckingh4ck!")
			driver.maximize_window()
			try:
				add_button = WebDriverWait(driver, 10).until(
					EC.element_to_be_clickable((By.CLASS_NAME, "add-card-placeholder"))
				)
			finally:
				add_button.click()
			try:
				comment_box = WebDriverWait(driver, 10).until(
					EC.element_to_be_clickable((By.CLASS_NAME, "control-add-card"))
				)
			finally:
				comment_box.click()			
			pyautogui.write("Test Movie Name")
			pyautogui.press("enter")

		if self.initial_check():
			t = threading.Thread(target=run)
			t.start()
			self.t.destroy()

def main():
	root = tk.Tk()

	root.title("TAPD Tracker")
	root.resizable(False, False)
	icon = tk.PhotoImage(file = "files\\tapdicon.png")
	root.iconphoto(True, icon)
	root.tk.call("source", "sun-valley.tcl")
	root.tk.call("set_theme", "light")
	app = App(root)
	app.pack(fill="both", expand=True)

	main_menu = tk.Menu(root)
	root.config(menu=main_menu)
	settings_menu = tk.Menu(main_menu)
	main_menu.add_cascade(label="Settings", menu=settings_menu)
	settings_menu.add_command(label="Change Login Details", command=LoginDetails)
	settings_menu.add_command(label="Manage Send Message Locations", command=SendMessageLocations)
	settings_menu.add_command(label="Manual Send", command=ManualSend)
	settings_menu.add_command(label="Auto Claim", command=AutoClaim)
	settings_menu.add_command(label="Click Coords", command=ClickCoords)
	settings_menu.add_command(label="Test Run", command=TestRun)
	settings_menu.add_command(label="About", command=About)

	root.update()
	root.minsize(root.winfo_width(), root.winfo_height())
	x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
	y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
	root.geometry("+{}+{}".format(x_cordinate, y_cordinate - 20))

	root.mainloop()

if __name__ == "__main__":
	main()
