"""FIT IoT-LAB st-iotnode (STM32L475VG) as the replication PIL target. Lessons applied (earlier articles):
- submit and flash the .elf, never .hex;
- ONE serial connection per node: the remote nc is wrapped in `timeout`, so it never lingers;
- attach the serial capture first, then reset the node, so the stream starts at @BEGIN;
- the first connection right after Running may be refused while flashing: retry for ~3 min.
One experiment holds ONE node for the whole campaign (etiquette: never all nodes of a site > 3 h).
"""
import json
import subprocess
import time

CLI = "/opt/iotlab-venv/bin"
SITE = "saclay"
ARCHI = "st-iotnode"
FRONT = f"janeri@{SITE}.iot-lab.info"
SSH = ["ssh", "-i", "/root/.ssh/iotlab_ed25519", "-o", "StrictHostKeyChecking=accept-new",
       "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", FRONT]


def _cli(*args, timeout=300):
    r = subprocess.run([f"{CLI}/{args[0]}", *args[1:]], capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def alive_nodes():
    rc, out, _ = _cli("iotlab-status", "--nodes", "--archi", ARCHI, "--state", "Alive", "--site", SITE)
    items = json.loads(out).get("items", [])
    return sorted(int(i["network_address"].split(".")[0].split("-")[-1]) for i in items)


def submit(elf, node, minutes, name="cicd-pil"):
    rc, out, err = _cli("iotlab-experiment", "submit", "-n", name, "-d", str(minutes),
                        "-l", f"{SITE},{ARCHI},{node},{elf}")
    if rc != 0:
        raise RuntimeError(err or out)
    exp = json.loads(out)["id"]
    _cli("iotlab-experiment", "wait", "-i", str(exp), "--state", "Running", "--timeout", "1800", timeout=1900)
    return exp


def flash(exp, node, elf):
    rc, out, err = _cli("iotlab-node", "--flash", str(elf), "-i", str(exp), "-l", f"{SITE},{ARCHI},{node}",
                        timeout=300)
    try:
        return json.loads(out).get("0") is not None, out
    except Exception:
        return False, out + err


def reset(exp, node):
    return _cli("iotlab-node", "--reset", "-i", str(exp), "-l", f"{SITE},{ARCHI},{node}")


def capture(exp, node, outfile, run_timeout=240):
    """Attach nc first, reset, read until @END. Returns dict like the Nucleo runner."""
    rep = dict(ok=False, seconds_run=None, bytes=0, error=None, attempts=0)
    t_end = time.time() + 180
    while time.time() < t_end:
        rep["attempts"] += 1
        with open(outfile, "wb") as fo:
            p = subprocess.Popen(SSH + [f"timeout {run_timeout + 30} nc {ARCHI}-{node} 20000"],
                                 stdout=fo, stderr=subprocess.PIPE)
            time.sleep(3)
            if p.poll() is not None:  # refused: retry
                time.sleep(15)
                continue
            reset(exp, node)
            t1 = time.time()
            while time.time() - t1 < run_timeout and p.poll() is None:
                time.sleep(1)
                fo.flush()
                with open(outfile, "rb") as fi:
                    fi.seek(0, 2)
                    size = fi.tell()
                    fi.seek(max(0, size - 64))
                    if b"@END" in fi.read():
                        rep["ok"] = True
                        break
            rep["seconds_run"] = time.time() - t1
            p.terminate()
            try:
                p.wait(10)
            except subprocess.TimeoutExpired:
                p.kill()
        rep["bytes"] = __import__("os").path.getsize(outfile)
        if rep["ok"]:
            break
        rep["error"] = "no @END"
    # Killing the local ssh does not kill the remote nc; kill it explicitly (one connection per node).
    subprocess.run(SSH + [f"pkill -u janeri -f 'nc {ARCHI}-{node} 20000' || true"], capture_output=True, text=True)
    time.sleep(1)
    stale = subprocess.run(SSH + ["pgrep -u janeri -a nc || true"], capture_output=True, text=True).stdout.strip()
    rep["stale_nc_after"] = stale
    return rep


def stop(exp):
    return _cli("iotlab-experiment", "stop", "-i", str(exp))
