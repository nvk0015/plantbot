# variants/v1_rule_based/backend.py
import os
import sys
import json
import subprocess
import logging
import shlex

# ---- Make "sensors" importable ------------------------------------------------
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sensors.main import main as sensor_main
# ------------------------------------------------------------------------------

logging.basicConfig(
    filename="plant_interface.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

OLLAMA_MODEL = "qwen:0.5b"
OLLAMA_URL = "http://localhost:11435/api/generate"

# ------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------

def call_api(prompt: str) -> str:
    """Return the model text or a readable error message."""
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    cmd = f"curl -s {OLLAMA_URL} -H 'Content-Type: application/json' -d {shlex.quote(payload)}"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        logging.error("curl timed out (no model server?)")
        return "Model server did not answer (timeout)."

    if result.returncode != 0:
        logging.error("curl failed: rc=%s stderr=%s", result.returncode, result.stderr.strip())
        return f"curl error: {result.stderr.strip() or 'non-zero exit code'}"

    raw = result.stdout.strip()
    logging.debug("Raw model JSON: %s", raw[:500])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return "Model returned invalid JSON."

    if "error" in data:
        logging.error("Model returned error: %s", data["error"])
        return f"Model error: {data['error']}"

    for key in ("response", "content", "output", "text", "message"):
        if key in data:
            content = data[key]
            if isinstance(content, str):
                return content
            elif isinstance(content, dict):
                return content.get("content", "")

    if "choices" in data and isinstance(data["choices"], list):
        return data["choices"][0].get("text", "")

    return "Could not find model reply in its JSON."

# ------------------------------------------------------------------------------

def generate_message(user_prompt: str | None = None) -> str:
    prompt = build_prompt(user_prompt)
    logging.info("Prompt: %s", prompt.replace("\n", " "))
    reply = call_api(prompt)
    logging.info("Reply: %s", reply)
    return reply
