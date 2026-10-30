# День 2: UART, SPI, I2C на Raspberry Pi 3

## UART loopback (пін 8 TX ↔ пін 10 RX)

На Pi 3 Bluetooth займає повноцінний PL011, а на піни 8/10 за замовчуванням виведено mini-UART, частота якого прив'язана до частоти ядра. Експеримент: порівняти втрати до і після `dtoverlay=disable-bt`.

| Прогін | config.txt | `ls -l /dev/serial0` → | Швидкість | Повідомлень | Втрачено | Час, с | Лог |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UART-01 | за замовчуванням | ttyS0 (mini-UART) | 115200 | 1000 | | | |
| UART-02 | за замовчуванням, під навантаженням CPU | ttyS0 | 115200 | 1000 | | | |
| UART-03 | `dtoverlay=disable-bt` | ttyAMA0 (PL011) | 115200 | 1000 | | | |
| UART-04 | `dtoverlay=disable-bt`, під навантаженням CPU | ttyAMA0 | 115200 | 1000 | | | |

Запуск: `pytest -v -s src/pi3/test_interfaces.py -k uart`. Логи до/після: `bash scripts/pi3/collect_logs.sh before-disable-bt` і `... after-disable-bt`.

Висновок:

## SPI loopback (пін 19 MOSI ↔ пін 21 MISO)

| ID | Перевірка | Очікувано | Факт |
| --- | --- | --- | --- |
| SPI-01 | `xfer2([0x01, 0x02, 0xAA])` з перемичкою | ті самі байти | |
| SPI-02 | Без перемички | `0x00` або `0xFF`, не вхідні дані | |

## I2C

| ID | Перевірка | Очікувано | Факт |
| --- | --- | --- | --- |
| I2C-01 | `i2cdetect -y 1` без пристроїв | порожня таблиця | |
| I2C-02 | `i2cdetect -y 1` з датчиком (якщо куплено) | адреса датчика (0x68 MPU6050, 0x76/0x77 BME280) | |

## Знахідки

Розбіжності — у [баг-репорти](../bug-reports/TEMPLATE.md).
