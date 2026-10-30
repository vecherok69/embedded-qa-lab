# Wokwi, Raspberry Pi Pico, MicroPython.
# Схема: один дріт GP4 (пін 6) -> GP5 (пін 7), UART1 у петлі.
# На UART0 (GP0/GP1) у Wokwi сидить консоль MicroPython, тому петля зроблена на UART1.
from machine import UART, Pin
import time

uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
n = 0
while True:
    msg = "[%d ms] count=%d\n" % (time.ticks_ms(), n)
    uart.write(msg)
    time.sleep(0.1)
    print("TX:", msg.strip(), "| RX:", uart.read())
    n += 1
    time.sleep(0.9)
