"""
Return soil-moisture percentage.

Falls back to 45 % if ADS1115 hardware libs are missing.
"""
try:
    import board
    import busio
    from adafruit_ads1x15.ads1115 import ADS1115, P0
    from adafruit_ads1x15.analog_in import AnalogIn

    V_DRY = 2.00    # volts in dry air/soil
    V_WET = 0.50    # volts in water / saturated soil

    _i2c = busio.I2C(board.SCL, board.SDA)
    _ads = ADS1115(_i2c)
    _ads.gain = 1
    _chan = AnalogIn(_ads, P0)

    def get_soil_moisture_pct() -> float:
        v = _chan.voltage
        pct = (V_DRY - v) / (V_DRY - V_WET) * 100
        return max(0.0, min(100.0, pct))

except Exception as exc:
    print("[soil_moisture_sensor] HW not available – using dummy data:", exc)

    def get_soil_moisture_pct() -> float:
        return 45.0
