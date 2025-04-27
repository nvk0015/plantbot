import os
import sys
import logging
import requests
import expressions_store
import prompt_engineering

# ---- Make sensors importable ------------------------------------------------
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from sensors.main import main as sensor_main
# -----------------------------------------------------------------------------

# Logging
logging.basicConfig(
    filename="plant_interface.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

OLLAMA_MODEL = "gemma2:2b"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")


def call_api(prompt: str) -> str:
    """Send prompt to Ollama, return model text or error."""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logging.error("Ollama API error: %s", exc)
        return f"API error: {exc}"

    if error := data.get("error"):
        logging.error("Model error: %s", error)
        return f"Model error: {error}"

    return data.get("response", "No response from model.")


def generate_message(user_prompt: str | None = None) -> dict:
    """
    1) Read sensors
    2) Build prompt via prompt_engineering
    3) Call model
    4) Attach mood emoji
    """
    # 1) Sensors
    try:
        pkg = sensor_main()
    except Exception:
        logging.exception("Sensor failure, using defaults.")
        pkg = {
            "overall": "mixed",
            "reasons": {"temperature": "unknown", "soil_moisture": "unknown", "humidity": "unknown"},
            "readings": {"temperature_c": 22, "humidity_pct": 50, "pressure_hpa": 1013, "soil_moisture_pct": 45},
        }

    # 2) Prompt
    prompt = prompt_engineering.create_prompt(pkg, user_prompt)
    logging.info("Prompt: %s", prompt.replace("\n", " "))

    # 3) Model reply
    reply = call_api(prompt)
    logging.info("Reply: %s", reply)

    # 4) Emoji
    mood = pkg.get("overall", "mixed")
    emoji = expressions_store.get_emoji(mood)

    return {"response": reply, "emoji": emoji}


if __name__ == "__main__":
    print(generate_message())