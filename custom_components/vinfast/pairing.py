"""VinFast remote-control pairing (tạo ``sess_id`` + share key).

Dịch ngược từ ``base_1.apk``:

* ``RemoteControlManager.T0(qrPayload, context)``   — quét QR trên màn hình xe, dựng khoá.
* ``ActivateRemoteControlsOTPViewModel.V()/W()``    — gọi ``verify-session`` (xin / gửi lại OTP).
* ``ActivateRemoteControlsOTPViewModel.a0(otp)``    — gọi ``send-pair-data`` để hoàn tất pairing.
* ``PairData`` / ``PairResponseDto``                — cấu trúc dữ liệu hai chiều.

QR trên màn hình xe có dạng ``K=<b64>&ssid=<...>&vin=<...>&profileId=<b64>&timeout=<n>``.

Luồng khoá::

    key1         = HMAC_SHA256( base64decode(K), vin_bytes + seed1_bytes )      # AES-256 key
    csr_pem      = PKCS#10(SHA256withRSA, CN={vin}_{android_id}, OU={device_name})
    encryptedCSR = Base64NoWrap( AES-CBC-PKCS7( key=key1, iv=seed1, data=csr_pem ) )
    seed         = Base64NoWrap( seed1 )                                        # seed1 = 16 ký tự [A-Za-z0-9]
    sessionId    = ssid                                                          # chính là ssid trong QR

``send-pair-data`` trả về ``{encrypted_cert, sess_id, seed2, presharedkey_v2}``.
``sess_id`` là giá trị mà lớp điều khiển dùng làm field ``sess_id``;
``presharedkey_v2`` là share key cho ``signature2``.

Module không import Home Assistant để kiểm thử offline được.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import random
import re
import string
from dataclasses import dataclass, field
from typing import Any, Mapping

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

PAIR_SESSION_PATH = "/ccaraccessmgmt/api/v1/pairing/app/verify-session"
PAIR_DATA_PATH = "/ccaraccessmgmt/api/v1/pairing/app/send-pair-data"

#: Thứ tự khoá bắt buộc trong QR (đúng như ``RemoteControlManager.T0``).
QR_REQUIRED_KEYS = ("K", "ssid", "vin", "timeout", "profileId")

#: Ký tự được escape khi đưa vào X500Principal (RFC 2253) — đúng như app.
_X500_ESCAPE_CHARS = (",", "=", "+", "<", ">", "#", ";")

_SEED_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits


class PairingError(Exception):
    """Lỗi dữ liệu QR / khoá / phản hồi pairing."""


# ---------------------------------------------------------------------------
# QR của xe
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VehicleQrPayload:
    key_b64: str
    key_bytes: bytes
    ssid: str
    vin: str
    profile_id_b64: str
    timeout: int
    raw: Mapping[str, str] = field(default_factory=dict)


def _escape_x500(value: str) -> str:
    return "".join(("\\" + ch) if ch in _X500_ESCAPE_CHARS else ch for ch in value)


def parse_vehicle_qr(text: str) -> VehicleQrPayload:
    """Phân tích payload QR của xe và kiểm tra đủ khoá bắt buộc."""
    raw: dict[str, str] = {}
    for chunk in str(text or "").split("&"):
        if not chunk or "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        raw[key.strip()] = value.strip()

    missing = [k for k in QR_REQUIRED_KEYS if not raw.get(k)]
    if missing:
        raise PairingError(
            "QR thiếu khoá bắt buộc: " + ", ".join(missing) + f" (nhận được: {sorted(raw)})"
        )

    try:
        key_bytes = base64.b64decode(raw["K"], validate=False)
    except Exception as exc:  # noqa: BLE001
        raise PairingError(f"K trong QR không phải Base64 hợp lệ: {exc}") from exc
    if len(key_bytes) < 16:
        raise PairingError(f"K quá ngắn ({len(key_bytes)} byte), cần tối thiểu 16 byte.")

    try:
        timeout = int(raw["timeout"])
    except (TypeError, ValueError) as exc:
        raise PairingError(f"timeout trong QR không phải số: {raw['timeout']!r}") from exc

    return VehicleQrPayload(
        key_b64=raw["K"],
        key_bytes=key_bytes,
        ssid=raw["ssid"],
        vin=raw["vin"],
        profile_id_b64=raw["profileId"],
        timeout=timeout,
        raw=raw,
    )


def qr_profile_user_id(qr: VehicleQrPayload) -> str | None:
    """``profileId`` trong QR là ``Base64NoWrap(userId)`` — trả về userId đã giải mã."""
    try:
        return base64.b64decode(qr.profile_id_b64).decode("utf-8")
    except Exception:  # noqa: BLE001
        return None


def check_qr_against_account(qr: VehicleQrPayload, vin: str, user_id: str) -> None:
    """Hai kiểm tra mà app thực hiện trước khi dựng khoá (PairStatus)."""
    if vin and qr.vin != vin:
        raise PairingError(f"QR_NOT_MATCHED_VINCODE: QR cho {qr.vin}, tài khoản đang chọn {vin}.")
    qr_user = qr_profile_user_id(qr)
    if qr_user and user_id and qr_user != user_id:
        raise PairingError(f"QR_NOT_MATCHED_PROFILE: QR của profile {qr_user}, tài khoản {user_id}.")


# ---------------------------------------------------------------------------
# Sinh khoá
# ---------------------------------------------------------------------------

def generate_seed(length: int = 16) -> str:
    """``SecurityUtils.p(n)`` — chuỗi ngẫu nhiên gồm ``[A-Za-z0-9]``."""
    return "".join(random.choice(_SEED_ALPHABET) for _ in range(length))


def derive_key1(key_bytes: bytes, vin: str, seed: str) -> bytes:
    """``SecurityUtils.n(K, [vin, seed1])`` — HMAC-SHA256, khoá AES-256."""
    mac = hmac.new(key_bytes, digestmod=hashlib.sha256)
    mac.update(vin.encode("utf-8"))
    mac.update(seed.encode("utf-8"))
    return mac.digest()


def build_csr_pem(vin: str, android_id: str, device_name: str, private_key: rsa.RSAPrivateKey) -> str:
    """``SecurityUtils.l(keyPair, X500Principal("CN={vin}_{androidId}, OU = {deviceName}"))``.

    ``device_name`` truyền vào là giá trị **thô**; thư viện ``cryptography`` tự escape
    theo RFC 4514 khi mã hoá DER (app escape thủ công vì nó parse từ chuỗi X500).
    """
    subject = x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, f"{vin}_{android_id}"),
        x509.NameAttribute(x509.NameOID.ORGANIZATIONAL_UNIT_NAME, device_name),
    ])
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(subject)
        .sign(private_key, hashes.SHA256())
    )
    return csr.public_bytes(serialization.Encoding.PEM).decode("utf-8")


def _pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    pad = block_size - (len(data) % block_size)
    return data + bytes([pad]) * pad


def _pkcs7_unpad(data: bytes, block_size: int = 16) -> bytes:
    if not data or len(data) % block_size:
        raise PairingError("Dữ liệu AES không phải bội số của 16 byte — sai khoá hoặc sai IV.")
    pad = data[-1]
    if not 1 <= pad <= block_size or data[-pad:] != bytes([pad]) * pad:
        raise PairingError("Padding PKCS7 không hợp lệ — sai khoá hoặc sai IV.")
    return data[:-pad]


def encrypt_csr_base64(key1: bytes, csr_pem: str, seed: str) -> str:
    """``SecurityUtils.k(key1, csrPEM, iv=seed1)`` — AES/CBC/**PKCS7** rồi Base64 NO_WRAP.

    ``cryptography`` không tự thêm padding (khác BouncyCastle bên app), nên phải pad tay.
    """
    encryptor = Cipher(algorithms.AES(key1), modes.CBC(seed.encode("utf-8"))).encryptor()
    payload = encryptor.update(_pkcs7_pad(csr_pem.encode("utf-8"))) + encryptor.finalize()
    return base64.b64encode(payload).decode("ascii")


def decrypt_csr_base64(key1: bytes, encrypted_csr_b64: str, seed: str) -> str:
    """Giải mã ``encryptedCSR`` — dùng để tự kiểm tra và để đối chiếu khi gỡ lỗi."""
    decryptor = Cipher(algorithms.AES(key1), modes.CBC(seed.encode("utf-8"))).decryptor()
    plain = decryptor.update(base64.b64decode(encrypted_csr_b64)) + decryptor.finalize()
    return _pkcs7_unpad(plain).decode("utf-8")


@dataclass
class PairSecrets:
    """Toàn bộ dữ liệu cục bộ sinh ra ở bước quét QR."""

    vin: str
    profile_id_b64: str
    ssid: str
    seed1: str
    key1: bytes
    csr_pem: str
    encrypted_csr: str
    private_key_pem: str


def create_pair_secrets(
    qr: VehicleQrPayload,
    android_id: str,
    device_name: str,
    *,
    seed: str | None = None,
    key_size: int = 2048,
) -> PairSecrets:
    """Sinh khoá RSA + CSR + ``encryptedCSR`` đúng như ``RemoteControlManager.T0``."""
    if not qr.ssid:
        raise PairingError("QR không có ssid — dùng làm sessionId của phiên pairing.")

    seed1 = seed or generate_seed(16)
    if len(seed1.encode("utf-8")) != 16:
        raise PairingError(
            f"seed1 phải đúng 16 byte (AES IV), hiện tại {len(seed1.encode('utf-8'))} byte."
        )

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    csr_pem = build_csr_pem(qr.vin, android_id, device_name, private_key)
    key1 = derive_key1(qr.key_bytes, qr.vin, seed1)
    encrypted_csr = encrypt_csr_base64(key1, csr_pem, seed1)

    return PairSecrets(
        vin=qr.vin,
        profile_id_b64=qr.profile_id_b64,
        ssid=qr.ssid,
        seed1=seed1,
        key1=key1,
        csr_pem=csr_pem,
        encrypted_csr=encrypted_csr,
        private_key_pem=private_key_pem,
    )


# ---------------------------------------------------------------------------
# Body request — đúng thứ tự tham số của RemoteRepository / RemoteApi
# ---------------------------------------------------------------------------

def pair_session_body(ssid: str, mobile_phone: str | None = None, email: str | None = None,
                      retry: bool = False) -> dict[str, Any]:
    """``PairSessionRequest`` cho ``POST verify-session``."""
    return {
        "sessionId": ssid,
        "mobilePhone": mobile_phone,
        "email": email,
        "retry": bool(retry),
    }


def pair_data_body(secrets: PairSecrets, otp: str, phone_number: str | None = None,
                   email: str | None = None) -> dict[str, Any]:
    """``PairDataRequest`` cho ``POST send-pair-data``.

    Thứ tự tham số trong ``RemoteControlManager.a0``::

        repo.b(pairData.b() /*encryptedCSR*/, otp, phoneNumber, email,
               pairData.d() /*seed = base64Seed1*/, pairData.g() /*sessionId = ssid*/)
    """
    if not str(otp or "").strip():
        raise PairingError("Cần OTP để gọi send-pair-data.")
    return {
        "encryptedCSR": secrets.encrypted_csr,
        "otp": str(otp).strip(),
        "phoneNumber": phone_number,
        "email": email,
        "seed": base64.b64encode(secrets.seed1.encode("utf-8")).decode("ascii"),
        "sessionId": secrets.ssid,
    }


@dataclass
class PairResult:
    sess_id: str
    share_key: str | None
    encrypted_cert: str | None
    seed2: str | None


def parse_pair_response(body: Any) -> PairResult:
    """Đọc ``PairResponseDto``: ``{encrypted_cert, sess_id, seed2, presharedkey_v2}``."""
    if not isinstance(body, dict):
        raise PairingError(f"Phản hồi pairing không phải JSON object: {type(body).__name__}")
    data = body.get("data") if isinstance(body.get("data"), dict) else body
    sess_id = data.get("sess_id") or data.get("sessId")
    if not sess_id:
        raise PairingError(
            "Phản hồi pairing không có 'sess_id'. Nội dung: " + json.dumps(body, ensure_ascii=False)[:400]
        )
    return PairResult(
        sess_id=str(sess_id),
        share_key=data.get("presharedkey_v2"),
        encrypted_cert=data.get("encrypted_cert"),
        seed2=data.get("seed2"),
    )


def looks_like_qr(text: str) -> bool:
    """Heuristic nhận biết chuỗi QR hợp lệ (dùng cho CLI)."""
    return bool(re.search(r"(?:^|&)K=", str(text or "")))
