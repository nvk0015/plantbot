# sensors/veml7700_lightsensor.py
try:
    import board
    import busio
    import adafruit_veml7700

    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_veml7700.VEML7700(i2c)

    def get_light_lux():
        return sensor.lux

    def get_light_category(lux):
        if lux < 1:
            return "very_dark"
        elif lux < 10:
            return "lightly_dark"
        elif lux < 1000:
            return "ambient"
        elif lux < 10000:
            return "sunny"
        else:
            return "very_sunny"

except Exception as e:
    print("[veml7700_lightsensor] hw not available using dummy data", e)

    def get_light_lux():
        return 100.0

    def get_light_category(lux):
        return "ambient"
