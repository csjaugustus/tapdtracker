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

def popupMessage(title, message, windowToClose=None):
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
	def __init__(self, window_title, coords):
		self.title = window_title
		self.x = coords[0]
		self.y = coords[1]

	def update_status(self):
		if gw.getWindowsWithTitle(self.title):
			self.open = True
		else:
			self.open = False

	def send(self, msg, times):
		window = gw.getWindowsWithTitle(self.title)[0]
		all_windows = gw.getAllWindows()

		for w in all_windows:
			w.minimize()
		window.maximize()
		pyautogui.moveTo(self.x, self.y)
		pyautogui.click()
		for i in range(times):
			pyautogui.write(msg)
			pyautogui.press('enter')
		window.minimize()


class App(ttk.Frame):
	def __init__(self, parent):
		ttk.Frame.__init__(self)
		self.t = threading.Thread(target=self.track)

		#variables
		self.pin = tk.BooleanVar(value=False)
		self.status = tk.StringVar(value="Status: Program not running.")
		self.output = tk.StringVar(value="No output.")

		#setup widgets
		self.setup_widgets()

	def initial_check(self):
		login_details = Database("login_details.json")
		windows_info = Database("windows_info.json")
		auto_claim_info = Database("auto_claim_info.json")

		#initialize auto claim data if empty
		if not auto_claim_info.data:
			auto_claim_info.data = {
			"all_state" : False,
			"keywords" : [],
			}
		auto_claim_info.save()

		errors = []
		if not login_details.data:
			errors.append("Please input login details.")
		if not any(windows_info.data[name]['activated'] for name in windows_info.data):
			errors.append("Please have at least one activated window to send messages to.")

		if errors:
			popupMessage("Error(s)", "\n\n".join(e for e in errors))
			return False

		self.to_send = []
		for name, attrs in windows_info.data.items():
			activated = attrs['activated']
			if activated:
				coords = attrs['coords']
				cw = ChatWindow(name, coords)
				self.to_send.append(cw)
		self.username = login_details.data['username']
		self.password = login_details.data['password']
		return True

	def start(self):
		if self.initial_check():
			self.t.start()

	def setup_widgets(self):
		self.light_label = tk.Label(self, image=red_light)
		self.pin_button = ttk.Checkbutton(self, text="Pin", variable=self.pin, style="Switch.TCheckbutton")
		self.status_label = ttk.Label(self,textvariable=self.status)
		self.output_label = ttk.Label(self, textvariable=self.output, borderwidth=1, relief="groove")
		self.start_button = ttk.Button(self, text="Start", command=self.start)
		self.pb = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=300, mode="indeterminate")

		self.pin_button.bind("<Button-1>", self.pin_window)

		self.light_label.grid(row=0, column=0, sticky=tk.W)
		self.pin_button.grid(row=0, column=2, sticky=tk.E)
		self.status_label.grid(row=1, column=0, columnspan=3, padx=20,pady=10)
		self.output_label.grid(row=2, column=0, columnspan=3, padx=20, pady=10)
		self.start_button.grid(row=4, column=0, columnspan=3, pady=10)

	def update_to_send(self):
		#updates send list during runtime
		self.to_send = []

		windows_info = Database("windows_info.json")
		for name, attrs in windows_info.data.items():
			activated = attrs['activated']
			if activated:
				coords = attrs['coords']
				cw = ChatWindow(name, coords)
				self.to_send.append(cw)

	def update_kw_list(self):
		#updates keyword list during runtime
		self.auto_claim_info = Database("auto_claim_info.json")
		self.all_state = self.auto_claim_info.data["all_state"]
		if self.all_state:
			self.keywords = "all"
		else:
			self.keywords = self.auto_claim_info.data["keywords"]
		self.negative_keywords = self.auto_claim_info.data["negative_keywords"]


	def pin_window(self, event):
		if not self.pin.get():
			root.attributes("-topmost", True)
		else:
			root.attributes("-topmost", False)

	def change_light(self, colour):
		if colour == "red":
			self.light_label.configure(image=red_light)
			self.light_label.image = red_light
			self.light_label.grid(row=0, column=0, sticky=tk.W)
		elif colour == "green":
			self.light_label.configure(image=green_light)
			self.light_label.image = green_light
			self.light_label.grid(row=0, column=0, sticky=tk.W)

	def track(self):
		self.initial_check()

		def get_count(text):
			pattern = re.compile("\\d+")
			return pattern.findall(text)[0]

		self.status.set("Status: Program is running.")
		self.start_button.config(state=tk.DISABLED)

		self.driver = webdriver.Chrome()
		self.driver.get("https://www.tapd.cn/43882502")
		self.driver.minimize_window()
		
		self.output.set("Logging in...")

		try:
			WebDriverWait(self.driver, 10).until(
				EC.presence_of_element_located((By.ID, "username"))
			)
		finally:
			username_box = self.driver.find_element_by_id("username")
			password_box = self.driver.find_element_by_id("password_input")
			username_box.send_keys(self.username)
			password_box.send_keys(self.password)
			login_button = self.driver.find_element_by_id("tcloud_login_button")
			login_button.click()
			self.output.set("Logged in.")

		try:
			WebDriverWait(self.driver, 10).until(
				EC.presence_of_element_located((By.CLASS_NAME, "list-count"))
			)
		finally:
			list_count_el = self.driver.find_element_by_class_name('list-count')
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
				list_count_el = self.driver.find_element_by_class_name('list-count')
				unclaimed_count = get_count(list_count_el.text)

				#get latest send list
				self.update_to_send()
				#get latest keyword list
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
					ready = []
					for cw in self.to_send:
						if cw.open:
							ready.append(cw)

				#change light
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
				output += f"\nCurrent refresh delay: {round(latency, 2)}s."

				if not latencies:
					avg_lat = 0
				else:
					avg_lat = sum(latencies)/len(latencies)

				output += f"\nAverage refresh delay: {round(avg_lat, 2)}s.\n"
				if not self.keywords:
					output += "\nAuto-claim off."
				elif self.keywords == "all":
					output += "\nWill auto-claim all videos."
				else:
					kws = ", ".join(kw for kw in self.keywords)
					output += f"\nWill claim videos with keyword(s): {kws}."
					nkws = ", ".join(nkw for nkw in self.negative_keywords)
					output += f"\nWill not claim videos with keyword(s): {nkws}."
				self.output.set(output)
				self.pb.grid(row=3, column=0, columnspan=3, pady=10)
				self.pb.start()

				if unclaimed_count != initial_count:
					if unclaimed_count == "0":
						for cw in ready:
							cw.send('UNCLAIMED VIDEOS HAVE BEEN CLEARED TO 0. STANDBY FOR UPDATE.', 3)
					elif unclaimed_count > initial_count: #do stuff
						self.output.set("TAPD has been updated!")
						for cw in ready:
							cw.send('TAPD HAS BEEN UPDATED. https://www.tapd.cn/43882502', 3)
						self.driver.maximize_window()

						#auto claim
						def add_comment():
							pyautogui.moveTo(708, 1143)
							pyautogui.click()
							pyautogui.press("1")
							pyautogui.press("enter")

						def close_comment():
							pyautogui.moveTo(979, 1280)
							pyautogui.click()						

						if self.keywords:
							to_click = []
							self.driver.switch_to.default_content()
							sections = self.driver.find_elements_by_class_name("title-name")
							for x in sections:
								if x.text == "待领取":
									main_box_el = x.find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..")
									found_elements = main_box_el.find_elements_by_class_name("card-name")
								if self.keywords == "all":
									to_click = [e for e in found_elements if not any(nkw in e.text for nkw in self.negative_keywords)]
								else:
									for e in found_elements:
										if any(kw in e.text for kw in self.keywords) and not any(nkw in e.text for nkw in self.negative_keywords):
											to_click.append(e)
							try:
								clicked = []
								for e in to_click:
									e.click()
									time.sleep(0.25)
									add_comment()
									close_comment()
									clicked.append(e)

							#in case clicking errors
							except:
								for e in to_click:
									if e not in clicked:
										e.click()
										time.sleep(0.5)
										add_comment()
										close_comment()

							claimed_titles = "\n".join(e.text for e in to_click)
							for cw in ready:
								cw.send(f"Claimed videos:\n{claimed_titles}", 1)
							self.output.set(f"Claimed videos: \n{claimed_titles}")
							self.driver.maximize_window()

						self.pb.stop()
						self.status.set("Status: Program has finished.")
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
					t1 = t2



