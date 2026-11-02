"""Прогін UART loopback на кількох швидкостях: втрати і час на 1000 повідомлень.

Потрібна перемичка: GPIO14 TX (пін 8) <-> GPIO15 RX (пін 10).
Запуск:  python3 src/pi3/uart_speed_sweep.py
         python3 src/pi3/uart_speed_sweep.py 115200 921600   # свої швидкості
Порт береться з /dev/serial0, тому скрипт однаково працює і з ttyS0 (mini-UART),
і з ttyAMA0 (PL011 після dtoverlay=disable-bt).
"""
import os
import sys
import time

import serial

PORT = "/dev/serial0"
COUNT = 1000
DEFAULT_BAUDS = [115200, 230400, 460800, 921600]


def run(baud):
    port = serial.Serial(PORT, baud, timeout=0.5)
    lost = 0
    corrupted = 0
    started = time.time()
    try:
        port.reset_input_buffer()
        for i in range(COUNT):
            msg = ("msg-%04d\n" % i).encode()
            port.write(msg)
            got = port.readline()
            if got != msg:
                lost += 1
                if got:  # щось прийшло, але не те: пошкоджені дані, а не тиша
                    corrupted += 1
    finally:
        port.close()
    elapsed = time.time() - started
    # Теоретичний час на дроті: 9 байт x 10 біт (старт + 8 даних + стоп)
    wire = COUNT * 9 * 10 / baud
    return lost, corrupted, elapsed, wire


def main():
    bauds = [int(b) for b in sys.argv[1:]] or DEFAULT_BAUDS
    print("порт: %s -> %s" % (PORT, os.path.realpath(PORT)))
    print("%8s | %6s | %10s | %8s | %10s" % ("baud", "lost", "corrupted", "time, s", "wire, s"))
    for baud in bauds:
        lost, corrupted, elapsed, wire = run(baud)
        print("%8d | %6d | %10d | %8.2f | %10.3f" % (baud, lost, corrupted, elapsed, wire))


if __name__ == "__main__":
    main()
