#!/usr/bin/env bash
# List alive FIT IoT-LAB nodes per architecture and site (to choose a second real board).
export PATH=/opt/iotlab-venv/bin:$PATH
iotlab-status --nodes --state Alive > /tmp/iotlab_nodes.json 2>/dev/null || iotlab-status --nodes > /tmp/iotlab_nodes.json
python - <<'EOF'
import json, collections
d = json.load(open("/tmp/iotlab_nodes.json"))["items"]
c = collections.Counter((n.get("archi"), n.get("site")) for n in d)
for k, v in sorted(c.items(), key=lambda kv: str(kv[0])):
    print(k, v)
EOF
