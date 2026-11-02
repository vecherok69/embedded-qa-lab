#!/usr/bin/env bash
# День 3: регресійний прогін усіх pytest-тестів стенда з логами.
#
# Тести розбито на дві фази, бо вони потребують різної комутації UART:
#   loopback  перемички пін 8 <-> 10 (UART), 19 <-> 21 (SPI), 11 <-> 13 (GPIO); Pico не підключено
#             -> src/pi3/test_interfaces.py
#   pico      перемичку 8 <-> 10 знято, Pico підключено (пін 8 -> GP1, пін 10 <- GP0, GND),
#             на Pico запущено src/pico/uart_echo_display.py з MODE = "fast"
#             -> src/pi3/test_pico_uart.py + src/pi3/test_pico_display.py
#
# Запуск:  bash scripts/pi3/run_all_tests.sh loopback
#          bash scripts/pi3/run_all_tests.sh pico
#
# Результат у logs/:
#   day3-<фаза>-<час>.txt  стан стенда до/після + повний вивід pytest
#   day3-<фаза>-<час>.xml  JUnit XML (машиночитаний звіт, так його забирає CI)
set -uo pipefail

phase="${1:-}"
case "$phase" in
  loopback) tests=(src/pi3/test_interfaces.py) ;;
  pico)     tests=(src/pi3/test_pico_uart.py src/pi3/test_pico_display.py) ;;
  *) echo "Вкажи фазу: loopback або pico"; exit 2 ;;
esac

cd "$(dirname "$0")/../.." || exit 1
mkdir -p logs
stamp="$(date +%Y%m%d-%H%M%S)"
out="logs/day3-${phase}-${stamp}.txt"
xml="logs/day3-${phase}-${stamp}.xml"

snapshot() {
  echo "### $1"
  echo "date:      $(date -Is)"
  echo "throttled: $(vcgencmd get_throttled 2>&1)"
  echo "temp:      $(vcgencmd measure_temp 2>&1)"
  echo "clock arm: $(vcgencmd measure_clock arm 2>&1)"
  echo "serial0:   $(readlink -f /dev/serial0 2>&1)"
  # Лічильники драйвера UART (tx/rx/oe): незалежний прилад, як у BUG-004
  echo "uart counters:"
  sudo -n cat /proc/tty/driver/serial 2>&1 | sed 's/^/  /'
  echo
}

{
  echo "=== День 3, фаза: $phase"
  echo "commit:    $(git rev-parse --short HEAD 2>/dev/null || echo 'немає git')"
  echo "branch:    $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  echo "kernel:    $(uname -r)"
  echo "model:     $(tr -d '\0' < /proc/device-tree/model)"
  echo "python:    $(python3 --version 2>&1)"
  echo "pytest:    $(python3 -m pytest --version 2>&1 | head -n1)"
  echo "тести:     ${tests[*]}"
  echo
  snapshot "стан стенда ДО прогону"
} | tee "$out"

started=$(date +%s)
python3 -m pytest -v -s -rA --junitxml="$xml" "${tests[@]}" 2>&1 | tee -a "$out"
rc=${PIPESTATUS[0]}
elapsed=$(( $(date +%s) - started ))

{
  echo
  snapshot "стан стенда ПІСЛЯ прогону"
  echo "=== Підсумок: код виходу pytest = $rc (0 = усі passed), тривалість ${elapsed} с"
  echo "Лог:   $out"
  echo "JUnit: $xml"
} | tee -a "$out"

exit "$rc"
