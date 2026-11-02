import time
import ustruct
import time

# Константи кольорів
BLACK = 0x0000
BLUE = 0x001F
RED = 0xF800
GREEN = 0x07E0
CYAN = 0x07FF
MAGENTA = 0xF81F
YELLOW = 0xFFE0
WHITE = 0xFFFF

class ST7789:
    def __init__(self, spi, width, height, reset, cs, dc, rotation=0):
        self.spi = spi
        self.width = width
        self.height = height
        self.reset = reset
        self.cs = cs
        self.dc = dc
        self.rotation = rotation
        self.hard_reset()
        self.init()

    def write_cmd(self, cmd):
        self.dc.off()
        self.cs.off()
        self.spi.write(bytearray([cmd]))
        self.cs.on()

    def write_data(self, data):
        self.dc.on()
        self.cs.off()
        self.spi.write(data)
        self.cs.on()

    def hard_reset(self):
        self.reset.on()
        time.sleep_ms(50)
        self.reset.off()
        time.sleep_ms(50)
        self.reset.on()
        time.sleep_ms(150)

    def init(self):
        self.write_cmd(0x11) # Sleep out
        time.sleep_ms(120)
        self.write_cmd(0x3A) # Interface pixel format
        self.write_data(bytearray([0x55])) # 16-bit/pixel
        self.write_cmd(0x36) # Memory Data Access Control
        self.write_data(bytearray([0x00]))
        self.write_cmd(0x2A) # Column Address Set
        self.write_data(bytearray([0x00, 0x00, 0x00, 0xEF]))
        self.write_cmd(0x2B) # Row Address Set
        self.write_data(bytearray([0x00, 0x00, 0x00, 0xEF]))
        self.write_cmd(0x21) # Display Inversion On
        self.write_cmd(0x13) # Normal Display Mode On
        self.write_cmd(0x29) # Display On
        time.sleep_ms(50)

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A)
        self.write_0b = ustruct.pack(">HH", x0, x1)
        self.write_data(self.write_0b)
        self.write_cmd(0x2B)
        self.write_1b = ustruct.pack(">HH", y0, y1)
        self.write_data(self.write_1b)
        self.write_cmd(0x2C)

    def fill(self, color):
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.dc.on()
        self.cs.off()
        # Малюємо блоками для швидкості
        buffer = ustruct.pack(">H", color) * 240
        for _ in range(self.width):
            self.spi.write(buffer)
        self.cs.on()