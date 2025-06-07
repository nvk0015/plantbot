#!/usr/bin/env python3
import os
import socket
import webbrowser
import logging
from flask import Flask, render_template, request, jsonify

import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

from STT.whisper_test import record_and_transcribe
import backend
import utils

logging.basicConfig(
    filename="plant_interface.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app = Flask(__name__)

# STT defaults
STT_DEVICE   = int(os.getenv("STT_DEVICE", 1))
STT_DURATION = float(os.getenv("STT_DURATION", 10.0))
STT_MODEL    = os.getenv("STT_MODEL", "tiny")
STT_LANG     = os.getenv("STT_LANG", "en")

# OLED setup
i2c = busio.I2C(board.SCL, board.SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
disp.fill(0)
disp.show()

# font setup – put your actual Symbola.ttf path here
FONT_PATH = "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf"
if not os.path.exists(FONT_PATH):
    raise RuntimeError(f"Font not found at {FONT_PATH}")
font = ImageFont.truetype(FONT_PATH, 48)

def show_emoji(emoji_char: str):
    disp.fill(0)
    img = Image.new("1", (disp.width, disp.height))
    draw = ImageDraw.Draw(img)
    # measure text
    bbox = draw.textbbox((0, 0), emoji_char, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (disp.width - w) // 2
    y = (disp.height - h) // 2
    draw.text((x, y), emoji_char, font=font, fill=255)
    disp.image(img)
    disp.show()

def process_user_input(user_text: str, mode: str, lang: str) -> dict:
    logging.info("User input: %r", user_text)
    msg = backend.generate_message(user_prompt=user_text)
    response, emoji = msg["response"], msg["emoji"]

    show_emoji(emoji)

    if mode == "speak":
        utils.speak_text(response, lang)

    return {"user_text": user_text, "response": response, "emoji": emoji}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    mode = data.get("mode", "text")
    lang = data.get("lang", "en")
    user = (data.get("user_input") or "").strip()
    if not user:
        return jsonify({"error": "No input provided."}), 400
    if len(user.split(". ")) > 2:
        return jsonify({"error": "Max two sentences."}), 400
    return jsonify(process_user_input(user, mode, lang))

@app.route("/talk", methods=["POST"])
def talk():
    data = request.get_json(force=True)
    mode = data.get("mode", "speak")
    lang = data.get("lang", STT_LANG)

    user_text = record_and_transcribe(
        device_index=STT_DEVICE,
        duration=STT_DURATION,
        model_name=STT_MODEL,
        language=STT_LANG,
    )
    logging.info("STT result: %r", user_text)

    if user_text == "sorry, didnt understand":
        show_emoji("")  # clear screen
        return jsonify({
            "user_text": "",
            "response": "sorry, didnt understand",
            "emoji": ""
        })

    return jsonify(process_user_input(user_text, mode, lang))

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()

    webbrowser.open(f"http://{ip}:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
