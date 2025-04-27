# /home/nvk15697/plants_speak/poc/sensors/bme280_sensor.py
"""
Return (temperature_c, humidity_pct, pressure_hpa).

If the BME280 hardware / libraries are missing, we fall back
to safe dummy readings so the rest of the stack never crashes.
"""
from typing import Tuple

try:
    import smbus2
    import bme280

    _BUS_NUMBER = 1
    _ADDRESS = 0x76
    _bus = smbus2.SMBus(_BUS_NUMBER)
    _params = bme280.load_calibration_params(_bus, _ADDRESS)

    def get_bme_readings() -> Tuple[float, float, float]:
        data = bme280.sample(_bus, _ADDRESS, _params)
        return data.temperature, data.humidity, data.pressure

except Exception as exc:          # library not found or bus error
    print("[bme280_sensor] HW not available – using dummy data:", exc)

    def get_bme_readings() -> Tuple[float, float, float]:
        return 22.0, 50.0, 1013.0     # comfy fallback values
