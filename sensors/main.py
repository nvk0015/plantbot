from .soil_moisture_sensor import get_soil_moisture_pct
from .bme280_sensor import get_bme_readings
from .veml7700_lightsensor import get_light_lux, get_light_category

def evaluate_plant_status(temperature_c, soil_moisture_pct, humidity_pct):
    # existing temp moisture humidity code
    # unchanged
    ...

def main():
    temperature_c, humidity_pct, pressure_hpa = get_bme_readings()
    soil_moisture_pct = get_soil_moisture_pct()
    light_lux = get_light_lux()
    light_cat = get_light_category(light_lux)

    status = evaluate_plant_status(temperature_c, soil_moisture_pct, humidity_pct)
    overall = status["overall"]

    # add light into reasons
    status["light"] = light_cat

    # override for extremes as before
    if soil_moisture_pct > 80:
        overall = "very_moist"
    elif soil_moisture_pct < 20:
        overall = "very_dry"
    elif temperature_c > 30:
        overall = "very_hot"
    elif temperature_c < 10:
        overall = "very_cold"
    elif humidity_pct > 80:
        overall = "very_humid"
    elif humidity_pct < 20:
        overall = "very_dry_air"
    # now handle light extremes
    elif light_cat == "very_dark":
        overall = "light_deprived"
    elif light_cat == "very_sunny":
        overall = "very_happy"

    return {
        "overall": overall,
        "reasons": status,
        "readings": {
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
            "pressure_hpa": pressure_hpa,
            "soil_moisture_pct": soil_moisture_pct,
            "light_lux": light_lux,
        },
    }

if __name__ == "__main__":
    print(main())
