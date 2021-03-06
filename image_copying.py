from io import BytesIO
import win32clipboard
from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype('files\\SourceHanSans-Normal.otf', 38)

def list_to_image(lst, title=None, user_imgs=[]):
	"""
	Takes a list, prints each element onto a canvas, and copies end image to clipboard.
	Optionally takes a title.
	"""
	def send_to_clipboard(clip_type, data):
		win32clipboard.OpenClipboard()
		win32clipboard.EmptyClipboard()
		win32clipboard.SetClipboardData(clip_type, data)
		win32clipboard.CloseClipboard()

	converted_list = []

	if title:
		converted_list.append(title)

	for e in lst:
		converted_list.append(e)

	margin = 20
	space = 10

	temp_canvas = Image.new('RGB', (0, 0))
	temp_draw = ImageDraw.Draw(temp_canvas)

	titles = []
	widths = []
	heights = []

	for title in converted_list:
		w, h = temp_draw.textsize(title, font=font)
		titles.append((title, h))
		widths.append(w)
		heights.append(h)

	if user_imgs:
		if max(widths[1:]) + 96 < widths[0]:
			canvas_w = max(widths) + 2 * margin
		else:
			canvas_w = max(widths[1:]) + 96 + 2 * margin
		canvas_h = heights[0] + (len(titles)-1) * (96 + space) + 2 * margin

	else:
		canvas_w = max(widths) + 2 * margin
		canvas_h = sum(heights) + 2 * margin + (len(titles) - 1) * space

	canvas = Image.new('RGB', (canvas_w, canvas_h), color="#FFFFFF")
	draw = ImageDraw.Draw(canvas)

	x_coord = margin
	y_coord = margin

	if user_imgs:
		for i, pair in enumerate(titles):
			title = pair[0]
			draw.text((x_coord, y_coord), title, font=font, fill="#000000")
			if i == 0:
				y_coord += h
				y_coord += space
			else:
				canvas.paste(user_imgs[i-1], (x_coord + max(widths[1:]), y_coord))
				y_coord += 96
				y_coord += space
	else:
		for title, h in titles:
			draw.text((x_coord, y_coord), title, font=font, fill="#000000")
			y_coord += h
			y_coord += space

	output = BytesIO()
	canvas.convert("RGB").save(output, "BMP")
	data = output.getvalue()[14:]
	output.close()

	send_to_clipboard(win32clipboard.CF_DIB, data)

def main():
	lst = [
	"【2】如果可以回到过去【6】自带轴 1080",
	"【2】男人的争斗【7】英文内嵌 非英文部分不翻1080",
	"【2】暗夜守护者 【6】自带轴 俄罗斯奇幻片1080",
	"【2】鳄口逃生【6】自带轴 惊悚1080",
	"【2】15年【7】英文内嵌 LGBT以色列同性片 1080",
	"【1.5】无辜【7】英文内嵌 戛纳电影节 爱情1080",
	"【2】圣乔治【7】英文内嵌1080",
	"【1】地下室【6】英文内嵌 1080",
	"【2】赛车狂人【7】英文内嵌 挪威赛车喜剧1080",
	"【1.5】守夜【8】法国悬疑 英文内嵌1080",
	"【1.5】花【6】英文内嵌 电影节 西班牙剧情1080",
	"【2】马里尤斯【8】法国爱情两部曲 英文内嵌1080",
	"【2】下众之爱【8】东京电影节 英文内嵌1080",
	"【2】无底袋【6】英文内嵌 轴少 俄罗斯黑白剧情 720",
	"【2.5】石头不会忘记【7】英文内嵌 历史 1080",
	"【2】超越无限两分钟【8】英内嵌 日本喜剧1080",
	"【1.5】请不要救我【8】英内嵌 韩国720",
	"【1.5】波登湖【6】英内嵌 轴少 芬兰悬疑 1080"]

	list_to_image(lst)

if __name__ == "__main__":
	main()