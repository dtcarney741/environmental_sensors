import sys
import smbus
import time
import math

class Pi_I2C:

    def __init__(self, smbus_channel, debug):
        self._bus = smbus.SMBus(smbus_channel)
        self._DEBUG = debug

    def write_byte(self, i2c_addr, value):
        if self._DEBUG:
            print("Write Byte: i2c_addr = ", i2c_addr, " value = ", value)
        self._bus.write_byte(i2c_addr, value)

    def write8(self, i2c_addr, reg, value):
        self.write(i2c_addr, reg, [value])

    def read8(self, i2c_addr, reg):
        buffer = self._bus.read_byte_data(i2c_addr, reg)
        if self._DEBUG:
            print("read8: i2c_addr = ", i2c_addr, " addr = ", reg, "read8 buffer = ", buffer)
        return buffer

    def read(self, i2c_addr, reg, num):
        buffer = self._bus.read_i2c_block_data(i2c_addr, reg, num)
        if self._DEBUG:
            print("read: i2c_addr = ", i2c_addr, " addr = ", reg, "read buffer = " , buffer)
#        self._bus.write_byte(self._i2caddr, reg)
        return buffer

    def write(self, i2c_addr, reg, buf):
        if self._DEBUG:
            print("write: i2c_addr = ", i2c_addr, " addr = ", reg, "buffer = ", buf)
        self._bus.write_i2c_block_data(i2c_addr, reg, buf)

