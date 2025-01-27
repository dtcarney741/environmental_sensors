import sys
import time
import math

class Pmod_Hygro:
    HYGROI2C_TMP_REG = 0x00
    HYGROI2C_HUM_REG = 0x01
    HYGROI2C_CONFIG_REG = 0x02
    HYGROI2C_HW_ID_REG = 0xFE

    HYGROI2C_HW_ID_CODE = 0x5449
    HYGROI2C_CONVERSION_TIME = 0.007        # 6.5 ms for temperature and 6.35 ms for humidity are the conversion times from the TI HDC1080 datasheet

    def __init__(self, i2c_addr, i2c_bus, debug, verbose):
        self._i2c_addr = i2c_addr
        self._i2c_bus = i2c_bus
        self._DEBUG = debug
        self._VERBOSE = verbose
        self.initialize_TIHDC1080()

    def initialize_TIHDC1080(self):
        # confirm that the chip reports the right HW ID
        buffer = self._i2c_bus.read(self._i2c_addr, self.PmodAQS_HW_ID, 2)
        hw_id = buffer[1] + buffer[0]*(2**8)
        if hw_id != self.HYGROI2C_HW_ID_CODE:
            if self._VERBOSE:
                print("ERROR: HW ID = ", hw_id, "Expected = ", self.HYGROI2C_HW_ID_CODE)
            sys.exit()

        # use non-sequential acquisition mode, all other config bits are default
        self._i2c_bus.write(self._i2c_addr, self.HYGROI2C_CONFIG_REG, 0x00)

        return True

    def read_temperature(self):
        self._i2c_bus.write_byte(self._i2c_addr, self.HYGROI2C_TMP_REG)
        time.sleep(self.HYGROI2C_CONVERSION_TIME)
        [MSB, LSB] = self._i2c_bus.read(self._i2c_addr, self.HYGROI2C_TMP_REG, 2)
        temp_ui16 = LSB + MSB*(2**8)
        temp = temp_ui16 / (2**16) * 165 - 40
        return temp

    def read_humidity(self):
        self._i2c_bus.write_byte(self._i2c_addr, self.HYGROI2C_HUM_REG)
        time.sleep(self.HYGROI2C_CONVERSION_TIME)
        [MSB, LSB] = self._i2c_bus.read(self._i2c_addr, self.HYGROI2C_HUM_REG, 2)
        hum_ui16 = LSB + MSB*(2**8)
        hum = hum_ui16 / (2**16) * 100
        return hum