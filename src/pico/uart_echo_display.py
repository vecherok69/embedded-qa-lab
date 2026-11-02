"""Прошивка-луна з дисплеєм ST7789 для Raspberry Pi Pico (MicroPython). День 4, крок 2.

Протокол UART той самий, що в uart_echo.py (луна рядків, CMD:PING, CMD:STAT,
CMD:BAUD=<число>, ERR:LONG), тому test_pico_uart.py працює і з цією прошивкою.
Додатково DUT показує отримані повідомлення на дисплеї.

Два режими (змінна MODE нижче):
  "legacy" - малювання як у старому проєкті (src/pico/legacy/main.py): SoftSPI 200 кГц,
             по одному пікселю, заливання всього екрана на кожне повідомлення.
             Малювання синхронне: поки малюємо, рядки з UART не обробляються.
             Режим для відтворення дефекту.
  "fast"   - виправлення: луна відправляється одразу, дисплей оновлюється лише тоді,
             коли лінія простоює IDLE_MS мс; апаратний SPI0 і буфер кадру framebuf,
             перемальовується лише смуга з текстом; недописаний рядок, після якого
             LINE_TIMEOUT_MS мс тиші, відкидається (не склеюється з наступним).
Обидва виправлення стосуються BUG-003 (docs/bug-reports/).
Усі відповіді йдуть через send(): дописує байти до кінця і рахує часткові записи
(tx_short у CMD:STAT), див. BUG-004.

Підключення UART (як у кроці 1):
  Pico GP0 TX (пін 1) -> Pi 3 пін 10, Pico GP1 RX (пін 2) <- Pi 3 пін 8, GND пін 3 -- Pi 3 пін 6.
Дисплей (припаяний): GP18 SCK, GP19 MOSI, GP12 RST, GP13 DC, GP14 CS.

Запуск: Thonny -> відкрити файл з ПК -> F5. На плату як main.py не зберігати.
"""
import time

import framebuf
import machine
import ustruct
from machine import UART, Pin

MODE = "fast"  # "legacy" або "fast"

UART_ID = 0
TX_PIN = 0
RX_PIN = 1
BAUD = 115200
MAX_LINE = 256
IDLE_MS = 50  # fast: скільки мс тиші на лінії перед оновленням дисплея
LINE_TIMEOUT_MS = 100  # fast: недописаний рядок без '\n' після стількох мс тиші відкидається
RESYNC = MODE == "fast"  # legacy лишаємо без цього, щоб відтворювати BUG-003 як є
SPI_HZ = 20_000_000  # fast: якщо на екрані сміття, знизити до 10_000_000

W = 240
H = 240
BLACK = 0x0000
WHITE = 0xFFFF
CYAN = 0x07FF
YELLOW = 0xFFE0

