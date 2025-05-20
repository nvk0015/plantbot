# /home/nvk15697/.../app.py
from flask import Flask, render_template, request, jsonify
import backend, utils, logging, socket, webbrowser

logging.basicConfig(
    filename="plant_interface.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hello", methods=["POST"])
def hello():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "text")
    lang = data.get("lang", "en")

    msg = backend.generate_message()
    text, emoji = msg["response"], msg["emoji"]

    if mode == "speak":
        utils.speak_text(text, lang)
    return jsonify({"response": text, "emoji": emoji})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    mode  = data.get("mode", "text")
    lang  = data.get("lang", "en")
    user  = (data.get("user_input") or "").strip()

    if user and len(user.split(". ")) > 2:
        return jsonify({"error": "Please enter no more than two sentences."}), 400

    msg = backend.generate_message(user or None)
    text, emoji = msg["response"], msg["emoji"]

    if mode == "speak":
        utils.speak_text(text, lang)
    return jsonify({"response": text, "emoji": emoji})

if __name__ == "__main__":
    # get LAN IP for auto-opening
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    url = f"http://{ip}:5000"
    webbrowser.open(url)
    app.run(host="0.0.0.0", port=5000, debug=False)
