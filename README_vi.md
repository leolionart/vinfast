# VinFast Connected Car cho Home Assistant

![VinFast Logo](images/logo.png)

Component tùy chỉnh này tích hợp xe **VinFast** vào Home Assistant để theo dõi trạng thái xe, lịch sử chuyến đi, thống kê sạc, điều khiển từ xa và giao diện Digital Twin đi kèm.

> **Lưu ý**: Bản hiện tại đã chuyển sang implementation MQTT/WebSocket và custom card đi kèm trong repo. Bộ YAML dashboard cũ không còn được dùng nữa.
>
> Chỉ cần cài từ repo này. Người dùng không cần add thêm repo upstream gốc vào HACS.

## Các Dòng Xe Được Hỗ Trợ

- **VF e34**
- **VF 3**
- **VF 5**
- **VF 6**
- **VF 7**
- **VF 8**
- **VF 9**

## 🏁 Hướng Dẫn Nhanh Cho Người Mới

### Bước 1: Cài các yêu cầu cần thiết

1. **Terminal & SSH** add-on

   * Vào **Settings > Add-ons > Add-on Store**
   * Cài **Terminal & SSH**
   * Bật **Start**
   * Nên bật thêm **Show in sidebar**

2. **HACS**

   * Nếu chưa có HACS, hãy cài trước
   * Khởi động lại Home Assistant sau khi cài

3. **Cài integration này qua HACS**

   * Vào **HACS > Integrations**
   * Chọn **Custom repositories**
   * Thêm repo: `https://github.com/leolionart/vinfast`
   * Category: **Integration**
   * Cài **VinFast Connected Car**
   * Khởi động lại Home Assistant

Nếu trước đó đã từng add một repo `vinfast` khác, hãy gỡ custom repository cũ và uninstall integration cũ trước để Home Assistant không load nhầm bản khác.

### Bước 2: Cấu hình Integration

1. Vào **Settings > Devices & Services**
2. Chọn **Add Integration**
3. Tìm **VinFast**
4. Nhập:

   * Email tài khoản VinFast
   * Mật khẩu
   * Region

5. Nếu muốn bật AI advisor, có thể nhập thêm:

   * **AI Base URL**: ví dụ `https://api.openai.com/v1`
   * **AI API Key**
   * **AI Model**: ví dụ `gpt-4o-mini`

Sau khi cấu hình xong, Home Assistant sẽ sinh entity dạng:

- `sensor.vf8_<vin>_trang_thai_hoat_dong`
- `button.vf8_<vin>_khoa_cua`
- `device_tracker.vf8_<vin>_vi_tri_gps`

## Bước 3: Chạy Wizard cài Frontend

Bản mới đã chứa sẵn custom card trong repo. Wizard này sẽ copy file JS sang `/config/www/vinfast` và tạo sẵn snippet để bạn paste vào Lovelace.

1. Mở **Terminal**
2. Chạy:

```bash
cd /config/custom_components/vinfast
python3 setup_dashboard.py
```

Wizard sẽ:

- Copy `vinfast-digital-twin.js` và `vinfast-debug-card.js` sang `/config/www/vinfast`
- Tự thử dò entity prefix từ Home Assistant
- Sinh ra các file:
  - `my_vinfast_resources.yaml`
  - `my_vinfast_cards.yaml` hoặc `my_vinfast_view.yaml`
  - `my_vinfast_setup_notes.txt`

## Bước 4: Add Lovelace Resources

1. Vào **Settings > Dashboards > Resources**
2. Add 2 resource trong file `my_vinfast_resources.yaml`

Ví dụ:

```yaml
- url: /local/vinfast/vinfast-digital-twin.js?v=...
  type: module
- url: /local/vinfast/vinfast-debug-card.js?v=...
  type: module
```

3. Refresh cứng trình duyệt sau khi add resource

## Bước 5: Add Dashboard

Bạn có 2 cách:

### Cách 1: Tạo hẳn một View riêng

Dùng file `my_vinfast_view.yaml`

### Cách 2: Chèn vào dashboard đang có

Dùng file `my_vinfast_cards.yaml`

Card Digital Twin sẽ tự dò entity xe. Card Debug dùng entity:

```yaml
entity: sensor.<prefix_cua_ban>_system_debug_raw
```

## Tính Năng Chính

- Telemetry thời gian thực qua MQTT/WebSocket
- Button điều khiển từ xa
- Lịch sử chuyến đi và replay route
- Danh sách trạm sạc lân cận
- Thống kê chi phí sạc và hiệu suất
- AI advisor tùy chọn qua API tương thích OpenAI
- Custom card Digital Twin và Debug đi kèm sẵn

## Ghi Chú Về AI

Phần AI là tùy chọn và không ảnh hưởng tới kết nối xe.

Bạn có thể dùng:

- OpenAI
- OpenRouter
- Azure OpenAI-compatible gateway
- Local/self-hosted provider miễn là hỗ trợ `chat/completions`

## Tuyên Bố Miễn Trừ

Dự án này do cộng đồng phát triển và không phải sản phẩm chính thức của VinFast Auto.

Mọi thao tác điều khiển từ xa và truy cập telemetry đều đi qua API nội bộ và backend liên quan của VinFast. Bạn tự chịu trách nhiệm khi sử dụng.
