"""Тести Pico з дисплеєм (прошивка src/pico/uart_echo_display.py), день 4, крок 2.

Перевіряємо, чи не заважає малювання на дисплеї обміну по UART.
Вимоги, які перевіряємо:
  R1. Луна приходить не пізніше ніж за 100 мс, навіть коли DUT малює.
  R2. Пачка рядків, надісланих без пауз (більше за буфер прийому Pico, 2048 байт),
      повертається повністю.
  R3. Після навантаження DUT коректно відповідає на службову команду.
  R4. Обірваний рядок (без '\n') не склеюється з наступною командою.

Підключення як у test_pico_uart.py. Запуск:
  pytest -v -s src/pi3/test_pico_display.py
У режимі legacy прогін триває кілька хвилин: DUT малює повільно.
"""
import time

import pytest

serial = pytest.importorskip("serial")

PORT = "/dev/serial0"
BAUD = 115200
LATENCY_LIMIT_S = 0.1
BURST_LINES = 12
BURST_LEN = 200  # байт у рядку разом з '\n'; 12 x 200 = 2400 байт > 2048


@pytest.fixture
def port():
    p = serial.Serial(PORT, BAUD, timeout=30)
    p.reset_input_buffer()
    yield p
    p.close()


def test_echo_latency_while_drawing(port):
    """R1: 5 повідомлень з паузою 0,2 с, щоб DUT встигав почати малювати між ними."""
    latencies = []
    wrong = 0
    for i in range(5):
        msg = ("lat-%d\n" % i).encode()
        started = time.time()
        port.write(msg)
        got = port.readline()
        latencies.append(time.time() - started)
        if got != msg:
            wrong += 1
        time.sleep(0.2)
    print("latency, ms: %s" % ", ".join("%.1f" % (x * 1000) for x in latencies))
    assert wrong == 0
    assert max(latencies) < LATENCY_LIMIT_S


def test_burst_bigger_than_rx_buffer(port):
    """R2: 12 рядків по 200 байт одним записом, далі чекаємо всі луни."""
    sent = []
    for i in range(BURST_LINES):
        head = "B%02d-" % i
        sent.append((head + "x" * (BURST_LEN - len(head) - 1) + "\n").encode())
    started = time.time()
    port.write(b"".join(sent))
    received = []
    deadline = started + 300
    while len(received) < BURST_LINES and time.time() < deadline:
        line = port.readline()
        if not line:  # 30 с тиші: далі чекати немає сенсу
            break
        received.append(line)
    elapsed = time.time() - started
    ok = [line for line in received if line in sent]
    missing = [s[:3].decode() for s in sent if s not in received]
    print("sent=%d received=%d ok=%d missing=%s time=%.1f s"
          % (len(sent), len(received), len(ok), missing, elapsed))
    assert len(ok) == BURST_LINES


def test_command_after_load(port):
    """R3: після навантаження DUT відповідає на CMD:STAT."""
    time.sleep(1)
    port.reset_input_buffer()
    port.write(b"CMD:STAT\n")
    reply = port.readline()
    print("reply: %r" % reply)
    assert reply.startswith(b"STAT ")


def test_partial_line_not_glued_to_next_command(port):
    """R4: шматок без '\\n', пауза 0,5 с, потім CMD:PING -> має бути PONG."""
    port.write(b"partial-no-newline")
    time.sleep(0.5)
    port.reset_input_buffer()
    port.write(b"CMD:PING\n")
    reply = port.readline()
    print("reply: %r" % reply)
    assert reply == b"PONG\n"
