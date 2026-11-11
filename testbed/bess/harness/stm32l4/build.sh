#!/usr/bin/env bash
# Build the real-target PIL firmware of subject 3 for one version directory.
#   build.sh <version_dir> <nucleo|iotnode> [baud]
# Needs vectors.c/vectors.h in $VECDIR (made by gen_vectors.py). Produces <version_dir>/fw_<board>.{elf,bin}
set -euo pipefail
V="$1"; BOARD="$2"; BAUD="${3:-115200}"
HERE="$(cd "$(dirname "$0")" && pwd)"
VECDIR="${VECDIR:-$HOME/cicd-work/bess/stm32vec}"
case "$BOARD" in
  nucleo)  DEF=-DBOARD_NUCLEO_L476 ;;
  iotnode) DEF=-DBOARD_IOTNODE ;;
  *) echo "board must be nucleo or iotnode" >&2; exit 2 ;;
esac
cd "$V"
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O2 -std=c11 \
  -ffunction-sections -fdata-sections -nostartfiles -nostdlib \
  "$DEF" -DPIL_BAUD="${BAUD}u" -I. -I"$HERE" -I"$VECDIR" \
  -T "$HERE/stm32l4.ld" -Wl,--gc-sections \
  "$HERE/startup.c" "$HERE/board.c" "$HERE/pil_main.c" bess.c "$VECDIR/vectors.c" \
  -lm -lc -lgcc -o "fw_${BOARD}.elf"
arm-none-eabi-objcopy -O binary "fw_${BOARD}.elf" "fw_${BOARD}.bin"
arm-none-eabi-size "fw_${BOARD}.elf" | tail -1
