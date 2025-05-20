# /home/nvk15697/plants_speak/poc/sensors/bme280_sensor.py

"""
Return (temperature_c, humidity_pct, pressure_hpa).

If the BME280 hardware / libraries are missing, we fall back
to safe dummy readings so the rest of the stack never crashes.
"""

from typing import Tuple

try:
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280

    # Create I2C bus and sensor object
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c)

    # Optionally override the I2C address (default 0x77):
    # sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

    def get_bme_readings() -> Tuple[float, float, float]:
        """
        Returns:
          (temperature_c, humidity_pct, pressure_hpa)
        """
        temp_c = sensor.temperature
        humidity = sensor.humidity
        pressure = sensor.pressure
        return temp_c, humidity, pressure

except Exception as exc:
    print("[bme280_sensor] HW not available – using dummy data:", exc)

    def get_bme_readings() -> Tuple[float, float, float]:
        return 22.0, 50.0, 1013.0     # comfy fallback values
