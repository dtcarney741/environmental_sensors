import time
import pmod_aqs

VERBOSE = True
DEBUG = True

PmodAQS_ADDRESS = 0x5B
ROOM_TEMPERATURE = 25               # in deg C
SAMPLE_PERIOD = 5                   # in s

print("PmodAQS Test")

pmod1 = pmod_aqs.PmodAQS(PmodAQS_ADDRESS, debug=DEBUG, verbose=VERBOSE)

print("Sensor Started")

# Calibrate temperature sensor
#while not pmod1.available():
#    temp = pmod1.calculateTemperature()
#    pmod1.setTempOffset(temp-ROOM_TEMPERATURE)

while True:
    if not pmod1.readData():
        print("CO2: ", pmod1.geteCO2(), "ppm")
        print("TVOC: ", pmod1.getTVOC(), "ppb")
    else:
        print("ERROR!")

    time.sleep(SAMPLE_PERIOD)
