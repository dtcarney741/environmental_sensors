import time
import pmod_aqs
import pi_i2c
import pmod_hygro

VERBOSE = True
DEBUG = True
SMBUS_CHANNEL = 1

PMOD_AQS_ADDRESS = 0x5B
PMOD_HYGRO_ADDR = 0x40

ROOM_TEMPERATURE = 25               # in deg C
SAMPLE_PERIOD = 5                   # in s

print("Pmod_AQS and Pmod_Hygro Test")

i2c_bus = pi_i2c.Pi_I2C(SMBUS_CHANNEL, debug=DEBUG)
pmod1 = pmod_aqs.Pmod_AQS(PMOD_AQS_ADDRESS, i2c_bus, debug=DEBUG, verbose=VERBOSE)
print("Pmod_AQS Sensor Started")
pmod2 = pmod_hygro.Pmod_Hygro(PMOD_HYGRO_ADDRESS, i2c_bus, debug=DEBUG, verbose=VERBOSE)
print("Pmod_Hygro Sensor Started")

# Calibrate temperature sensor
#while not pmod1.available():
#    temp = pmod1.calculate_temperature()
#    pmod1.set_temp_offset(temp-ROOM_TEMPERATURE)

while True:
    if not pmod1.read_data():
        print("CO2: ", pmod1.get_eCO2(), "ppm")
        print("TVOC: ", pmod1.get_TVOC(), "ppb")
    else:
        print("PMOD AQS ERROR!")

    temp = pmod2.read_temperature()
    humidity = pmod2.read_humidity()
    print("Temperature = ", temp)
    print("Humidity = ", humidity)

    time.sleep(SAMPLE_PERIOD)
