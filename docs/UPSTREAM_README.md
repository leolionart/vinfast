# VinFast Home Assistant Integration 2.9.56

Bản chia sẻ sạch của custom integration VinFast.

## Nội dung

- `custom_components/vinfast/`: integration Home Assistant.
- `custom_components/vinfast/root_ca_prod.pem`: CA VinFast cho EMQX TLS.
- `www/vinfast-digital-twin.js`: frontend Lovelace.
- `docs/TECHNICAL.md`: kiến trúc, API, MQTT, chuyển provider.
- `tests/provider_smoke.py`: kiểm tra contract offline, không cần Home Assistant.

## Cài đặt

1. Sao lưu `config/custom_components/vinfast/` hiện có.
2. Chép thư mục `custom_components/vinfast/` vào `config/custom_components/`.
3. Chép `www/vinfast-digital-twin.js` vào `config/www/` nếu dashboard đang dùng thẻ này.
4. Cấu hình integration qua UI Home Assistant.
5. Restart Home Assistant.

Không chép credential, token, private key hoặc file debug vào package này. Credentials phải nhập qua Config Flow/Home Assistant.

## Yêu cầu

- Home Assistant hỗ trợ Config Entries.
- `paho-mqtt>=1.6.1`.
- Kết nối HTTPS tới API VinFast.
- Kết nối TCP/TLS EMQX hoặc WSS AWS IoT tùy xe.

## Lưu ý

- Provider được đọc theo đúng `vinCode` từ API `user-vehicle`; không suy luận theo model xe.
- Credentials provider-aware dùng POST. AWS GET chỉ là fallback tương thích server cũ.
- Sau 300 giây không có telemetry, integration thử broker còn lại. Khoảng thử lại tăng dần, tối đa 30 phút, tránh churn khi xe ngủ.
- Chỉ hỗ trợ transport `AWS` và `EMQX`. Provider mới cần bổ sung transport tương ứng.
- Không commit email, VIN, password, token, private key hoặc file `.storage`.

## Kiểm tra nhanh

```powershell
python -m py_compile custom_components/vinfast/*.py
python tests/provider_smoke.py
```

Không paste output chứa JWT/STS lên issue công khai.