# Шрифт 5x7 зі старого проєкту (для режиму legacy)
FONT_BASIC = {
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00], '!': [0x00, 0x00, 0x5f, 0x00, 0x00],
    ',': [0x00, 0x50, 0x30, 0x00, 0x00], '.': [0x00, 0x60, 0x60, 0x00, 0x00],
    '?': [0x00, 0x02, 0x51, 0x05, 0x00],
    '0': [0x3e, 0x51, 0x49, 0x45, 0x3e], '1': [0x00, 0x42, 0x7f, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46], '3': [0x21, 0x41, 0x45, 0x4b, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7f, 0x10], '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3c, 0x4a, 0x49, 0x49, 0x30], '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36], '9': [0x06, 0x49, 0x49, 0x29, 0x1e],
    'A': [0x7e, 0x11, 0x11, 0x11, 0x7e], 'B': [0x7f, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3e, 0x41, 0x41, 0x41, 0x22], 'D': [0x7f, 0x41, 0x41, 0x22, 0x1c],
    'E': [0x7f, 0x49, 0x49, 0x49, 0x41], 'F': [0x7f, 0x09, 0x09, 0x09, 0x01],
    'G': [0x3e, 0x41, 0x49, 0x49, 0x7a], 'H': [0x7f, 0x08, 0x08, 0x08, 0x7f],
    'I': [0x00, 0x41, 0x7f, 0x41, 0x00], 'J': [0x20, 0x40, 0x41, 0x3f, 0x01],
    'K': [0x7f, 0x08, 0x14, 0x22, 0x41], 'L': [0x7f, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7f, 0x02, 0x0c, 0x02, 0x7f], 'N': [0x7f, 0x04, 0x08, 0x10, 0x7f],
    'O': [0x3e, 0x41, 0x41, 0x41, 0x3e], 'P': [0x7f, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3e, 0x41, 0x51, 0x21, 0x5e], 'R': [0x7f, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31], 'T': [0x01, 0x01, 0x7f, 0x01, 0x01],
    'U': [0x3f, 0x40, 0x40, 0x40, 0x3f], 'V': [0x1f, 0x20, 0x40, 0x20, 0x1f],
    'W': [0x3f, 0x40, 0x38, 0x40, 0x3f], 'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x07, 0x08, 0x70, 0x08, 0x07], 'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    'a': [0x20, 0x54, 0x54, 0x54, 0x78], 'b': [0x7f, 0x48, 0x44, 0x44, 0x38],
    'c': [0x38, 0x44, 0x44, 0x44, 0x20], 'd': [0x38, 0x44, 0x44, 0x48, 0x7f],
    'e': [0x38, 0x54, 0x54, 0x54, 0x18], 'f': [0x08, 0x7e, 0x09, 0x01, 0x02],
    'g': [0x0c, 0x52, 0x52, 0x52, 0x3e], 'h': [0x7f, 0x08, 0x04, 0x04, 0x78],
    'i': [0x00, 0x44, 0x7d, 0x40, 0x00], 'j': [0x20, 0x40, 0x44, 0x3d, 0x00],
    'k': [0x7f, 0x10, 0x28, 0x44, 0x00], 'l': [0x00, 0x41, 0x7f, 0x40, 0x00],
    'm': [0x7c, 0x04, 0x18, 0x04, 0x78], 'n': [0x7c, 0x08, 0x04, 0x04, 0x78],
    'o': [0x38, 0x44, 0x44, 0x44, 0x38], 'p': [0x7c, 0x14, 0x14, 0x14, 0x08],
    'q': [0x08, 0x14, 0x14, 0x14, 0x7c], 'r': [0x7c, 0x08, 0x04, 0x04, 0x08],
    's': [0x24, 0x54, 0x54, 0x54, 0x48], 't': [0x04, 0x3f, 0x44, 0x40, 0x20],
    'u': [0x3c, 0x40, 0x40, 0x20, 0x7c], 'v': [0x1c, 0x20, 0x40, 0x20, 0x1c],
    'w': [0x3c, 0x40, 0x30, 0x40, 0x3c], 'x': [0x44, 0x28, 0x10, 0x28, 0x44],
    'y': [0x0c, 0x50, 0x50, 0x50, 0x3c], 'z': [0x44, 0x64, 0x54, 0x4c, 0x44]
}

