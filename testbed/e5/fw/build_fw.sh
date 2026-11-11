#!/usr/bin/env bash
# Build the E5 firmware for one version dir.  build_fw.sh <version_dir> <soc|fuel|bess> <vecdir> [board] [passes]
# board: iotnode (default, USART1), nucleo, or nrf52840 (added 2026-11-11 for the E5b addendum). passes: 5 (default) or 1.
# Optimisation: env E5_OPT (default -O2, the frozen E5 setting). Produces <version_dir>/e5_<board>.elf
set -euo pipefail
V="$1"; SUBJ="$2"; VECDIR="$3"; BOARD="${4:-iotnode}"; PASSES="${5:-5}"
HERE="$(cd "$(dirname "$0")" && pwd)"
BSP="$HERE/../../soc/harness/stm32l4"
BOARDC="$BSP/board.c"; LD="$BSP/stm32l4.ld"
OPT="${E5_OPT:--O2}"
case "$BOARD" in
  nucleo)  DEF=-DBOARD_NUCLEO_L476 ;;
  iotnode) DEF=-DBOARD_IOTNODE ;;
  nrf52840) DEF=-DBOARD_NRF52840; BOARDC="$HERE/nrf52840/board.c"; LD="$HERE/nrf52840/nrf52840.ld" ;;
  *) echo "board must be nucleo, iotnode or nrf52840" >&2; exit 2 ;;
esac
case "$SUBJ" in
  soc)  SRC=soc_obs.c ;;
  fuel) SRC=fuel.c ;;
  bess) SRC=bess.c ;;
  *) echo "unknown subject" >&2; exit 2 ;;
esac
cd "$V"
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 "$OPT" -std=c11 \
  -ffunction-sections -fdata-sections -nostartfiles -nostdlib \
  "$DEF" -DPIL_BAUD=115200u -DE5_PASSES="${PASSES}u" -I. -I"$HERE" -I"$BSP" -I"$VECDIR" \
  -T "$LD" -Wl,--gc-sections \
  "$BSP/startup.c" "$BOARDC" "$HERE/e5_main.c" "$HERE/e5_${SUBJ}.c" "$SRC" "$VECDIR/vectors.c" \
  -lm -lc -lgcc -o "e5_${BOARD}.elf"
