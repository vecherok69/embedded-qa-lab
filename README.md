# embedded-qa-lab

Власний стенд для тестування embedded-пристроїв: Raspberry Pi 3 як тестовий хост, Raspberry Pi Pico з дисплеєм як пристрій під тестом (DUT), мультиметр і автотести на `pytest`. Мета — показати, як я тестую залізо: від заміру напруги на піні до знаходження й доведення дефекту в прошивці.

Я QA-інженер з досвідом інтеграційного тестування платіжних систем (протоколи, логи, зовнішні провайдери). Цей репозиторій — мій перехід до embedded: усе зібрано, виміряно й задокументовано власноруч.

## Головне за 30 секунд

- **4 баг-репорти**, з них 2 знайдено у взаємодії двох плат по UART і доведено до першопричини.
- **BUG-003 → BUG-004:** виправлення одного дефекту (дисплей блокував UART) відкрило другий, прихований: прошивка ігнорувала частковий `uart.write()`. Нестабільний тест не перезапускав «до зеленого», а прогнав серією (7 з 30 failed) і по лічильниках драйвера на обох кінцях показав, що байти губить передавач DUT. Після виправлення — 30 з 30.
- **Перевірені гіпотези:** дві мої власні гіпотези (тайм-аут FIFO у PL011, розбіжність тактів UART між платами) спростовано вимірюванням і розрахунком, а не прийнято на віру.
- **Регресія одним скриптом:** `run_all_tests.sh` фіксує стан стенда до/після, пише лог і JUnit XML.

## Дефекти

| ID | Що знайдено | Як доведено | Severity | Статус |
| --- | --- | --- | --- | --- |
| [BUG-001](docs/bug-reports/BUG-001-i2c-wrong-address-crash.md) | Прошивка падає з необробленим `OSError`, якщо адреса I2C у коді не збігається з реальною | трейс PulseView: `Address write: 69` + NACK, `scan` показує 0x68 | Major | відкритий |
| [BUG-002](docs/bug-reports/BUG-002-pi3-undervoltage-pc-usb.md) | Pi 3 працює в undervoltage від USB-порту ПК, хоча мережа й SSH працюють | `get_throttled` `0x50005` → `0x0` після заміни блока, підтверджено мультиметром | Major | закрито |
| [BUG-003](docs/bug-reports/BUG-003-pico-display-blocks-uart-data-loss.md) | Поки Pico малює на дисплеї, UART не обслуговується: луна 5,5 с, втрата даних, склеювання команд | прийнято рівно 2080 байт = 2048 буфер + 32 FIFO, решта мовчки відкинута | Critical | закрито |
| [BUG-004](docs/bug-reports/BUG-004-pico-uart-write-partial-tx-loss.md) | `uart.write()` на Pico записує не всі байти, прошивка цього не перевіряє | серія 30 прогонів; на Pi `tx` +72000, `rx` +71880, `oe` немає → втрата на передавачі DUT | Major | закрито |

Шаблон баг-репорту з полями для заліза (ревізія плати, прошивка, живлення, прилади, відтворюваність): [TEMPLATE.md](docs/bug-reports/TEMPLATE.md).

## Що перевірено

| Область | Результат | Деталі |
| --- | --- | --- |
| Живлення | 5,00 / 4,98 В і 3,29 / 3,30 В у простої, 4,91 В під навантаженням; розібрано прапорці `get_throttled` | [day1-power-gpio.md](docs/measurements/day1-power-gpio.md) |
| GPIO | вихід 3,3 / 0 В збігається з `pinctrl`; вхід без підтяжки «плаває» ≈ 50/50; PWM 25–100 % → 0,85–3,30 В | [day1-power-gpio.md](docs/measurements/day1-power-gpio.md) |
| UART loopback | mini-UART і PL011: 0 втрат на 1000 повідомлень, у спокої й під навантаженням, до 921600 бод | [day2-uart-spi-i2c.md](docs/measurements/day2-uart-spi-i2c.md) |
| SPI loopback | 0 пошкоджених байт до 62,5 МГц (з обґрунтуванням, чому це ще не гарантія для реального пристрою) | [day2-uart-spi-i2c.md](docs/measurements/day2-uart-spi-i2c.md) |
| I2C (Wokwi) | сканування з NACK, WHO_AM_I = 0x68, негативні кейси: хибна адреса, SDA/SCL навпаки | [i2c-traces.md](docs/notes/i2c-traces.md), [wokwi-closeout.md](docs/wokwi-closeout.md) |
| Pi 3 ↔ Pico | протокол прошивки, негативні тести, швидкості до 921600, вимоги R1–R4 до прошивки з дисплеєм | [day4-pico-uart.md](docs/measurements/day4-pico-uart.md) |

