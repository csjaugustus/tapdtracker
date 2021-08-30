import pyautogui

print("Move mouse to desired location.")
while True:
	user_input = input("Press any key to get coords. 'q' to quit.")
	if user_input == 'q':
		break
	else:
		print(pyautogui.position())