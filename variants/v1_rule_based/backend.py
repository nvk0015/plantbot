# /home/nvk15697/plants_speak/poc/variants/v1_rule_based/backend.py
# /home/nvk15697/plants_speak/poc/variants/v1_rule_based/backend.py
import os
import sys
import json
import logging
import requests                      # NEW

# ---- Make "sensors" importable ----------------------------------------------
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sensors.main import main as sensor_main
# -----------------------------------------------------------------------------

logging.basicConfig(
    filename="plant_interface.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

OLLAMA_MODEL = "qwen:0.5b"
# Default to localhost:11434 but allow override
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# -----------------------------------------------------------------------------


def build_prompt(user_prompt: str | None = None) -> str:
    try:
        pkg = sensor_main()
    except Exception:
        logging.exception("Sensor read failed, falling back to dummy values")
        pkg = {
            "overall": "mixed",
            "reasons": {"temperature": "unknown", "soil_moisture": "unknown", "humidity": "unknown"},
            "readings": {"temperature_c": 22, "humidity_pct": 50, "pressure_hpa": 1013, "soil_moisture_pct": 45},
        }

    o, r, s = pkg["overall"], pkg["reasons"], pkg["readings"]
    prompt = (
        "You are a houseplant speaking in first person to your owner.\n"
        f"I currently feel *{o.replace('_', ' ')}* because:\n"
        f" - temperature is {s['temperature_c']:.1f}°C ({r['temperature'].replace('_', ' ')}),\n"
        f" - soil moisture is {s['soil_moisture_pct']:.0f}% ({r['soil_moisture'].replace('_', ' ')}),\n"
        f" - humidity is {s['humidity_pct']:.0f}% ({r['humidity'].replace('_', ' ')}).\n"
    )

    if user_prompt:
        prompt += f"\nOwner says: \"{user_prompt}\"\nPlant replies:"
    else:
        prompt += "\nPlant speaks to the owner:"
    return prompt


# -----------------------------------------------------------------------------


def call_api(prompt: str) -> str:
    """Return the model text or a readable error message."""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logging.error("Request to Ollama failed: %s", exc)
        return f"Ollama request error: {exc}"

    try:
        data = resp.json()
    except ValueError:
        logging.error("Ollama returned non-JSON: %s", resp.text[:300])
        return "Model returned invalid JSON."

    if "error" in data:
        logging.error("Model error: %s", data['error'])
        return f"Model error: {data['error']}"

    # Ollama uses the field `response`
    return data.get("response", "Could not find model reply in its JSON.")


# -----------------------------------------------------------------------------


def generate_message(user_prompt: str | None = None) -> str:
    prompt = build_prompt(user_prompt)
    logging.info("Prompt: %s", prompt.replace("\n", " "))
    reply = call_api(prompt)
    logging.info("Reply: %s", reply)
    return reply


if __name__ == "__main__":
    # Simple CLI test
    print(generate_message())
