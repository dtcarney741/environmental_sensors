import time
import pmod_aqs
import pi_i2c

VERBOSE = True
DEBUG = True
SMBUS_CHANNEL = 1

PmodAQS_ADDRESS = 0x5B
ROOM_TEMPERATURE = 25               # in deg C
SAMPLE_PERIOD = 5                   # in s

print("PmodAQS Test")

i2c_bus = pi_i2c.Pi_I2C(SMBUS_CHANNEL, debug=DEBUG)
pmod1 = pmod_aqs.PmodAQS(PmodAQS_ADDRESS, i2c_bus, debug=DEBUG, verbose=VERBOSE)

print("Sensor Started")

# Calibrate temperature sensor
#while not pmod1.available():
#    temp = pmod1.calculate_temperature()
#    pmod1.set_temp_offset(temp-ROOM_TEMPERATURE)

while True:
    if not pmod1.read_data():
        print("CO2: ", pmod1.get_eCO2(), "ppm")
        print("TVOC: ", pmod1.get_TVOC(), "ppb")
    else:
        print("ERROR!")

    time.sleep(SAMPLE_PERIOD)
