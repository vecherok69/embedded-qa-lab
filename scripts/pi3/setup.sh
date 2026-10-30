#!/usr/bin/env bash
# День 1: підготовка Raspberry Pi 3 до тестів.
# Запуск на Pi:  bash scripts/pi3/setup.sh   (потім sudo reboot)
set -euo pipefail

echo "== Пакети"
sudo apt update
sudo apt install -y git i2c-tools python3-gpiozero python3-serial python3-spidev python3-pytest

echo "== Інтерфейси (raspi-config nonint: 0 = увімкнути)"
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
# UART: апаратний порт увімкнути, консоль на ньому вимкнути, інакше loopback ловить логін-промпт
if sudo raspi-config nonint do_serial_hw 0 2>/dev/null; then
  sudo raspi-config nonint do_serial_cons 1
else
  sudo raspi-config nonint do_serial 2   # старіші версії raspi-config
fi

echo "== Перевірка"
ls -l /dev/serial0 /dev/spidev0.0 /dev/i2c-1 2>/dev/null || echo "Частина пристроїв з'явиться після перезавантаження"
vcgencmd get_throttled
echo "Готово. Виконай: sudo reboot"
