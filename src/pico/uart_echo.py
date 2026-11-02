"""Прошивка-луна для Raspberry Pi Pico (MicroPython). День 4, крок 1: без дисплея.

Pico тут пристрій під тестом (DUT), Raspberry Pi 3 тестовий хост.
Кожен рядок, що прийшов по UART (до '\n'), повертається назад без змін.

Службові команди (теж рядком, з '\n' в кінці):
  CMD:PING          -> PONG
  CMD:STAT          -> STAT lines=<N> long=<N> baud=<N>
  CMD:BAUD=<число>  -> OK BAUD=<число>, після чого Pico переходить на нову швидкість
Рядок, довший за MAX_LINE байт, відкидається, у відповідь ERR:LONG.

Підключення (UART0):
  Pico GP0 TX (пін 1)  ->  Pi 3 GPIO15 RXD (пін 10)
  Pico GP1 RX (пін 2)  <-  Pi 3 GPIO14 TXD (пін 8)
  Pico GND   (пін 3)   --  Pi 3 GND (пін 6)
  Живлення: кожна плата від свого USB, 5 В і 3V3 між платами НЕ з'єднувати.

Запуск: у Thonny відкрити файл і натиснути Run (F5). Не зберігати як main.py,
поки старий main.py з проєктом дисплея не збережено в репозиторій.
"""
import time

from machine import UART, Pin

UART_ID = 0
TX_PIN = 0
RX_PIN = 1
BAUD = 115200
MAX_LINE = 256

try:
    led = Pin("LED", Pin.OUT)  # Pico і Pico W з новою MicroPython
except (TypeError, ValueError):
    led = Pin(25, Pin.OUT)  # старі збірки для звичайної Pico


def send(data):
    """Пише в UART усі байти: uart.write() може записати лише частину (див. BUG-004)."""
    mv = memoryview(data)
    off = 0
    while off < len(data):
        off += uart.write(mv[off:]) or 0


def open_uart(baud):
    return UART(UART_ID, baudrate=baud, tx=Pin(TX_PIN), rx=Pin(RX_PIN), rxbuf=2048)


uart = open_uart(BAUD)
baud = BAUD
buf = b""
lines = 0
too_long = 0
skipping = False  # True, поки дочитуємо хвіст задовгого рядка

print("uart_echo: UART%d tx=GP%d rx=GP%d baud=%d" % (UART_ID, TX_PIN, RX_PIN, baud))


def handle(line):
    """Обробка одного повного рядка (з '\\n' в кінці)."""
    global uart, baud, lines
    lines += 1
    led.toggle()
    if not line.startswith(b"CMD:"):
        send(line)
        return
    cmd = line[4:].strip()
    if cmd == b"PING":
        send(b"PONG\n")
    elif cmd == b"STAT":
        send(("STAT lines=%d long=%d baud=%d\n" % (lines, too_long, baud)).encode())
    elif cmd.startswith(b"BAUD="):
        try:
            new = int(cmd[5:])
        except ValueError:
            new = 0
        if not 1200 <= new <= 921600:
            send(b"ERR:BAUD\n")
            return
        send(("OK BAUD=%d\n" % new).encode())
        time.sleep_ms(50)  # даємо відповіді повністю вийти на старій швидкості
        uart = open_uart(new)
        baud = new
        print("baud ->", new)
    else:
        send(b"ERR:CMD\n")


while True:
    n = uart.any()
    if not n:
        continue
    buf += uart.read(n)
    while True:
        i = buf.find(b"\n")
        if i < 0:
            if len(buf) > MAX_LINE:
                buf = b""
                skipping = True
            break
        line = buf[: i + 1]
        buf = buf[i + 1 :]
        if skipping or len(line) > MAX_LINE:
            skipping = False
            too_long += 1
            send(b"ERR:LONG\n")
            continue
        handle(line)
