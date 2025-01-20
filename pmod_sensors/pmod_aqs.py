import sys
import smbus
import time
import math

class PmodAQS:
    SMBUS_CHANNEL = 1
    PmodAQS_HW_ID = 0x20
    PmodAQS_HW_ID_CODE = 0x81
    PmodAQS_BOOTLOADER_APP_START = 0xF4
    PmodAQS_DRIVE_MODE_1SEC = 0x01
    PmodAQS_MEAS_MODE = 0x01
    PmodAQS_ENV_DATA = 0x05
    PmodAQS_ALG_RESULT_DATA = 0x02
    PmodAQS_NTC = 0x06
    PmodAQS_THRESHOLDS = 0x10
    PmodAQS_SW_RESET = 0xFF
    PmodAQS_STATUS = 0x00
    PmodAQS_ERROR_ID = 0xE0
    PmodAQS_REF_RESISTOR = 100000

    def __init__(self, i2c_addr, debug, verbose):
        self._i2caddr = i2c_addr
        self._bus = smbus.SMBus(self.SMBUS_CHANNEL)
        self._tempOffset = 0
        self._TVOC = 0
        self._eCO2 = 0
        self._status = self.status()
        self._meas_mode = self.meas_mode()
        self._error_id = self.error_id()
        self._DEBUG = debug
        self._VERBOSE = verbose
        self.initialize_AMSCCS811()

    def initialize_AMSCCS811(self):
        # Send the reset sequence to the chip
        reset_seq = [0x11, 0xE5, 0x72, 0x8A]
        self.write(self.PmodAQS_SW_RESET, reset_seq)
        # wait for the reset to complete
        time.sleep(0.1)

        # confirm that the chip reports the right HW ID
        hw_id = self.read8(self.PmodAQS_HW_ID)
        if hw_id != self.PmodAQS_HW_ID_CODE:
            if self._VERBOSE:
                print("ERROR: HW ID = ", hw_id, "Expected = ", AMSCCS811_HW_ID_CODE)
            sys.exit()

        # confirm that the chip reports that it is in boot mode and that it has a valid application loaded
        self.readStatus()
        if (self._status.FW_MODE) or (not self._status.APP_VALID):
            if self._VERBOSE:
                print("ERROR: Not in boot mode or invalid application after reset")
                print("STATUS.ERROR = ", self._status.ERROR)
                print("STATUS.DATA_READY = ", self._status.DATA_READY)
                print("STATUS.APP_VALID = ", self._status.APP_VALID)
                print("STATUS.FW_MODE = ", self._status.FW_MODE)
            sys.exit()

        # Set the CCS811 mode of operation to mode 1: Constant power mode, IQS measurement every second
        # step 1 - send app start
        self.writeByte(self.PmodAQS_BOOTLOADER_APP_START)
        time.sleep(0.1)

        hw_id = self.read8(self.PmodAQS_HW_ID)
        if self._VERBOSE:
            print("HW ID = ", hw_id)
        # step 2 - check for errors
        self.readStatus()
        if self._VERBOSE:
            print("STATUS.ERROR = ", self._status.ERROR)
            print("STATUS.DATA_READY = ", self._status.DATA_READY)
            print("STATUS.APP_VALID = ", self._status.APP_VALID)
            print("STATUS.FW_MODE = ", self._status.FW_MODE)
        if self._status.ERROR:
            if self._VERBOSE:
                print("ERROR: AMSCCS811 ERROR Status after setting mode")
                err_id = self.read8(self.PmodAQS_ERROR_ID)
                print("ERROR_ID = ", err_id)
            sys.exit()
        if not self._status.FW_MODE:
            if self._VERBOSE:
                print("ERROR: AMSCCS811 is in boot mode")
            sys.exit()

        # step 3 - disable CCS811 interrupts
        self._meas_mode.INT_DATARDY = 0
        self.write8(self.PmodAQS_MEAS_MODE, self._meas_mode.get())
        
        # step 4 - set the driver mode
        self._meas_mode.DRIVE_MODE = self.PmodAQS_DRIVE_MODE_1SEC
        self.write8(self.PmodAQS_MEAS_MODE, self._meas_mode.get())

        return True
        
    def enableInterrupt(self):
        self._meas_mode.INT_DATARDY = 1
        self.write8(self.PmodAQS_MEAS_MODE, self._meas_mode.get())

    def available(self):
        self._status.set(self.read8(self.PmodAQS_STATUS))
        return self._status.DATA_READY

    def readData(self):
        if not self.available():
            return False
        buf = self.read(self.PmodAQS_ALG_RESULT_DATA, 8)
        self._eCO2 = (buf[0] << 8) | buf[1]
        self._TVOC = (buf[2] << 8) | buf[3]
        return buf[5] if self._status.ERROR else 0

    def setEnvironmentalData(self, humidity, temperature):
        hum_perc = humidity << 1
        fractional, temperature = math.modf(temperature)
        temp_conv = (((int(temperature) + 25) << 9) | int(fractional / 0.001953125) & 0x1FF)
        buf = [hum_perc, 0x00, (temp_conv >> 8) & 0xFF, temp_conv & 0xFF]
        self.write(self.PmodAQS_ENV_DATA, buf)

    def calculateTemperature(self):
        buf = self.read(self.PmodAQS_NTC, 4)
        vref = (buf[0] << 8) | buf[1]
        vntc = (buf[2] << 8) | buf[3]
        rntc = vntc * self.PmodAQS_REF_RESISTOR / vref
        if (self._DEBUG):
            print("vref = ", vref)
            print("vntc = ", vntc)
            print("rntc = ", rntc)
        ntc_temp = math.log(rntc / self.PmodAQS_REF_RESISTOR) / 3380 + 1.0 / (25 + 273.15)
        return 1.0 / ntc_temp - 273.15 - self._tempOffset

    def setThresholds(self, low_med, med_high, hysteresis=50):
        buf = [(low_med >> 8) & 0xF, low_med & 0xF, (med_high >> 8) & 0xF, med_high & 0xF, hysteresis]
        self.write(self.PmodAQS_THRESHOLDS, buf)

    def readStatus(self):
        self._status.set(self.read8(self.PmodAQS_STATUS))
        return self._status.ERROR

    def writeByte(self, value):
        if self._DEBUG:
            print("Write Byte = ", value)
        self._bus.write_byte(self._i2caddr, value)

    def write8(self, reg, value):
        self.write(reg, [value])

    def read8(self, reg):
        buffer = self._bus.read_byte_data(self._i2caddr, reg)
        if self._DEBUG:
            print("read8 addr = ", reg, "read8 buffer = ", buffer)
        return buffer

    def read(self, reg, num):
        buffer = self._bus.read_i2c_block_data(self._i2caddr, reg, num)
        if self._DEBUG:
            print("read addr = ", reg, "read buffer = " , buffer)
