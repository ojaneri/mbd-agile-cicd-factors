"""Flash one PIL firmware on the NUCLEO-L476RG and capture its stream until @END (runs on Windows).

Usage: py -3 pil_nucleo_win.py <fw.bin> <drive, e.g. F:> <COMx> <baud> <out.txt> [timeout_s]
Prints one JSON line: {"ok":..., "seconds_flash":..., "seconds_run":..., "bytes":..., "error":...}
The serial port is opened BEFORE the copy so the boot output is not lost (copying the .bin resets
the board, as in the author's earlier capture.py).
"""
import json
import os
import shutil
import sys
import time

import serial  # pyserial (installed on this PC)


def main():
    fw, drive, port, baud, out = sys.argv[1:6]
    timeout = float(sys.argv[6]) if len(sys.argv) > 6 else 600.0
    rep = dict(ok=False, seconds_flash=None, seconds_run=None, bytes=0, error=None)
    if not os.path.isdir(drive + "\\"):
        rep["error"] = f"board drive {drive} not present"
        print(json.dumps(rep))
        return 2
    try:
        with serial.Serial(port, int(baud), timeout=0.5) as ser, open(out, "wb") as fo:
            ser.reset_input_buffer()
            t0 = time.time()
            shutil.copy(fw, drive + "\\")
            rep["seconds_flash"] = time.time() - t0
            t1, buf = time.time(), b""
            while time.time() - t1 < timeout:
                chunk = ser.read(65536)
                if chunk:
                    fo.write(chunk)
                    buf = (buf + chunk)[-64:]
                    rep["bytes"] += len(chunk)
                    if b"@END" in buf:
                        rep["ok"] = True
                        break
            rep["seconds_run"] = time.time() - t1
            if not rep["ok"]:
                rep["error"] = "timeout before @END"
    except serial.SerialException as e:
        rep["error"] = f"serial: {e}"
    print(json.dumps(rep))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
