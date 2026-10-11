#!/usr/bin/env python3
"""Vá challenge limit TrickyStore OSS rồi tính lại checksum + signature của DEX."""
import hashlib
import sys
import zlib

SRC, DST = sys.argv[1], sys.argv[2]
NEW_LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 512

raw = bytearray(open(SRC, "rb").read())
CODE_OFF, INSNS_SIZE = 1477840, 952
CODE_START, CODE_END = CODE_OFF + 16, CODE_OFF + 16 + INSNS_SIZE * 2

pat = bytes([0x13, 0x0E, 0x80, 0x00])
cands = []
s = CODE_START
while True:
    p = raw.find(pat, s, CODE_END)
    if p == -1:
        break
    cands.append(p)
    s = p + 1

target = None
for p in cands:
    nxt = int.from_bytes(raw[p + 4:p + 6], "little") & 0xFF
    if nxt == 0x38:
        window = raw[p + 4:p + 14]
        ops = [int.from_bytes(window[i:i + 2], "little") & 0xFF for i in range(0, len(window) - 1, 2)]
        if 0x37 in ops or 0x36 in ops:
            target = p

if target is None:
    print("không xác định được lệnh đích")
    sys.exit(1)

print(f"vá const/16 v14, 128 tại {target} -> {NEW_LIMIT}")
raw[target + 2:target + 4] = NEW_LIMIT.to_bytes(2, "little", signed=True)

old_s = b"B > 128)"
new_s = f"B > {NEW_LIMIT})".encode()
if len(new_s) == len(old_s):
    n = st = 0
    while True:
        q = raw.find(old_s, st)
        if q == -1:
            break
        raw[q:q + len(old_s)] = new_s
        n += 1
        st = q + len(old_s)
    print(f"vá {n} chuỗi log")

# --- tính lại signature (SHA-1 từ offset 32) và checksum (Adler32 từ offset 12) ---
sig = hashlib.sha1(bytes(raw[32:])).digest()
raw[12:32] = sig
chk = zlib.adler32(bytes(raw[12:])) & 0xFFFFFFFF
raw[8:12] = chk.to_bytes(4, "little")
print(f"signature mới: {sig.hex()}")
print(f"checksum mới : 0x{chk:08x}")

open(DST, "wb").write(bytes(raw))
print(f"ghi {DST} ({len(raw)} byte)")
