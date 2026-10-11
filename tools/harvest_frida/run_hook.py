#!/usr/bin/env python3
"""Spawn app VinFast với hook, ghi lại luồng đăng ký."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import frida

PKG = "com.vinfast.companion.app"
SCRIPT = Path(__file__).with_name("frida_hook.js")
SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 75

dev = frida.get_usb_device(timeout=15)
try:
    dev.kill(PKG)
except Exception:
    pass
time.sleep(2)
pid = dev.spawn([PKG])
session = dev.attach(pid)
script = session.create_script(SCRIPT.read_text(encoding="utf-8"))


def on_message(msg, data):
    p = msg.get("payload")
    if isinstance(p, dict) and p.get("t") == "log":
        print(p["m"], flush=True)
    else:
        print("[msg]", msg, flush=True)


script.on("message", on_message)
script.load()
dev.resume(pid)
print(f"--- spawned pid={pid}, theo dõi {SECS}s ---", flush=True)
time.sleep(SECS)
session.detach()
print("--- hết ---")
