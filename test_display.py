import time
import board
import busio
from PIL import Image, ImageDraw
import adafruit_ssd1306

# initialize I2C (SCL, SDA on Pi)
i2c = busio.I2C(board.SCL, board.SDA)

# 128x64 OLED on I2C 0x3C
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

disp.fill(0)
disp.show()

width  = disp.width
height = disp.height
image  = Image.new("1", (width, height))
draw   = ImageDraw.Draw(image)

cx, cy = width//2, height//2
r      = min(cx, cy) - 2

# face outline
draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=255)
# eyes
er = r//5
edx, edy = r//2, r//3
for ex in (-edx, +edx):
    draw.ellipse((cx+ex-er, cy-edy-er, cx+ex+er, cy-edy+er), fill=255)
# smile
mw, mh = r, r//2
draw.arc((cx-mw//2, cy-mh//2 + r//4, cx+mw//2, cy+mh//2 + r//4), 0, 180, fill=255)

disp.image(image)
disp.show()

time.sleep(10)
