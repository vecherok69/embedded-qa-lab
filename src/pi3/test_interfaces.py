"""Апаратні тести інтерфейсів Raspberry Pi 3 (pytest).

СТАТУС: написано заздалегідь, на залізі ще не запускалося.

Потрібні перемички (Dupont, мама-мама):
  UART loopback: GPIO14 TX (пин 8)  <->  GPIO15 RX (пин 10)
  SPI loopback:  GPIO10 MOSI (пин 19) <-> GPIO9 MISO (пин 21)
  GPIO:          GPIO17 (пин 11)    <->  GPIO27 (пин 13)

Встановлення: bash scripts/pi3/setup.sh
Запуск:       pytest -v -s src/pi3/test_interfaces.py
"""
import time

import pytest


def test_uart_loopback():
    serial = pytest.importorskip("serial")
    port = serial.Serial("/dev/serial0", 115200, timeout=1)
    try:
        port.reset_input_buffer()
        port.write(b"hello\n")
        assert port.readline() == b"hello\n"
    finally:
        port.close()


def test_uart_loopback_soak():
    """1000 повідомлень поспіль: рахуємо втрати."""
    serial = pytest.importorskip("serial")
    port = serial.Serial("/dev/serial0", 115200, timeout=1)
    lost = 0
    started = time.time()
    try:
        for i in range(1000):
            msg = ("msg-%04d\n" % i).encode()
            port.write(msg)
            if port.readline() != msg:
                lost += 1
    finally:
        port.close()
    print("lost=%d of 1000, time=%.2f s" % (lost, time.time() - started))
    assert lost == 0


def test_spi_loopback():
    spidev = pytest.importorskip("spidev")
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 500000
    try:
        data = [0x01, 0x02, 0xAA]
        assert spi.xfer2(list(data)) == data
    finally:
        spi.close()


def test_gpio_level_through_jumper():
    gpiozero = pytest.importorskip("gpiozero")
    out = gpiozero.OutputDevice(17)
    inp = gpiozero.InputDevice(27, pull_up=False)
    try:
        out.on()
        time.sleep(0.05)
        assert inp.value == 1
        out.off()
        time.sleep(0.05)
        assert inp.value == 0
    finally:
        out.close()
        inp.close()
