# Wokwi, Raspberry Pi Pico, MicroPython. Негативний тест TC-11.
# Схема така сама, як у 02_i2c_mpu6050.py (AD0 не підключений, тобто на GND, адреса датчика 0x68).
# Умисна поломка: у коді адреса 0x69. Очікується OSError на рядку з WHO_AM_I,
# а на логічному аналізаторі: Address write: 69 -> NACK -> Stop.
from machine import I2C, Pin
import struct, time

i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
print("scan:", [hex(a) for a in i2c.scan()])  # ['0x68']

ADDR = 0x69
print("WHO_AM_I:", hex(i2c.readfrom_mem(ADDR, 0x75, 1)[0]))  # тут падає: OSError ETIMEDOUT
i2c.writeto_mem(ADDR, 0x6B, b'\x00')  # розбудити датчик

while True:
    ax, ay, az = struct.unpack('>hhh', i2c.readfrom_mem(ADDR, 0x3B, 6))
    t = struct.unpack('>h', i2c.readfrom_mem(ADDR, 0x41, 2))[0] / 340 + 36.53
    print("accel g: %.2f %.2f %.2f | temp: %.1f C" % (ax/16384, ay/16384, az/16384, t))
    time.sleep(1)