Повний перелік кейсів зі статусами, критеріями і обмеженнями: **[тест-план](docs/test-plan.md)**.

## Як я працюю

- **Спершу методика, потім дефект.** Тричі результат не збігся з очікуванням, і тричі причина була в методиці: міряв не той пін, поганий контакт щупа, кабель USB лише для заряджання. Жоден не став хибним баг-репортом.
- **Незалежний прилад.** Програмний стан перевіряю приладом (`pinctrl` і мультиметр, `get_throttled` і мультиметр), втрату даних — лічильниками на обох кінцях лінії.
- **Нестабільний тест — це дані.** Серія прогонів і частота відмов замість перезапуску до «зеленого».
- **Знаю межі своїх інструментів.** Від 460800 бод Python-цикл запит-відповідь вимірює швидкість скрипта, а не UART; SPI loopback не проводить SCLK через дріт. Це записано в тест-плані як обмеження.

## Стенд

| Що | Значення |
| --- | --- |
| Хост | Raspberry Pi 3 Model B+ Rev 1.3, Raspberry Pi OS Lite 64-bit, Python 3.13, pytest 8.3 |
| DUT | Raspberry Pi Pico + TFT 1,54″ ST7789 (SPI), MicroPython |
| Прилади | мультиметр ANENG SZ08, `vcgencmd`, `pinctrl`, `/proc/tty/driver/serial`, Thonny |
| Симулятор | Wokwi (Pico + MPU6050 + логічний аналізатор), PulseView |

## Структура

```
docs/
  test-plan.md                      тест-план: обсяг, кейси, критерії, ризики, регресія
  measurements/day1-power-gpio.md   живлення та GPIO на Pi 3
  measurements/day2-uart-spi-i2c.md UART/SPI/I2C loopback, mini-UART проти PL011
  measurements/day4-pico-uart.md    UART Pi 3 ↔ Pico, дисплей, R1–R4
  bug-reports/                      BUG-001…BUG-004 і шаблон
  notes/i2c-traces.md               розбір трейсів I2C у PulseView
  wokwi-closeout.md                 підсумок роботи в симуляторі
  interview/star-stories.md         історії для співбесіди (STAR)
  screenshots/                      докази: термінали, трейси, заміри
scripts/pi3/
  setup.sh                          пакети + увімкнення SPI, I2C, UART
  collect_logs.sh                   знімок діагностики стенда
  run_all_tests.sh                  регресійний прогін з логами і JUnit XML
src/
  pi3/                              pytest-тести і скрипти прогону швидкостей (хост)
  pico/uart_echo.py                 прошивка DUT: луна + службові команди
  pico/uart_echo_display.py         прошивка DUT з дисплеєм (режими legacy і fast)
  pico/legacy/                      старий проєкт дисплея, з якого відтворено BUG-003
  wokwi/                            код для симулятора
logs/                               логи прогонів
```

## Швидкий старт на Raspberry Pi 3

Живлення тільки від окремого блока 5 В від 2,5 А: від USB-порту ПК плата йде в undervoltage (BUG-002). Перша команда після входу по SSH: `vcgencmd get_throttled`, очікувано `0x0`.

```bash
sudo apt install -y git   # у Raspberry Pi OS Lite git немає з коробки
git clone https://github.com/vecherok69/embedded-qa-lab && cd embedded-qa-lab
bash scripts/pi3/setup.sh && sudo reboot

# фаза 1: перемички 8↔10, 19↔21, 11↔13, Pico не підключено
bash scripts/pi3/run_all_tests.sh loopback
# фаза 2: зняти 8↔10, підключити Pico, запустити на ньому src/pico/uart_echo_display.py
bash scripts/pi3/run_all_tests.sh pico
```

Схеми комутації — у [тест-плані](docs/test-plan.md#3-стенд).

## Що далі

- Логічний аналізатор: побачити реальну форму UART/SPI і фактичну частоту SPI.
- I2C з реальним датчиком (I2C-02) і TC-08 «немає живлення» на залізі.
- Потоковий тест пропускної здатності UART замість запит-відповідь.
