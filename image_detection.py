import cv2
import numpy as np
import pyautogui
from random import choice
from win32gui import GetForegroundWindow, GetWindowRect
import time

def detect_image(template_file_name, threshold = 0.9):
	ss = pyautogui.screenshot()
	img_rgb = cv2.cvtColor(np.array(ss), cv2.COLOR_RGB2BGR)
	img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
	template = cv2.imread(template_file_name, 0)

	# Store width and height of template in w and h
	w, h = template.shape[::-1]
	res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
	loc = np.where( res >= threshold )
	if len(loc[0]) > 0:
		ranges = [] # (x_min, x_max, y_min, y_max)
		for pt in zip(*loc[::-1]):
			ranges.append((pt[0], pt[0] + w, pt[1], pt[1]+h))
		current_x = list(pyautogui.position())[0]
		current_y = list(pyautogui.position())[1]
		return sorted(ranges, key = lambda i: min(abs(i[0]-current_x),abs(i[2]-current_y)))[0] #return the closest detection

	else:
		return False

def crop_full(detected):
	x_min, x_max, y_min, y_max = detected
	ss = pyautogui.screenshot()
	cropped = ss.crop((x_min-80, y_min-50, x_max+100, y_max+15))
	return cropped

def click_image(template_file_name, delay=None):
	result = detect_image(template_file_name)
	if not result:
		if delay:
			time.sleep(delay)
			result = detect_image(template_file_name)
			if not result:
				print("No image detected.")
				return
		else:
			print("No image detected.")
			return
	x1, x2, y1, y2 = result
	center_x = (x1 + x2)/2
	center_y = (y1 + y2)/2
	pyautogui.moveTo(center_x, center_y)
	pyautogui.click()

def main():
	result = click_image("files\\1.png", delay=5)
	# # crop_full(result).save("cropped.png")

if __name__ == "__main__":
	main()