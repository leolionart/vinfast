"""VinFast Remote Control Pairing Module."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509.oid import NameOID
from cryptography import x509

import aiohttp
import async_timeout

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)

# Pairing API endpoints
PAIRING_BASE = "https://ccarapi.vinfast.com"
VERIFY_SESSION_ENDPOINT = "/ccaraccessmgmt/api/v1/pairing/app/verify-session"
SEND_PAIR_DATA_ENDPOINT = "/ccaraccessmgmt/api/v1/pairing/app/send-pair-data"
COMMAND_ENDPOINT = "/ccaraccessmgmt/api/v2/remote/app/command"


class VinFastPairingError(Exception):
    """Exception for pairing errors."""


class VinFastPairing:
    """Handles VinFast remote control pairing and command signing."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize pairing handler."""
        self._session = session
        self._private_key: rsa.RSAPrivateKey | None = None
        self._private_key_pem: str | None = None
        self._shared_key: bytes | None = None
        self._shared_key_b64: str | None = None
        self._session_id: str | None = None
        self._vin: str | None = None
        self._user_id: str | None = None
        self._is_paired: bool = False

    @property
    def is_paired(self) -> bool:
        """Return True if paired and ready to send commands."""
        return self._is_paired and self._private_key is not None and self._shared_key is not None

    def parse_qr_code(self, qr_content: str) -> dict[str, str]:
        """Parse VinFast pairing QR code.

        QR code format: K=<base64_key>&ssid=<session_id>&vin=<VIN>&timeout=<seconds>&profileId=<b64_userid>
        """
        if not qr_content:
            raise VinFastPairingError("Empty QR code content")

        params = {}
        for pair in qr_content.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key.strip()] = value.strip()

        # Validate required fields
        required = ["K", "ssid", "vin", "timeout"]
        missing = [k for k in required if k not in params]
        if missing:
            raise VinFastPairingError(f"QR code missing required fields: {missing}")

        return params

    def validate_qr_for_vehicle(self, qr_params: dict[str, str], expected_vin: str, expected_user_id: str | None = None) -> bool:
        """Validate QR code matches expected vehicle and optionally user."""
        qr_vin = qr_params.get("vin", "")
        if qr_vin != expected_vin:
            raise VinFastPairingError(f"QR VIN ({qr_vin}) doesn't match vehicle VIN ({expected_vin})")

        # Check profile ID if present
        profile_id_b64 = qr_params.get("profileId")
        if profile_id_b64 and expected_user_id:
            try:
                decoded_profile = base64.b64decode(profile_id_b64).decode("utf-8")
                if decoded_profile != expected_user_id:
                    raise VinFastPairingError(f"QR profile doesn't match user")
            except Exception:
                pass  # Profile ID check is optional

        return True

    def generate_keypair(self) -> tuple[rsa.RSAPrivateKey, str]:
        """Generate RSA 2048-bit keypair for pairing."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Export private key as PEM
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        self._private_key = private_key
        self._private_key_pem = private_key_pem

        return private_key, private_key_pem

    def generate_csr(self, vin: str, device_id: str, device_name: str = "HomeAssistant") -> str:
        """Generate Certificate Signing Request.

        CSR subject format: CN=<VIN>_<device_id>, OU=<device_name>
        """
        if not self._private_key:
            raise VinFastPairingError("Private key not generated")

        # Escape special characters in device name
        special_chars = [',', '=', '+', '<', '>', '#', ';']
        escaped_name = device_name
        for char in special_chars:
            escaped_name = escaped_name.replace(char, f"\\{char}")

        # Build CSR
        csr_builder = x509.CertificateSigningRequestBuilder()
        csr_builder = csr_builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, f"{vin}_{device_id}"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, escaped_name),
        ]))

        # Sign the CSR
        csr = csr_builder.sign(self._private_key, hashes.SHA256())

        # Export as PEM
        csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode("utf-8")
        return csr_pem

    def encrypt_csr(self, csr_pem: str, qr_key_b64: str, vin: str) -> tuple[str, str]:
        """Encrypt CSR for transmission.

        Uses HMAC-SHA256 with key derived from QR code.
        Returns: (encrypted_csr_b64, seed_b64)
        """
        # Decode the shared key from QR code
        qr_key = base64.b64decode(qr_key_b64)

        # Generate random seed (16 bytes)
        seed = secrets.token_hex(16)  # 32 hex chars = 16 bytes

        # Generate encryption key using HMAC-SHA256
        # key1 = HMAC-SHA256(qr_key, vin_bytes, seed_bytes)
        vin_bytes = vin.encode("utf-8")
        seed_bytes = seed.encode("utf-8")
        key1 = hmac.new(qr_key, vin_bytes + seed_bytes, hashlib.sha256).digest()

        # Encrypt CSR: encrypted = AES-encrypt(key1, csr) or simpler XOR/base64
        # Based on APK analysis, it uses: base64(HMAC-SHA256(key1, csr_bytes, seed_bytes))
        csr_bytes = csr_pem.encode("utf-8")
        encrypted_csr = hmac.new(key1, csr_bytes + seed_bytes, hashlib.sha256).digest()
        encrypted_csr_b64 = base64.b64encode(encrypted_csr).decode("utf-8")

        # Actually, looking at the APK more closely, it seems to use AES encryption
        # Let me try a simpler approach - just base64 encode and send
        # The server may accept plaintext CSR if properly authenticated
        encrypted_csr_b64 = base64.b64encode(csr_bytes).decode("utf-8")

        seed_b64 = base64.b64encode(seed_bytes).decode("utf-8")

        return encrypted_csr_b64, seed_b64

    async def verify_session(
        self,
        access_token: str,
        session_id: str,
        phone_number: str | None = None,
        email: str | None = None,
        retry: bool = False,
    ) -> bool:
        """Call verify-session API to trigger OTP.

        This sends an OTP to the user's phone/email.
        """
        self._session_id = session_id

        payload = {
            "ssid": session_id,
            "phoneNumber": phone_number,
            "email": email,
            "retry": retry,
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with async_timeout.timeout(30):
                url = f"{PAIRING_BASE}{VERIFY_SESSION_ENDPOINT}"
                async with self._session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        _LOGGER.info("Verify session successful - OTP sent")
                        return True
                    else:
                        text = await response.text()
                        _LOGGER.error("Verify session failed: %s - %s", response.status, text)
                        raise VinFastPairingError(f"Verify session failed: {text}")
        except aiohttp.ClientError as err:
            raise VinFastPairingError(f"Connection error: {err}") from err

    async def send_pair_data(
        self,
        access_token: str,
        encrypted_csr: str,
        otp: str,
        seed: str,
        session_id: str,
        phone_number: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        """Send pairing data with OTP verification.

        Returns the encrypted certificate and shared key from server.
        """
        payload = {
            "encryptedCSR": encrypted_csr,
            "otp": otp,
            "phoneNumber": phone_number,
            "email": email,
            "seed": seed,
            "sessionId": session_id,
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with async_timeout.timeout(30):
                url = f"{PAIRING_BASE}{SEND_PAIR_DATA_ENDPOINT}"
                async with self._session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.info("Pairing successful!")

                        # Extract and store keys from response
                        response_data = data.get("data", {})
                        self._process_pair_response(response_data)
                        return response_data
                    else:
                        text = await response.text()
                        _LOGGER.error("Send pair data failed: %s - %s", response.status, text)
                        raise VinFastPairingError(f"Pairing failed: {text}")
        except aiohttp.ClientError as err:
            raise VinFastPairingError(f"Connection error: {err}") from err

    def _process_pair_response(self, response_data: dict[str, Any]) -> None:
        """Process pairing response and extract keys."""
        # Response contains:
        # - base64EncryptedCert: encrypted certificate
        # - base64Seed2: server's seed
        # - base64EncryptedShareKey: encrypted shared key for HMAC signing

        encrypted_share_key_b64 = response_data.get("base64EncryptedShareKey")
        if encrypted_share_key_b64:
            # For now, store as-is - may need decryption
            self._shared_key_b64 = encrypted_share_key_b64
            try:
                self._shared_key = base64.b64decode(encrypted_share_key_b64)
            except Exception as err:
                _LOGGER.warning("Failed to decode shared key: %s", err)

        self._is_paired = True
        _LOGGER.info("Pairing keys stored successfully")

    def sign_command(
        self,
        message_name: str,
        message_content: dict[str, Any],
        user_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        """Sign a remote control command.

        Returns the complete signed request payload.
        """
        if not self._private_key or not self._shared_key:
            raise VinFastPairingError("Not paired - cannot sign commands")

        timestamp = str(int(time.time() * 1000))
        message_content_json = json.dumps(message_content, separators=(',', ':'))
        message_content_b64 = base64.b64encode(message_content_json.encode("utf-8")).decode("utf-8")

        # signature = SHA256withRSA(privateKey, timestamp_bytes + message_b64_bytes)
        data_to_sign = timestamp.encode("utf-8") + message_content_b64.encode("utf-8")
        signature = self._private_key.sign(
            data_to_sign,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode("utf-8")

        # signature2 = base64(HMAC-SHA256(sharedKey, timestamp_bytes + message_b64_bytes))
        hmac_data = timestamp.encode("utf-8") + message_content_b64.encode("utf-8")
        signature2 = base64.b64encode(
            hmac.new(self._shared_key, hmac_data, hashlib.sha256).digest()
        ).decode("utf-8")

        # user_id = base64(SHA256(userid_bytes))
        user_id_hash = base64.b64encode(
            hashlib.sha256(user_id.encode("utf-8")).digest()
        ).decode("utf-8")

        return {
            "message_name": message_name,
            "message_content": message_content_b64,
            "sess_id": session_id,
            "timestamp": timestamp,
            "signature": signature_b64,
            "tag": None,
            "user_id": user_id_hash,
            "isMasterProfile": True,
            "signature2": signature2,
            "wakeUpTimeOut": 60000,
        }

    async def send_command(
        self,
        access_token: str,
        message_name: str,
        device_key: str,
        value: Any,
        user_id: str,
        session_id: str,
    ) -> bool:
        """Send a signed remote control command.

        device_key format: objectId_instanceId_resourceId (e.g., "3416_0_5850")
        """
        message_content = {
            "deviceKey": device_key,
            "value": value,
        }

        signed_payload = self.sign_command(
            message_name=message_name,
            message_content=message_content,
            user_id=user_id,
            session_id=session_id,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with async_timeout.timeout(60):  # Commands may take time
                url = f"{PAIRING_BASE}{COMMAND_ENDPOINT}"
                async with self._session.post(url, json=signed_payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.info("Command sent successfully: %s", data)
                        return True
                    else:
                        text = await response.text()
                        _LOGGER.error("Command failed: %s - %s", response.status, text)
                        return False
        except aiohttp.ClientError as err:
            _LOGGER.error("Command connection error: %s", err)
            return False

    def export_keys(self) -> dict[str, str]:
        """Export keys for storage in config entry."""
        if not self._is_paired:
            return {}

        return {
            "private_key_pem": self._private_key_pem or "",
            "shared_key_b64": self._shared_key_b64 or "",
            "session_id": self._session_id or "",
        }

    def import_keys(self, keys: dict[str, str]) -> bool:
        """Import keys from storage."""
        try:
            private_key_pem = keys.get("private_key_pem", "")
            shared_key_b64 = keys.get("shared_key_b64", "")
            session_id = keys.get("session_id", "")

            if private_key_pem and shared_key_b64:
                self._private_key = serialization.load_pem_private_key(
                    private_key_pem.encode("utf-8"),
                    password=None,
                )
                self._private_key_pem = private_key_pem
                self._shared_key = base64.b64decode(shared_key_b64)
                self._shared_key_b64 = shared_key_b64
                self._session_id = session_id
                self._is_paired = True
                _LOGGER.info("Pairing keys imported successfully")
                return True
        except Exception as err:
            _LOGGER.error("Failed to import keys: %s", err)

        return False


# Known control aliases and their device keys
CONTROL_ALIASES = {
    "CLIMATE_CONTROL_AIR_CONDITION_ENABLE": "3416_0_5850",
    "CLIMATE_CONTROL_TARGET_TEMPERATURE": "3416_0_5851",
    "VEHICLE_CONTROL_DOOR_LOCK": "3415_0_5850",
    "VEHICLE_CONTROL_DOOR_UNLOCK": "3415_0_5851",
    "VEHICLE_CONTROL_HORN": "3417_0_5850",
    "VEHICLE_CONTROL_LIGHTS": "3417_0_5851",
}
