# Hướng dẫn nạp cấu hình UAA VinFast & Vận hành Home Assistant

Tài liệu này hướng dẫn cách nạp trực tiếp bộ 4 thông số xác thực UAA vào Home Assistant khi giao diện người dùng không hỗ trợ nhập Private Key hoặc khi gặp lỗi `Failsafe`.

---

## 1. Bộ 4 thông số bắt buộc

Để integration VinFast hoạt động đầy đủ tính năng (đồng bộ dữ liệu xe, vị trí GPS, pin SOC, và điều khiển khoá/mở/điều hoà), mục `options` của config entry VinFast trong Home Assistant cần có đủ:

| Tên trường trong config entry | Kiểu dữ liệu | Ý nghĩa |
| :--- | :--- | :--- |
| `uaa_client_instance_id` | Chuỗi UUID | Mã định danh thiết bị được cấp sau khi `client/register` thành công. |
| `uaa_timestamp` | Chuỗi Epoch ms | Thời điểm tạo chữ ký UAA (ví dụ: `1791682280523`). |
| `uaa_signature` | Chuỗi Base64 | Chữ ký RSA-SHA256 trên chuỗi băm hex của `clientInstanceId + timestamp`. |
| `vinfast_private_key` | Chuỗi PEM | Nội dung khoá riêng tư RSA-2048 (`-----BEGIN PRIVATE KEY----- ...`). |

---

## 2. Kịch bản nạp tự động qua SSH

Do nội dung Private Key dạng PEM có chứa nhiều dòng ngắt (`\n`), việc sao chép thủ công qua terminal dễ bị cắt xén hoặc lỗi cú pháp JSON. Hãy sử dụng phương pháp mã hoá Base64 để truyền tải an toàn:

### Bước 1: Chuẩn bị file dữ liệu
Giả sử bạn đã có file `const.py` (chứa 3 giá trị UAA) và file `vinfast_private.pem` (chứa Private Key).

### Bước 2: Tạo script cập nhật trên máy chủ Home Assistant
Đăng nhập SSH vào máy chủ Home Assistant (hoặc dùng terminal addon), tạo file `/tmp/apply_uaa.py`:

```python
import json
import base64

# Dán chuỗi Base64 của file private key pem vào đây để tránh lỗi ký tự ngắt dòng
B64_PEM = """<CHUỖI_BASE64_CỦA_FILE_PEM>"""
pem_content = base64.b64decode(B64_PEM.strip()).decode('utf-8')

uaa_client_instance_id = "<CLIENT_INSTANCE_ID>"
uaa_timestamp = "<TIMESTAMP>"
uaa_signature = "<SIGNATURE>"

CONFIG_PATH = '/config/.storage/core.config_entries'

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

patched = False
for entry in config.get('data', {}).get('entries', []):
    if entry.get('domain') == 'vinfast':
        if 'options' not in entry or not isinstance(entry['options'], dict):
            entry['options'] = {}
        entry['options']['uaa_client_instance_id'] = uaa_client_instance_id
        entry['options']['uaa_timestamp'] = uaa_timestamp
        entry['options']['uaa_signature'] = uaa_signature
        entry['options']['vinfast_private_key'] = pem_content
        print(f"-> Đã cập nhật entry: {entry.get('entry_id')} ({entry.get('title')})")
        patched = True
        break

if patched:
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("-> Ghi đĩa thành công!")
else:
    print("! Không tìm thấy integration vinfast nào trong config_entries.")
```

### Bước 3: Chạy script và khởi động lại Home Assistant Core
```bash
python3 /tmp/apply_uaa.py
ha core restart
```

---

## 3. Quy trình xác minh sau triển khai

Sau khi Home Assistant Core khởi động lại, kiểm tra log để đảm bảo kết nối thông suốt:

```bash
ha core logs | grep -i vinfast
```

### Dấu hiệu thành công:
1. **Không còn cảnh báo Failsafe**: Không còn xuất hiện dòng `VinFast [Failsafe]: Chưa đủ thông tin UAA...`.
2. **Không có lỗi PEM**: Không xuất hiện `Lỗi đọc Private Key từ cấu hình - Unable to load PEM file`.
3. **Các entity cảm biến cập nhật**: Trên giao diện Lovelace hoặc tab Developer Tools -> States, các entity như `sensor.<tên_xe>_soc`, `sensor.<tên_xe>_odo`, `device_tracker.<tên_xe>` bắt đầu hiển thị dữ liệu hoặc có trạng thái kết nối.

---

## 4. Xử lý sự cố thường gặp (Troubleshooting)

### A. Lỗi `ValueError: Sensor ... has a numeric value; however, it has non-numeric value: 'Không có tín hiệu'`
- **Nguyên nhân**: Khi xe đang đỗ lâu hoặc ECU/TCU đang ngủ sâu, máy chủ VinFast trả về chuỗi text `"Không có tín hiệu"` thay vì giá trị toạ độ số.
- **Ý nghĩa**: Điều này **chứng minh API đã được xác thực thành công** và server đang phản hồi đúng trạng thái của xe.
- **Khắc phục**: Khi xe nổ máy di chuyển hoặc cắm sạc, giá trị số sẽ tự động cập nhật bình thường.

### B. Lỗi `403 Unauthorized` ở endpoint `telemetry/app/ping`
- **Nguyên nhân 1: Xe đang ngủ sâu (TCU Sleep)**:
  - Máy chủ VinFast không thể liên lạc với xe nên trả về 403 (không phải do sai tài khoản).
  - Khắc phục: Gửi lệnh đánh thức TCU bằng cách gọi API:
    ```http
    POST /ccaraccessmgmt/api/v1/remote/app/wakeup
    ```
    (API này gửi request rỗng, không body, có header Bearer CCP Token).
- **Nguyên nhân 2: Hết hạn phiên cấp quyền (Grant Expired)**:
  - Quyền gọi ping gắn liền với một phiên đăng nhập còn hiệu lực của app VinFast trên điện thoại.
  - Khắc phục: Sử dụng script `tools/upstream_tools/vf_grant_renew_app.py` chạy qua ADB để điều khiển điện thoại đăng nhập lại vào app VinFast.