class Database:
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
	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
		self.setup_widgets()
		self.load()

	def load(self):
		self.login_details = Database("login_details.json")
		if self.login_details.data:
			username = self.login_details.data['username']
			password = self.login_details.data['password']
			self.username_entry.insert(0, username)
			self.password_entry.insert(0, password)

	def setup_widgets(self):
		self.l = ttk.Label(self.t, text="Login Details")
		self.username_label = ttk.Label(self.t, text="Username: ")
		self.password_label = ttk.Label(self.t, text="Password: ")
		self.username_entry = ttk.Entry(self.t, width=20)
		self.password_entry = ttk.Entry(self.t, width=20, show="*")
		self.save_button = ttk.Button(self.t, text="Save", command=self.save)

		self.l.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
		self.username_label.grid(row=1, column=0, padx=10, pady=10)
		self.username_entry.grid(row=1, column=1, padx=10, pady=10)
		self.password_label.grid(row=2, column=0, padx=10, pady=10)
		self.password_entry.grid(row=2, column=1, padx=10, pady=10)
		self.save_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

	def save(self):
		username = self.username_entry.get()
		password = self.password_entry.get()

		if not (username and password):
			popupMessage("Error", "Please input all fields.")
		else:
			self.login_details.data["username"] = username
			self.login_details.data["password"] = password
			self.login_details.save()
			popupMessage("Successful", "Login details saved.")
			self.t.destroy()

