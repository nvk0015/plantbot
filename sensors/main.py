# /home/nvk15697/plants_speak/poc/sensors/main.py
from .soil_moisture_sensor import get_soil_moisture_pct
from .bme280_sensor        import get_bme_readings


def evaluate_plant_status(temperature_c, soil_moisture_pct, humidity_pct):
    temp_ranges = {
        "highly_stressed":     lambda t: (t < 10) or (t > 30),
        "moderately_stressed": lambda t: (10 <= t < 15) or (24 < t <= 27),
        "happy":               lambda t: (15 <= t <= 24),
    }
    moisture_ranges = {
        "highly_stressed":     lambda m: (m < 20) or (m > 80),
        "moderately_stressed": lambda m: (20 <= m < 40) or (60 < m <= 80),
        "happy":               lambda m: (40 <= m <= 60),
    }
    humidity_ranges = {
        "highly_stressed":     lambda h: (h < 20) or (h > 80),
        "moderately_stressed": lambda h: (20 <= h < 40) or (60 < h <= 80),
        "happy":               lambda h: (40 <= h <= 60),
    }

    def _cat(val, ranges):
        for cat, test in ranges.items():
            if test(val):
                return cat
        return "unknown"

    t_stat = _cat(temperature_c,  temp_ranges)
    m_stat = _cat(soil_moisture_pct, moisture_ranges)
    h_stat = _cat(humidity_pct,    humidity_ranges)

    if "highly_stressed" in (t_stat, m_stat, h_stat):
        overall = "highly_stressed"
    elif "moderately_stressed" in (t_stat, m_stat, h_stat):
        overall = "moderately_stressed"
    elif all(s == "happy" for s in (t_stat, m_stat, h_stat)):
        overall = "happy"
    else:
        overall = "mixed"

    return {
        "temperature":   t_stat,
        "soil_moisture": m_stat,
        "humidity":      h_stat,
        "overall":       overall,
    }


def main():
    temp_c, humidity_pct, pressure_hpa = get_bme_readings()
    soil_pct = get_soil_moisture_pct()

    status = evaluate_plant_status(temp_c, soil_pct, humidity_pct)

    reasons = {
        "temperature":   status["temperature"],
        "soil_moisture": status["soil_moisture"],
        "humidity":      status["humidity"],
    }
    overall = status["overall"]

    return {
        "overall":  overall,
        "reasons":  reasons,
        "readings": {
            "temperature_c":     temp_c,
            "humidity_pct":      humidity_pct,
            "pressure_hpa":      pressure_hpa,
            "soil_moisture_pct": soil_pct,
        },
    }


if __name__ == "__main__":
    print(main())
