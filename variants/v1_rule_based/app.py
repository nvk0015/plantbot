# /home/nvk15697/plants_speak/poc/variants/v1_rule_based/app.py
from flask import Flask, render_template, request, jsonify
import backend
import utils
import logging
import webbrowser
import socket

logging.basicConfig(
    filename="plant_interface.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app = Flask(__name__)

@app.route("/")
def index():
    try:
        return render_template("index.html")
    except Exception as e:
        logging.error("Template rendering failed: %s", str(e))
        return "<h1>Missing index.html!</h1><p>Please add templates/index.html</p>", 500

@app.route("/hello", methods=["POST"])
def hello():
    mode = request.json.get("mode", "text")
    logging.info("/hello invoked (mode=%s)", mode)

    result = backend.generate_message()
    text, emoji = result["response"], result["emoji"]

    if mode == "speak":
        utils.speak_text(text)
        logging.info("Speaking done.")

    return jsonify({"response": text, "emoji": emoji})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mode = data.get("mode", "text")
    user_input = data.get("user_input", "").strip()
    logging.info("/chat invoked (mode=%s, input=%s)", mode, user_input)

    if user_input and len(user_input.split(". ")) > 2:
        return jsonify({"error": "Please enter no more than two sentences."}), 400

    result = backend.generate_message(user_prompt=user_input or None)
    text, emoji = result["response"], result["emoji"]

    if mode == "speak":
        utils.speak_text(text)
        logging.info("Speaking done.")

    return jsonify({"response": text, "emoji": emoji})

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    url = f"http://{local_ip}:5000"
    logging.info(f"Opening browser at {url}")
    webbrowser.open(url)
    app.run(host="0.0.0.0", port=5000, debug=False)