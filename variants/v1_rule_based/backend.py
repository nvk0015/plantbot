# variants/v1_rule_based/backend.py
import os, sys, logging, requests
import expressions_store, prompt_engineering

# make sensors importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from sensors.main import main as sensor_main

logging.basicConfig(
    filename="plant_interface.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

OLLAMA_MODEL = "gemma2:2b"
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

def call_api(prompt: str) -> str:
    try:
        r = requests.post(OLLAMA_URL,
                          json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                          timeout=120)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        logging.exception("Ollama request failed")
        return f"API error: {exc}"

    if data.get("error"):
        logging.error("Model error: %s", data["error"])
        return f"Model error: {data['error']}"

    return data.get("response", "No response from model.")

def generate_message(user_prompt: str | None = None) -> dict:
    """Return {'response': str, 'emoji': str}."""
    try:
        pkg = sensor_main()
    except Exception:
        logging.exception("sensor_main failed – using defaults")
        pkg = {
            "overall":  "mixed",
            "reasons":  {"temperature": "unknown", "soil_moisture": "unknown", "humidity": "unknown"},
            "readings": {"temperature_c": 22, "humidity_pct": 50, "pressure_hpa": 1013, "soil_moisture_pct": 45},
        }

    prompt = prompt_engineering.create_prompt(pkg, user_prompt)
    logging.info("Prompt: %s", prompt.replace("\n", " "))

    reply = call_api(prompt)
    logging.info("Reply: %s", reply)

    emoji = expressions_store.get_emoji(pkg.get("overall"))
    return {"emoji": emoji, "response": reply}

if __name__ == "__main__":
    print(generate_message())
