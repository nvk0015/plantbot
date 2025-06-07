# /home/nvk15697/plants_speak/poc/sensors/bme280_sensor.py

from typing import Tuple

try:
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280

    # create I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # try the 0x76 address first (your i2cdetect showed 76)
    try:
        sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    except Exception:
        # fallback to the more common 0x77
        sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)

    def get_bme_readings() -> Tuple[float, float, float]:
        """
        Returns real sensor values:
          (temperature_c, humidity_pct, pressure_hpa)
        """
        temp_c    = sensor.temperature
        humidity  = sensor.humidity
        pressure  = sensor.pressure
        return temp_c, humidity, pressure

except Exception as exc:
    print("[bme280_sensor] HW not available – using dummy data:", exc)

    def get_bme_readings() -> Tuple[float, float, float]:
        # fallback values so nothing crashes
        return 22.0, 50.0, 1013.0