class SendMessageLocations:
	def __init__(self):
		self.t = tk.Toplevel()
		self.t.resizable(False, False)
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

		self.l.grid(row=0, column=0, columnspan=4)
		self.name_label.grid(row=1, column=0, padx=10, pady=10)
		self.name_entry.grid(row=1, column=1, columnspan=3, padx=10, pady=10)
		self.x_label.grid(row=2, column=0, padx=10, pady=10)
		self.x_entry.grid(row=2, column=1, padx=10, pady=10)
		self.y_label.grid(row=2, column=2, padx=10, pady=10)
		self.y_entry.grid(row=2, column=3, padx=10, pady=10)
		self.save_button.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

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
		#error checking
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
				kw_label = ttk.Button(self.t, text=kw)
				del_button = ttk.Button(self.t, text="Delete", command= lambda x=kw: self.delete(x))

				#saving references to widgets
				self.refs[kw] = {
				"kw_label" : kw_label,
				"del_button" : del_button,
				}

				kw_label.grid(row=self.r1, column=0, sticky=tk.W)
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
				kw_label = ttk.Button(self.t, text=kw)
				del_button = ttk.Button(self.t, text="Delete", command= lambda x=kw: self.delete(x))

				#saving references to widgets
				self.refs[kw] = {
				"kw_label" : kw_label,
				"del_button" : del_button,
				}

				kw_label.grid(row=self.r2, column=2, sticky=tk.W)
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


root = tk.Tk()

#load r&g lights
red_light = Image.open("files\\redlight.png")
red_light = red_light.resize((20, 20))
red_light = ImageTk.PhotoImage(red_light)
green_light = Image.open("files\\greenlight.png")
green_light = green_light.resize((20, 20))
green_light = ImageTk.PhotoImage(green_light)

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
settings_menu.add_command(label="Change Login Details", command=lambda: LoginDetails())
settings_menu.add_command(label="Manage Send Message Locations", command= lambda: SendMessageLocations())
settings_menu.add_command(label="Manual Send", command=lambda: ManualSend())
settings_menu.add_command(label="Auto Claim", command=lambda: AutoClaim())

root.update()
root.minsize(root.winfo_width(), root.winfo_height())
x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
root.geometry("+{}+{}".format(x_cordinate, y_cordinate - 20))

root.mainloop()

