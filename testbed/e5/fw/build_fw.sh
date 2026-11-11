#!/usr/bin/env bash
# Build the E5 firmware for one version dir.  build_fw.sh <version_dir> <soc|fuel|bess> <vecdir> [board] [passes]
# board: iotnode (default, USART1) or nucleo. passes: 5 (default) or 1. Produces <version_dir>/e5_<board>.elf
set -euo pipefail
V="$1"; SUBJ="$2"; VECDIR="$3"; BOARD="${4:-iotnode}"; PASSES="${5:-5}"
HERE="$(cd "$(dirname "$0")" && pwd)"
BSP="$HERE/../../soc/harness/stm32l4"
case "$BOARD" in
  nucleo)  DEF=-DBOARD_NUCLEO_L476 ;;
  iotnode) DEF=-DBOARD_IOTNODE ;;
  *) echo "board must be nucleo or iotnode" >&2; exit 2 ;;
esac
case "$SUBJ" in
  soc)  SRC=soc_obs.c ;;
  fuel) SRC=fuel.c ;;
  bess) SRC=bess.c ;;
  *) echo "unknown subject" >&2; exit 2 ;;
esac
cd "$V"
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O2 -std=c11 \
  -ffunction-sections -fdata-sections -nostartfiles -nostdlib \
  "$DEF" -DPIL_BAUD=115200u -DE5_PASSES="${PASSES}u" -I. -I"$HERE" -I"$BSP" -I"$VECDIR" \
  -T "$BSP/stm32l4.ld" -Wl,--gc-sections \
  "$BSP/startup.c" "$BSP/board.c" "$HERE/e5_main.c" "$HERE/e5_${SUBJ}.c" "$SRC" "$VECDIR/vectors.c" \
  -lm -lc -lgcc -o "e5_${BOARD}.elf"