# ============================================================================
# Драйвер ST7789 (з src/pico/legacy/main.py, без змін у логіці)
# ============================================================================
class ST7789:
    def __init__(self, spi, reset, cs, dc):
        self.spi = spi
        self.reset = reset
        self.cs = cs
        self.dc = dc
        self.hard_reset()
        self.init_display()

    def write_cmd(self, cmd):
        self.dc.off(); self.cs.off(); self.spi.write(bytearray([cmd])); self.cs.on()

    def write_data(self, data):
        self.dc.on(); self.cs.off(); self.spi.write(data); self.cs.on()

    def hard_reset(self):
        self.reset.on(); time.sleep_ms(50)
        self.reset.off(); time.sleep_ms(50)
        self.reset.on(); time.sleep_ms(150)

    def init_display(self):
        self.write_cmd(0x01); time.sleep_ms(150)  # Software reset
        self.write_cmd(0x11); time.sleep_ms(120)  # Sleep out
        self.write_cmd(0x3A); self.write_data(bytearray([0x55]))  # 16 біт на піксель
        self.write_cmd(0x36); self.write_data(bytearray([0x00]))  # MADCTL
        self.write_cmd(0x2A); self.write_data(bytearray([0x00, 0x00, 0x00, 0xEF]))
        self.write_cmd(0x2B); self.write_data(bytearray([0x00, 0x00, 0x00, 0xEF]))
        self.write_cmd(0x21); self.write_cmd(0x13); self.write_cmd(0x29); time.sleep_ms(100)

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A); self.write_data(ustruct.pack(">HH", x0, x1))
        self.write_cmd(0x2B); self.write_data(ustruct.pack(">HH", y0, y1))
        self.write_cmd(0x2C)

    def fill(self, color):
        self.set_window(0, 0, W - 1, H - 1)
        self.dc.on(); self.cs.off()
        row = ustruct.pack(">H", color) * W
        for _ in range(H):
            self.spi.write(row)
        self.cs.on()

    # --- повільний шлях legacy: по одному пікселю ---
    def draw_pixel(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            self.set_window(x, y, x, y)
            self.write_data(ustruct.pack(">H", color))

    def draw_char(self, x, y, char, color):
        bitmap = FONT_BASIC.get(char, FONT_BASIC[" "])
        for column in range(5):
            byte = bitmap[column]
            for row in range(8):
                if byte & (1 << row):
                    self.draw_pixel(x + column, y + row, color)

    def draw_string(self, x, y, string, color):
        for char in string:
            self.draw_char(x, y, char, color)
            x += 6

    # --- швидкий шлях fast: цілий прямокутник одним записом ---
    def blit(self, x, y, w, h, buf):
        self.set_window(x, y, x + w - 1, y + h - 1)
        self.write_data(buf)


def swap565(c):
    """framebuf зберігає RGB565 little-endian, ST7789 чекає big-endian."""
    return ((c & 0xFF) << 8) | (c >> 8)


rst = Pin(12, Pin.OUT)
cs = Pin(14, Pin.OUT)
dc = Pin(13, Pin.OUT)
if MODE == "legacy":
    spi = machine.SoftSPI(baudrate=200000, polarity=1, phase=0,
                          sck=Pin(18), mosi=Pin(19), miso=Pin(16))
else:
    spi = machine.SPI(0, baudrate=SPI_HZ, polarity=1, phase=0, sck=Pin(18), mosi=Pin(19))
display = ST7789(spi, rst, cs, dc)
time.sleep_ms(50)
display.write_cmd(0x22)  # як у старому main.py

BAND_H = 40  # fast: смуга з текстом, 240 x 40 пікселів
band_buf = bytearray(W * BAND_H * 2)
band = framebuf.FrameBuffer(band_buf, W, BAND_H, framebuf.RGB565)

t0 = time.ticks_ms()
display.fill(BLACK)
print("fill(BLACK): %d ms" % time.ticks_diff(time.ticks_ms(), t0))
if MODE == "legacy":
    display.draw_string(10, 100, "UART echo: legacy", CYAN)
else:
    band.fill(0)
    band.text("UART echo: fast", 4, 16, swap565(CYAN))
    display.blit(0, 100, W, BAND_H, band_buf)

# ============================================================================
# Малювання повідомлення
# ============================================================================
draws = 0
draw_ms_last = 0
draw_ms_max = 0


def to_text(raw):
    """Лише друковані ASCII, решта -> '?'. decode() на довільних байтах може впасти."""
    return "".join(chr(b) if 32 <= b < 127 else "?" for b in raw)


def draw_message(n, raw):
    global draws, draw_ms_last, draw_ms_max
    t0 = time.ticks_ms()
    text = to_text(raw)
    if MODE == "legacy":
        # Як у старому проєкті: чистимо весь екран і пишемо до 4 рядків по 20 символів
        display.fill(BLACK)
        for k in range(4):
            display.draw_string(10, 30 + 35 * k, text[20 * k: 20 * (k + 1)], WHITE)
    else:
        band.fill(0)
        band.text("RX #%d" % n, 4, 4, swap565(YELLOW))
        band.text(text[:29], 4, 20, swap565(WHITE))
        display.blit(0, 100, W, BAND_H, band_buf)
    draw_ms_last = time.ticks_diff(time.ticks_ms(), t0)
    draw_ms_max = max(draw_ms_max, draw_ms_last)
    draws += 1
    print("draw #%d: %d ms" % (n, draw_ms_last))


# ============================================================================
# UART
# ============================================================================
try:
    led = Pin("LED", Pin.OUT)
except (TypeError, ValueError):
    led = Pin(25, Pin.OUT)


tx_short = 0  # скільки разів uart.write() записав менше, ніж просили (BUG-004)


def send(data):
    """Пише в UART усі байти. uart.write() на RP2040 при заповненому буфері передавання
    може записати лише частину і повернути меншу кількість (або None). Без циклу
    решта мовчки губиться."""
    global tx_short
    mv = memoryview(data)
    off = 0
    while off < len(data):
        n = uart.write(mv[off:]) or 0
        if n < len(data) - off:
            tx_short += 1
        off += n


def open_uart(baud):
    return UART(UART_ID, baudrate=baud, tx=Pin(TX_PIN), rx=Pin(RX_PIN), rxbuf=2048)


uart = open_uart(BAUD)
baud = BAUD
buf = b""
lines = 0
too_long = 0
skipping = False
stale = 0  # скільки недописаних рядків відкинуто за тайм-аутом
pending = None  # fast: останній рядок, який ще не показано
last_rx = time.ticks_ms()

print("uart_echo_display: MODE=%s UART%d tx=GP%d rx=GP%d baud=%d"
      % (MODE, UART_ID, TX_PIN, RX_PIN, baud))


def handle(line):
    global uart, baud, lines, pending
    lines += 1
    led.toggle()
    if not line.startswith(b"CMD:"):
        send(line)  # луна завжди першою, до будь-якого малювання
        raw = line.strip()
        if MODE == "legacy":
            draw_message(lines, raw)  # синхронно: поки малюємо, UART ніхто не читає
        else:
            pending = (lines, raw)
        return
    cmd = line[4:].strip()
    if cmd == b"PING":
        send(b"PONG\n")
    elif cmd == b"STAT":
        send(("STAT lines=%d long=%d stale=%d tx_short=%d baud=%d mode=%s draws=%d draw_ms_last=%d draw_ms_max=%d\n"
                    % (lines, too_long, stale, tx_short, baud, MODE, draws, draw_ms_last, draw_ms_max)).encode())
    elif cmd.startswith(b"BAUD="):
        try:
            new = int(cmd[5:])
        except ValueError:
            new = 0
        if not 1200 <= new <= 921600:
            send(b"ERR:BAUD\n")
            return
        send(("OK BAUD=%d\n" % new).encode())
        time.sleep_ms(50)
        uart = open_uart(new)
        baud = new
        print("baud ->", new)
    else:
        send(b"ERR:CMD\n")


while True:
    n = uart.any()
    if n:
        last_rx = time.ticks_ms()
        buf += uart.read(n)
        while True:
            i = buf.find(b"\n")
            if i < 0:
                if len(buf) > MAX_LINE:
                    buf = b""
                    skipping = True
                break
            line = buf[: i + 1]
            buf = buf[i + 1:]
            if skipping or len(line) > MAX_LINE:
                skipping = False
                too_long += 1
                send(b"ERR:LONG\n")
                continue
            handle(line)
    elif RESYNC and buf and time.ticks_diff(time.ticks_ms(), last_rx) > LINE_TIMEOUT_MS:
        print("stale: відкинуто %d байт без '\\n'" % len(buf))
        buf = b""
        skipping = False
        stale += 1
    elif pending and time.ticks_diff(time.ticks_ms(), last_rx) > IDLE_MS:
        draw_message(*pending)
        pending = None
