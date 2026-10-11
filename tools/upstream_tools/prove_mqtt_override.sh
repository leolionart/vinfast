#!/bin/bash
# Chung minh override MQTT tu config entry thuc su co tac dung.
# Quy trinh: dung HA -> sua options -> chay HA -> xem log -> hoan tac -> chay lai.
set -e
CE=/home/pi/.homeassistant/.storage/core.config_entries
BAK=/tmp/core.config_entries.bak_override

echo "=== 1. Dung HA ==="
sudo -n systemctl stop hass@pi.service
sleep 5

cp "$CE" "$BAK"

echo "=== 2. Dat emqx_host = test-override.local (giu nguyen port) ==="
/home/pi/vinfast/env/bin/python3 - <<'PY'
import json
p = "/home/pi/.homeassistant/.storage/core.config_entries"
d = json.load(open(p, encoding="utf-8"))
n = 0
for e in d["data"]["entries"]:
    if e.get("domain") != "vinfast":
        continue
    e.setdefault("options", {})
    e["options"]["emqx_host"] = "test-override.local"
    n += 1
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"   da sua {n} entry")
PY

echo "=== 3. Chay HA + xem log ==="
sudo -n systemctl start hass@pi.service
sleep 80
journalctl -u hass@pi.service --since '-2 min' --no-pager -o cat \
  | grep -E 'CONST-SYNC. MQTT EMQX' | head -3

echo
echo "=== 4. Hoan tac ==="
sudo -n systemctl stop hass@pi.service
sleep 5
cp "$BAK" "$CE"
sudo -n systemctl start hass@pi.service
sleep 80
echo "--- MQTT sau khi hoan tac ---"
journalctl -u hass@pi.service --since '-2 min' --no-pager -o cat \
  | grep -E 'CONST-SYNC. MQTT EMQX|EMQX MQTT đã kết nối' | head -4
