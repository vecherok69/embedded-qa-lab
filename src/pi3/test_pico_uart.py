"""Тести UART між Raspberry Pi 3 (тестовий хост) і Pico (DUT, прошивка src/pico/uart_echo.py).

Підключення:
  Pi 3 пін 8  (GPIO14 TXD)  ->  Pico пін 2 (GP1 RX)
  Pi 3 пін 10 (GPIO15 RXD)  <-  Pico пін 1 (GP0 TX)
  Pi 3 пін 6  (GND)         --  Pico пін 3 (GND)
Перемичку loopback (пін 8 <-> пін 10) зняти.

Запуск:  pytest -v -s src/pi3/test_pico_uart.py
Порт /dev/serial0 (зараз ttyS0, mini-UART).

Важливо: у loopback передавач і приймач Pi працюють від одного тактового сигналу,
тому похибка швидкості не видна. З Pico такти різні, і похибка mini-UART
(залежить від частоти ядра) може проявитися на високих швидкостях.
"""
import time

import pytest

serial = pytest.importorskip("serial")

PORT = "/dev/serial0"
BASE_BAUD = 115200


def open_port(baud=BASE_BAUD):
    port = serial.Serial(PORT, baud, timeout=1)
    port.reset_input_buffer()
    return port


def ask(port, payload):
    port.write(payload)
    return port.readline()


@pytest.fixture
def port():
    p = open_port()
    yield p
    p.close()


def test_ping(port):
    assert ask(port, b"CMD:PING\n") == b"PONG\n"


def test_echo_hello(port):
    assert ask(port, b"hello\n") == b"hello\n"


def test_echo_soak_1000(port):
    lost = corrupted = 0
    started = time.time()
    for i in range(1000):
        msg = ("msg-%04d\n" % i).encode()
        got = ask(port, msg)
        if got != msg:
            lost += 1
            if got:
                corrupted += 1
    print("lost=%d corrupted=%d of 1000, time=%.2f s" % (lost, corrupted, time.time() - started))
    assert lost == 0


def test_echo_all_byte_values(port):
    """Усі значення 0x00..0xFF, крім 0x0A (кінець рядка): дані мають повернутися без змін."""
    payload = bytes(b for b in range(256) if b != 0x0A) + b"\n"
    assert ask(port, payload) == payload


def test_too_long_line_rejected_and_recovers(port):
    """Негативний тест: 300 байт без '\\n' у межах ліміту -> ERR:LONG, після цього DUT живий."""
    assert ask(port, b"A" * 300 + b"\n") == b"ERR:LONG\n"
    assert ask(port, b"CMD:PING\n") == b"PONG\n"


def test_unknown_command(port):
    assert ask(port, b"CMD:FOO\n") == b"ERR:CMD\n"


def test_invalid_baud_rejected(port):
    assert ask(port, b"CMD:BAUD=abc\n") == b"ERR:BAUD\n"
    assert ask(port, b"CMD:BAUD=5000000\n") == b"ERR:BAUD\n"


@pytest.mark.parametrize("baud", [115200, 230400, 460800, 921600])
def test_baud_sweep(baud):
    """Перемикаємо Pico на нову швидкість, 200 повідомлень, повертаємо 115200."""
    p = open_port()
    try:
        assert ask(p, b"CMD:BAUD=%d\n" % baud) == b"OK BAUD=%d\n" % baud
    finally:
        p.close()
    time.sleep(0.1)
    p = open_port(baud)
    lost = 0
    try:
        for i in range(200):
            msg = ("b%d-%03d\n" % (baud, i)).encode()
            if ask(p, msg) != msg:
                lost += 1
        print("baud=%d lost=%d of 200" % (baud, lost))
    finally:
        # Повертаємо DUT на базову швидкість, навіть якщо тест упав
        p.write(b"CMD:BAUD=%d\n" % BASE_BAUD)
        p.readline()
        p.close()
        time.sleep(0.1)
    assert lost == 0
