# Wokwi, Raspberry Pi Pico, MicroPython.
# Схема: MPU6050 VCC -> 3V3(OUT) (пін 36), GND -> GND (пін 38),
#        SDA -> GP16 (пін 21), SCL -> GP17 (пін 22).
# Логічний аналізатор: D0 -> GP16, D1 -> GP17, GND -> GND.
from machine import I2C, Pin
import struct
import time

i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
print("scan:", [hex(a) for a in i2c.scan()])  # очікується ['0x68']

ADDR = 0x68
# WHO_AM_I: регістр 0x75, у MPU6050 повертає 0x68
print("WHO_AM_I:", hex(i2c.readfrom_mem(ADDR, 0x75, 1)[0]))
# Регістр 0x6B (PWR_MGMT_1): записати 0, щоб розбудити датчик
i2c.writeto_mem(ADDR, 0x6B, b"\x00")

while True:
    ax, ay, az = struct.unpack(">hhh", i2c.readfrom_mem(ADDR, 0x3B, 6))
    t = struct.unpack(">h", i2c.readfrom_mem(ADDR, 0x41, 2))[0] / 340 + 36.53
    print("accel g: %.2f %.2f %.2f | temp: %.1f C" % (ax / 16384, ay / 16384, az / 16384, t))
    time.sleep(1)
