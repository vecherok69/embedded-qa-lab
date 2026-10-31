# embedded-qa-lab

Навчальна лабораторія з тестування embedded-пристроїв: інтерфейси (UART, SPI, I2C), живлення, логи, прошивка, баг-репорти. Усе зроблено з нуля, щоб показати, як я підходжу до тестування заліза.

## Стенди

| Стенд | Що перевіряється | Статус |
| --- | --- | --- |
| Raspberry Pi Pico + MPU6050 + логічний аналізатор (симулятор Wokwi) | I2C: сканування, WHO_AM_I, читання регістрів, негативні сценарії | завершено (з обмеженнями симулятора: електричні ефекти та UART перевіряються на Raspberry Pi 3) |
| Raspberry Pi 3 + мультиметр + перемички | живлення, GPIO, pull-up, PWM, UART/SPI loopback, автотести на pytest | заплановано |

## Структура

```
docs/
  test-plan.md                     тест-план для I2C-стенду (Wokwi)
  notes/i2c-traces.md              розбір трейсів PulseView
  measurements/day1-power-gpio.md  заміри живлення та GPIO на Pi 3
  measurements/day2-uart-spi-i2c.md  UART/SPI/I2C loopback, до/після disable-bt
  bug-reports/TEMPLATE.md          шаблон баг-репорту для заліза
  bug-reports/BUG-001-...md        перший баг-репорт (хибна адреса I2C)
  wokwi-closeout.md                підсумок роботи у Wokwi, вправа 6
  interview/star-stories.md        історії для співбесіди (STAR)
  screenshots/                     трейси та осцилограми
scripts/pi3/
  setup.sh                         пакети + увімкнення SPI, I2C, UART
  collect_logs.sh                  знімок діагностики стенда в logs/
src/
  wokwi/                           код для Pico (MicroPython)
  pi3/test_interfaces.py           pytest-тести для Raspberry Pi 3
logs/                              логи прогонів (у git не потрапляють)
STATE.md                           поточний стан підготовки
```

## Швидкий старт на Raspberry Pi 3

```bash
git clone https://github.com/vecherok69/embedded-qa-lab && cd embedded-qa-lab
bash scripts/pi3/setup.sh && sudo reboot
# після перезавантаження, з перемичками (див. docstring у test_interfaces.py):
pytest -v -s src/pi3/test_interfaces.py
bash scripts/pi3/collect_logs.sh baseline
```

## Що вже є

- Розібрано два I2C-трейси: сканування шини з NACK на відсутніх адресах і читання WHO_AM_I (0x68) з повторним Start. Деталі в [docs/notes/i2c-traces.md](docs/notes/i2c-traces.md).
- Тест-план для MPU6050 з кейсами, статусами та доказами: [docs/test-plan.md](docs/test-plan.md).
- Перший баг-репорт BUG-001 і негативні тести TC-07, TC-08, TC-11: [docs/bug-reports/](docs/bug-reports/), [docs/wokwi-closeout.md](docs/wokwi-closeout.md).
- Шаблон баг-репорту з полями для залізних дефектів: версія прошивки, ревізія плати, живлення, прилади, докази.

## Що буде далі

- Негативні сценарії на I2C (неправильна адреса, SDA/SCL навпаки, немає живлення) з баг-репортами.
- Вимірювання на Raspberry Pi 3: живлення під навантаженням, GPIO, PWM, UART до/після `dtoverlay=disable-bt`.
- Автотести `pytest` для UART, SPI і GPIO.
