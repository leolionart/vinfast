#!/usr/bin/env python3
"""Bridge Play Integrity: chạy frida trong tiến trình app VinFast."""
from __future__ import annotations

import hashlib
import queue
import time
from pathlib import Path

import frida

PKG = "com.vinfast.companion.app"
SCRIPT = Path(__file__).with_name("frida_mint.js")


class Bridge:
    def __init__(self, pkg: str = PKG, timeout: int = 240, verbose: bool = True):
        self.pkg = pkg
        self.timeout = timeout
        self.verbose = verbose
        self.dev = frida.get_usb_device(timeout=15)
        self.session = None
        self.script = None
        self.q: queue.Queue = queue.Queue()

    def _on_message(self, msg, data):
        payload = msg.get("payload")
        if self.verbose:
            print("[frida]", payload if payload is not None else msg)
        if isinstance(payload, dict) and payload.get("t") in ("token", "error"):
            self.q.put(payload)

    def _resolve_pid(self):
        try:
            return self.dev.get_process(self.pkg).pid
        except Exception:
            pass
        for p in self.dev.enumerate_processes():
            if "vinfast" in p.name.lower():
                return p.pid
        raise RuntimeError("không thấy tiến trình app VinFast")

    def attach(self):
        pid = self._resolve_pid()
        self.session = self.dev.attach(pid)
        self.script = self.session.create_script(SCRIPT.read_text(encoding="utf-8"))
        self.script.on("message", self._on_message)
        self.script.load()
        return pid

    def device_id(self) -> str:
        return self.script.exports_sync.deviceid()

    def integrity_token(self, nonce_hex: str, timeout: int | None = None) -> str:
        while not self.q.empty():
            self.q.get_nowait()
        self.script.exports_sync.mint(nonce_hex)
        deadline = time.time() + (timeout or self.timeout)
        while time.time() < deadline:
            try:
                msg = self.q.get(timeout=deadline - time.time())
            except queue.Empty:
                break
            if msg["t"] == "token":
                return msg["v"]
            raise RuntimeError("integrity: " + str(msg.get("v")))
        raise TimeoutError("hết thời gian chờ Play Integrity token")

    def close(self):
        try:
            if self.session:
                self.session.detach()
        except Exception:
            pass


if __name__ == "__main__":
    b = Bridge()
    print("attached pid", b.attach())
    print("device id:", b.device_id())
    nonce = hashlib.sha256(b"selftest" + str(time.time()).encode()).hexdigest()
    t0 = time.time()
    tok = b.integrity_token(nonce)
    print(f"token len={len(tok)} in {time.time()-t0:.1f}s")
    print("token head:", tok[:60])
    b.close()
