import sys
import machine
import time
import ustruct
import select

# ============================================================================
# 1. ПОВНИЙ ШРИФТ 5x7 (Всі англійські літери, цифри та знаки)
# ============================================================================
FONT_BASIC = {
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00], '!': [0x00, 0x00, 0x5f, 0x00, 0x00],
    ',': [0x00, 0x50, 0x30, 0x00, 0x00], '.': [0x00, 0x60, 0x60, 0x00, 0x00],
    '?': [0x00, 0x02, 0x51, 0x05, 0x00],
    
    # Цифри
    '0': [0x3e, 0x51, 0x49, 0x45, 0x3e], '1': [0x00, 0x42, 0x7f, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46], '3': [0x21, 0x41, 0x45, 0x4b, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7f, 0x10], '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3c, 0x4a, 0x49, 0x49, 0x30], '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36], '9': [0x06, 0x49, 0x49, 0x29, 0x1e],

    # ВЕЛИКІ ЛІТЕРИ
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

    # маленькі літери
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

BLACK = 0x0000
WHITE = 0xFFFF
CYAN = 0x07FF

# ============================================================================
# 2. КЛАС ДРАЙВЕРА ST7789
# ============================================================================
class ST7789:
    def __init__(self, spi, width, height, reset, cs, dc):
        self.spi = spi
        self.width = width
        self.height = height
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
        self.write_cmd(0x01); time.sleep_ms(150) # Reset
        self.write_cmd(0x11); time.sleep_ms(120) # Sleep Out
        self.write_cmd(0x3A); self.write_data(bytearray([0x55])) # 16-bit color
        self.write_cmd(0x36); self.write_data(bytearray([0x00])) # MADCTL
        self.write_cmd(0x2A); self.write_data(bytearray([0x00, 0x00, 0x00, 0xEF]))
        self.write_cmd(0x2B); self.write_data(bytearray([0x00, 0x00, 0x00, 0xEF]))
        self.write_cmd(0x21); self.write_cmd(0x13); self.write_cmd(0x29); time.sleep_ms(100)

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A); self.write_data(ustruct.pack(">HH", x0, x1))
        self.write_cmd(0x2B); self.write_data(ustruct.pack(">HH", y0, y1))
        self.write_cmd(0x2C)

    def fill(self, color):
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.dc.on(); self.cs.off()
        buffer = ustruct.pack(">H", color) * self.height
        for _ in range(self.width): self.spi.write(buffer)
        self.cs.on()

    def draw_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.set_window(x, y, x, y)
            self.write_data(ustruct.pack(">H", color))

    def draw_char(self, x, y, char, color, size=1):
        if char not in FONT_BASIC: char = ' '
        bitmap = FONT_BASIC[char]
        for column in range(5):
            byte = bitmap[column]
            for row in range(8):
                if byte & (1 << row):
                    for px in range(size):
                        for py in range(size):
                            self.draw_pixel(x + column * size + px, y + row * size + py, color)

    def draw_string(self, x, y, string, color, size=1):
        current_x = x
        for char in string:
            self.draw_char(current_x, y, char, color, size)
            current_x += 6 * size

# ============================================================================
# 3. ІНІЦІАЛІЗАЦІЯ ЗАЛІЗА (ОПТИМІЗОВАНИЙ SOFTSPI)
# ============================================================================
rst_pin = machine.Pin(12, machine.Pin.OUT, machine.Pin.PULL_UP)
cs_pin = machine.Pin(14, machine.Pin.OUT, machine.Pin.PULL_UP)
dc_pin = machine.Pin(13, machine.Pin.OUT, machine.Pin.PULL_UP)

# Швидкість знижено до 200 кГц для стабільності та чітких сигналів
spi = machine.SoftSPI(
    baudrate=200000, polarity=1, phase=0,
    sck=machine.Pin(18), mosi=machine.Pin(19), miso=machine.Pin(16)
)

display = ST7789(spi, width=240, height=240, reset=rst_pin, cs=cs_pin, dc=dc_pin)
time.sleep_ms(50) # Короткий таймаут перед першою командою виведення даних
display.write_cmd(0x22)

# Чисте фарбування в чорний
display.fill(BLACK)
display.draw_string(15, 100, "Waiting PC...", CYAN, size=2)

# ============================================================================
# 4. ГОЛОВНИЙ ЦИКЛ: ПРИЙОМ ДАНИХ
# ============================================================================
buffer = ""
while True:
    if select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.read(1)
        
        if char == '\n' or char == '\r':
            line = buffer.strip()
            
            if len(line) > 0:
                display.fill(BLACK)
                row_height = 35 
                
                # Розбиваємо рядок до 80 символів на 4 частини
                display.draw_string(10, 30, line[0:20], WHITE, size=1)
                display.draw_string(10, 30 + row_height, line[20:40], WHITE, size=1)
                display.draw_string(10, 30 + row_height*2, line[40:60], WHITE, size=1)
                display.draw_string(10, 30 + row_height*3, line[60:80], WHITE, size=1)
                
                buffer = "" 
        else:
            buffer += char
            if len(buffer) > 120:
                buffer = ""
                
    time.sleep_ms(5)