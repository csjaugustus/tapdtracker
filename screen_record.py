import cv2
import numpy as np
import pyautogui
import threading
import tkinter as tk

class MyThread(threading.Thread):
	"""Thread class with a stop() method. The thread itself has to check
	regularly for the stopped() condition."""

	def __init__(self, *args, **kwargs):
		super(MyThread, self).__init__(*args, **kwargs)
		self._stop = threading.Event()
 
	# function using _stop function
	def stop(self):
		self._stop.set()
 
	def stopped(self):
		return self._stop.isSet()
 
	def run(self):
		SCREEN_SIZE = tuple(pyautogui.size())
		fourcc = cv2.VideoWriter_fourcc(*"XVID")
		fps = 12.0
		out = cv2.VideoWriter("output.avi", fourcc, fps, (SCREEN_SIZE))

		while True:
			if self.stopped():
				return
			img = pyautogui.screenshot()
			frame = np.array(img)
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			out.write(frame)

			# cv2.imshow("screenshot", frame)			

def start_record():
	t = MyThread()
	t.start()
	return t

def stop_record(t):
	t.stop()

def main():
	t = start_record()

	root = tk.Tk()

	b = tk.Button(root, text="STOP", command=lambda x=t: stop_record(x))
	b.pack()

	root.mainloop()

if __name__ == "__main__":
	main()