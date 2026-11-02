"""Прогін SPI loopback на кількох швидкостях: скільки передач повернули не ті байти.

Потрібна перемичка: GPIO10 MOSI (пін 19) <-> GPIO9 MISO (пін 21).
Запуск:  python3 src/pi3/spi_speed_sweep.py
         python3 src/pi3/spi_speed_sweep.py 1000000 32000000   # свої швидкості, Гц
"""
import random
import sys
import time

import spidev

COUNT = 1000      # передач на кожній швидкості
LENGTH = 32       # байт в одній передачі
DEFAULT_SPEEDS = [500_000, 1_000_000, 4_000_000, 8_000_000, 16_000_000, 32_000_000, 62_500_000]


def run(spi, speed):
    spi.max_speed_hz = speed
    bad_transfers = 0
    bad_bytes = 0
    rng = random.Random(42)  # фіксоване зерно: однакові дані на кожному прогоні
    started = time.time()
    for _ in range(COUNT):
        data = [rng.randrange(256) for _ in range(LENGTH)]
        got = spi.xfer2(list(data))
        diff = sum(1 for a, b in zip(data, got) if a != b)
        if diff:
            bad_transfers += 1
            bad_bytes += diff
    return bad_transfers, bad_bytes, time.time() - started


def main():
    speeds = [int(s) for s in sys.argv[1:]] or DEFAULT_SPEEDS
    spi = spidev.SpiDev()
    spi.open(0, 0)
    try:
        print("%12s | %13s | %9s | %7s" % ("speed, Hz", "bad transfers", "bad bytes", "time, s"))
        for speed in speeds:
            bad_t, bad_b, elapsed = run(spi, speed)
            print("%12d | %13d | %9d | %7.2f" % (speed, bad_t, bad_b, elapsed))
    finally:
        spi.close()


if __name__ == "__main__":
    main()