#        self._bus.write_byte(self._i2caddr, reg)
        return buffer

    def write(self, reg, buf):
        if self._DEBUG:
            print("write addr = ", reg, "write or write8 buffer = ", buf)
        self._bus.write_i2c_block_data(self._i2caddr, reg, buf)

    class status:
        def __init__(self):
            self.ERROR = 0
            self.DATA_READY = 0
            self.APP_VALID = 0
            self.FW_MODE = 0

        def set(self, data):
            self.ERROR = data & 0x01
            self.DATA_READY = (data >> 3) & 0x01
            self.APP_VALID = (data >> 4) & 0x01
            self.FW_MODE = (data >> 7) & 0x01

    class meas_mode:
        def __init__(self):
            self.INT_THRESH = 0
            self.INT_DATARDY = 0
            self.DRIVE_MODE = 0

        def get(self):
            return (self.INT_THRESH << 2) | (self.INT_DATARDY << 3) | (self.DRIVE_MODE << 4)

    class error_id:
        def __init__(self):
            self.WRITE_REG_INVALID = 0
            self.READ_REG_INVALID = 0
            self.MEASMODE_INVALID = 0
            self.MAX_RESISTANCE = 0
            self.HEATER_FAULT = 0
            self.HEATER_SUPPLY = 0

        def set(self, data):
            self.WRITE_REG_INVALID = data & 0x01
            self.READ_REG_INVALID = (data & 0x02) >> 1
            self.MEASMODE_INVALID = (data & 0x04) >> 2
            self.MAX_RESISTANCE = (data & 0x08) >> 3
            self.HEATER_FAULT = (data & 0x10) >> 4
            self.HEATER_SUPPLY = (data & 0x20) >> 5

    def getTVOC(self):
        return self._TVOC

    def geteCO2(self):
        return self._eCO2

    def setTempOffset(self, offset):
        self._tempOffset = offset

