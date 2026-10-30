#!/usr/bin/env bash
# Збір діагностики стенда в один файл logs/<дата>_<мітка>.log
# Запуск: bash scripts/pi3/collect_logs.sh before-disable-bt
set -uo pipefail

label="${1:-snapshot}"
mkdir -p logs
out="logs/$(date +%Y%m%d-%H%M%S)_${label}.log"

{
  echo "### date";            date -Is
  echo "### uname";           uname -a
  echo "### os";              cat /etc/os-release
  echo "### model";           tr -d '\0' < /proc/device-tree/model; echo
  echo "### throttled";       vcgencmd get_throttled
  echo "### temp";            vcgencmd measure_temp
  echo "### volts core";      vcgencmd measure_volts core
  echo "### clock arm";       vcgencmd measure_clock arm
  echo "### serial links";    ls -l /dev/serial* 2>&1
  echo "### spi/i2c";         ls -l /dev/spidev* /dev/i2c-* 2>&1
  echo "### i2cdetect -y 1";  i2cdetect -y 1 2>&1
  echo "### config.txt (без коментарів)"
  grep -vE '^\s*(#|$)' /boot/firmware/config.txt 2>/dev/null || grep -vE '^\s*(#|$)' /boot/config.txt
  echo "### dmesg (uart|spi|i2c|voltage)"
  dmesg | grep -iE 'uart|tty(S|AMA)|spi|i2c|voltage' | tail -n 50
} > "$out" 2>&1

echo "Записано: $out"
