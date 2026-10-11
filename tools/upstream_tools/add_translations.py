#!/usr/bin/env python3
"""Them nhan dich cho emqx_host / emqx_port vao translations."""
import json
import shutil
import time
from pathlib import Path

DIR = Path("/home/pi/.homeassistant/custom_components/vinfast/translations")
LABELS = {
    "en": {"emqx_host": "MQTT server (host) — blank = use const.py",
           "emqx_port": "MQTT server (port) — blank = use const.py"},
    "vi": {"emqx_host": "Máy chủ MQTT (host) — để trống = dùng const.py",
           "emqx_port": "Máy chủ MQTT (port) — để trống = dùng const.py"},
}

for lang, labels in LABELS.items():
    p = DIR / f"{lang}.json"
    if not p.exists():
        print(f"  [BỎ QUA] {p} không tồn tại")
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    step = d.setdefault("options", {}).setdefault("step", {}).setdefault("init", {})
    data = step.setdefault("data", {})
    before = len(data)
    for k, v in labels.items():
        data[k] = v
    bak = p.with_suffix(f".json.bak_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(p, bak)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [OK] {p.name}: {before} -> {len(data)} trường")
    for k in labels:
        print(f"        {k}: {data[k]}")
