#!/usr/bin/env python3
"""Harvest bộ ba UAA cho một tài khoản VinFast, dùng bridge Play Integrity trên điện thoại.

Tái tạo từ APK 2.26.11 (com.vinfast.companion.app):
  Auth0 /oauth/token  ->  GET ccaruaa/api/v1/auth/client/challenge
  ->  osPublicKey = base64(SPKI) của khoá RSA tạm
  ->  playNonce = sha256_hex(nonceRegister + osPublicKey)
  ->  Play Integrity token (bridge Frida trong tiến trình app)
  ->  POST ccaruaa/api/v1/auth/client/register {integrityToken,nonceRegister,osPublicKey}
  ->  clientInstanceId
  ->  signature = base64(RSA_SHA256(sha256_hex(clientInstanceId + timestamp)))
  ->  POST ccaruaa/oauth/token (form) -> CCP token
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

sys.path.insert(0, str(Path(__file__).parent))
from bridge import Bridge  # noqa: E402

AUTH0_DOMAIN = "https://vin3s.au.auth0.com"
AUTH0_CLIENT_ID = "jE5xt50qC7oIh1f32qMzA6hGznIU5mgH"
API_BASE = "https://mobile.connected-car.vinfast.vn"
BASIC_AUTH = "Basic Y2FwcDhPWFdEOWJGYkdpRkc6YnFGZ2pLQ0I2U0pqZ0w3bQ=="
APP_VERSION = "2.26.11"
SERIAL = "hq6dcixwmjjj5hsk"

CHALLENGE = "/ccaruaa/api/v1/auth/client/challenge"
REGISTER = "/ccaruaa/api/v1/auth/client/register"
OAUTH = "/ccaruaa/oauth/token"
USER_VEHICLE = "/ccarusermgnt/api/v1/user-vehicle"
PING = "/ccaraccessmgmt/api/v1/telemetry/app/ping"


def sh(*args, timeout=60):
    return subprocess.run(["adb", "-s", SERIAL, *args], capture_output=True, text=True,
                          timeout=timeout).stdout


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def spki_b64(pub) -> str:
    der = pub.public_bytes(serialization.Encoding.DER,
                           serialization.PublicFormat.SubjectPublicKeyInfo)
    return base64.b64encode(der).decode()


def device_headers(device_id: str, os_version: str) -> dict:
    return {
        "X-Device-Identifier": device_id,
        "X-APP-VERSION": APP_VERSION,
        "X-Device-Family": "Redmi Note 8 Pro",
        "X-Device-Locale": "vi_VN",
        "X-Device-Platform": "android",
        "X-Device-OS-Version": f"android {os_version}",
        "X-SERVICE-NAME": "CAPP",
        "X-Timezone": "Asia/Ho_Chi_Minh",
        "X-TIMESTAMP": str(int(time.time() * 1000)),
        "User-Agent": f"android - {device_id} - {APP_VERSION}",
        "Accept": "application/json",
    }


def auth0_login(email: str, password: str) -> str:
    r = requests.post(
        f"{AUTH0_DOMAIN}/oauth/token",
        json={"grant_type": "password", "client_id": AUTH0_CLIENT_ID, "audience": API_BASE,
              "username": email, "password": password},
        headers={"Content-Type": "application/json", "X-APP-VERSION": APP_VERSION},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def get_challenge(at: str, hdr: dict) -> str:
    h = dict(hdr)
    h["Authorization"] = f"Bearer {at}"
    r = requests.get(f"{API_BASE}{CHALLENGE}", headers=h, timeout=30)
    r.raise_for_status()
    return (r.json().get("data") or {}).get("value")


def register_client(at: str, os_pub: str, nonce: str, itok: str, hdr: dict) -> str:
    h = dict(hdr)
    h["Authorization"] = f"Bearer {at}"
    h["Content-Type"] = "application/json; charset=UTF-8"
    r = requests.post(f"{API_BASE}{REGISTER}", json={
        "integrityToken": itok, "nonceRegister": nonce, "osPublicKey": os_pub}, headers=h, timeout=60)
    if r.status_code != 200:
        print(f"   register HTTP {r.status_code}: {r.text[:400]}")
    r.raise_for_status()
    return (r.json().get("data") or {}).get("clientInstanceId")


def uaa_exchange(priv, cid: str, ts: str, sig: str, hdr: dict) -> str:
    body = (f"grant_type=app&timestamp={ts}&clientInstanceId={cid}"
            f"&signature={requests.utils.quote(sig, safe='')}")
    h = dict(hdr)
    h["Authorization"] = BASIC_AUTH
    h["Content-Type"] = "application/x-www-form-urlencoded"
    h["X-TIMESTAMP"] = ts
    r = requests.post(f"{API_BASE}{OAUTH}", data=body, headers=h, timeout=30)
    r.raise_for_status()
    return r.json().get("access_token")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", default=None)
    ap.add_argument("--out", default="/tmp/vfharvest/harvest_result.json")
    args = ap.parse_args()
    if not args.password:
        args.password = os.environ.get("VF_PASSWORD", "")
    if not args.password:
        print("thiếu mật khẩu (--password hoặc VF_PASSWORD)")
        return 2

    os_version = sh("shell", "getprop ro.build.version.release").strip() or "11"

    print("1. Auth0 login…")
    at = auth0_login(args.email, args.password)
    print(f"   access_token {len(at)} ký tự")

    b = Bridge(verbose=False)
    b.attach()
    device_id = b.device_id()
    print(f"   X-Device-Identifier (SSAID app) = {device_id}")
    hdr = device_headers(device_id, os_version)

    print("2. challenge…")
    nonce = get_challenge(at, hdr)
    print(f"   nonceRegister = {nonce}")

    print("3. khoá RSA 2048 tạm (chỉ trong RAM)…")
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    os_pub = spki_b64(priv.public_key())
    print(f"   osPublicKey {len(os_pub)} ký tự")

    print("4. playNonce = sha256(nonceRegister + osPublicKey)…")
    play_nonce = sha256_hex(nonce + os_pub)
    print(f"   {play_nonce}")

    print("5. Play Integrity token qua bridge…")
    t0 = time.time()
    itok = b.integrity_token(play_nonce)
    print(f"   integrityToken {len(itok)} ký tự trong {time.time()-t0:.1f}s")

    print("6. client/register…")
    cid = register_client(at, os_pub, nonce, itok, hdr)
    print(f"   clientInstanceId = {cid}")

    print("7. chữ ký UAA…")
    ts = str(int(time.time() * 1000))
    digest_hex = sha256_hex(cid + ts)
    sig = base64.b64encode(priv.sign(digest_hex.encode("utf-8"),
                                     padding.PKCS1v15(), hashes.SHA256())).decode()

    print("8. đổi token UAA…")
    ccp = uaa_exchange(priv, cid, ts, sig, hdr)
    print(f"   CCP token {len(ccp)} ký tự")

    print("9. xác minh: user-vehicle…")
    hv = dict(hdr)
    hv["Authorization"] = f"Bearer {ccp}"
    rv = requests.get(f"{API_BASE}{USER_VEHICLE}", headers=hv, timeout=30)
    print(f"   HTTP {rv.status_code}")
    vin = None
    if rv.status_code == 200:
        veh = rv.json().get("data") or []
        vin = (veh[0] or {}).get("vinCode") if veh else None
        print(f"   VIN = {vin} | iotProvider = {(veh[0] or {}).get('iotProvider') if veh else None}")

    pem = priv.private_bytes(serialization.Encoding.PEM,
                             serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()

    out = {
        "email": args.email,
        "device_id": device_id,
        "uaa_client_instance_id": cid,
        "uaa_timestamp": ts,
        "uaa_signature": sig,
        "vinfast_private_key": pem,
        "vin": vin,
        "ccp_token_len": len(ccp),
        "integrity_token_len": len(itok),
        "api_base": API_BASE,
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐÃ GHI {args.out}")
    print("uaa_client_instance_id =", cid)
    print("uaa_timestamp          =", ts)
    b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
