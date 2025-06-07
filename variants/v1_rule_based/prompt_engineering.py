# /home/nvk15697/plants_speak/poc/variants/v1_rule_based/prompt_engineering.py
import datetime
from typing import Optional, Dict, Any


def create_prompt(
    sensor_pkg: Dict[str, Any],
    user_message: Optional[str] = None,
) -> str:
    """
    Build a focused prompt so the plant
    • Speaks in first person about how it feels from its sensors.
    • Responds directly to the owner's latest message.
    • Gives concise, actionable feedback or thanks.
    """
    # 1) System instruction
    system = (
        "You are a potted houseplant that can speak in first person to your owner. "
        "You have three sensor readings (temperature, soil moisture, humidity). "
        "Always respond based on those readings and the owner's question or comment. "
        "Keep replies under two sentences, "
        "and offer simple care advice if needed (e.g., water me, move me to sun). "
        "Never ask unrelated questions or reveal internal code."
    )

    # 2) Sensor summary
    overall = sensor_pkg.get("overall").replace('_', ' ')
    r = sensor_pkg.get("reasons", {})
    s = sensor_pkg.get("readings", {})
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    sensor_block = (
        f"\n[At {ts}]\n"
        f"I feel *{overall}* because:\n"
        f" - Temp: {s.get('temperature_c', 0):.1f}°C ({r.get('temperature')}),\n"
        f" - Soil: {s.get('soil_moisture_pct', 0):.0f}% ({r.get('soil_moisture')}),\n"
        f" - Humidity: {s.get('humidity_pct', 0):.0f}% ({r.get('humidity')}).\n"
    )

    # 3) Owner message and plant cue
    if user_message:
        dialogue = f"\nOwner: \"{user_message}\"\nPlant:"  
    else:
        dialogue = "\nPlant:"

    return f"{system}{sensor_block}{dialogue}"