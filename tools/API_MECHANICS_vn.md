# Cơ chế hoạt động của VinFast API Integration

Tài liệu này giải thích chi tiết về cách integration này giao tiếp với hệ thống Connected Car của VinFast. Về cơ bản, integration hoạt động bằng cách **giả lập ứng dụng di động VinFast** để lấy dữ liệu.

## 1. Tổng quan kiến trúc

Integration không sử dụng một public API chính thức dành cho bên thứ 3. Thay vào đó, nó đóng vai trò như một "client" (thiết bị di động) hợp lệ:
- **Client Identity**: Tự xưng là `HomeAssistant` nhưng sử dụng các header nhận diện giống ứng dụng thật (ví dụ: `x-service-name: CAPP`).
- **Protocol**: Sử dụng HTTP/HTTPS cho REST API.
- **Data Format**: Dữ liệu xe được trả về dưới dạng cấu trúc **LwM2M** (Lightweight M2M).

## 2. Quy trình Xác thực (Authentication)

Hệ thống sử dụng **Auth0** để quản lý danh tính. Mỗi khu vực (Region) có một server Auth0 riêng biệt.

| Khu vực (Region) | Auth0 Domain | API Base URL |
| :--- | :--- | :--- |
| **Vietnam (VN)** | `vin3s.au.auth0.com` | `https://mobile.connected-car.vinfast.vn` |
| **United States (US)** | `vinfast-us-prod.us.auth0.com` | `https://mobile.connected-car.vinfastauto.us` |
| **Europe (EU)** | `vinfast-eu-prod.eu.auth0.com` | `https://mobile.connected-car.vinfastauto.eu` |

**Các bước xác thực:**
1.  Gửi `username` (email) và `password` tới Auth0 endpoint `/oauth/token`.
2.  Yêu cầu các scopes: `offline_access`, `openid`, `profile`, `email`.
3.  Nhận về `access_token` (dùng cho các request tiếp theo) và `refresh_token` (dùng để lấy access token mới khi hết hạn mà không cần đăng nhập lại).

## 3. Giao thức dữ liệu LwM2M

Dữ liệu của xe VinFast không được lưu dưới dạng JSON keys dễ đọc (như `battery_level`), mà được mã hóa theo chuẩn OMA LwM2M với cấu trúc đường dẫn số:

`/{objectId}/{instanceId}/{resourceId}`

Ví dụ:
- `/34196/0/0`: Mức pin (SOC)
- `/34196/0/1`: Quãng đường còn lại (Range)
- `/34197/0/0`: Trạng thái sạc

### Cơ chế Mapping (Alias)
Để tránh việc phải "đoán" các ID số này (có thể thay đổi tùy dòng xe hoặc bản cập nhật firmware), integration sử dụng endpoint `get-alias`.
- Endpoint này trả về một bản đồ ánh xạ từ **Tên dễ đọc (Alias)** sang **LwM2M Path**.
- Ví dụ: Server trả về `VEHICLE_STATUS_HV_BATTERY_SOC` -> map tới `/34196/0/0`.
- Integration sẽ dùng bản đồ này để gửi request lấy dữ liệu chính xác.

## 4. Các Endpoints Chính

### 4.1. Lấy danh sách xe (`GET /user-vehicle`)
- **Endpoint**: `/ccarusermgnt/api/v1/user-vehicle`
- **Mục đích**: Lấy danh sách các xe gắn với tài khoản. Trả về `vinCode` (số khung) và `userId` (ID người dùng) cần thiết cho các request sau.

### 4.2. Khám phá dữ liệu (`GET /get-alias`)
- **Endpoint**: `/modelmgmt/api/v2/vehicle-model/mobile-app/vehicle/get-alias`
- **Mục đích**: Lấy danh sách các thông số mà xe hỗ trợ và đường dẫn LwM2M tương ứng. Integration sẽ tải bản đồ này khi khởi động.

### 4.3. Lấy dữ liệu xe (`POST /telemetry/app/ping`)
Đây là endpoint quan trọng nhất và khác biệt nhất.
- **Endpoint**: `/ccaraccessmgmt/api/v1/telemetry/app/ping`
- **Cách hoạt động**:
    - Thay vì gọi `GET` để lấy toàn bộ trạng thái, integration gửi `POST` kèm theo **danh sách các ID** mà nó muốn biết.
    - Ví dụ gửi: `[{"objectId": "34196", "resourceId": "0", ...}, ...]`
    - Server trả về giá trị hiện tại của đúng các ID đó.
- **Ưu điểm**: Endpoint này lấy dữ liệu từ cache của server VinFast (hoặc đánh thức xe nhẹ nhàng) nên hoạt động ổn định ngay cả khi xe đang ở chế độ ngủ (sleep).

## 5. Headers Giả lập

Để request được chấp nhận, integration phải gửi kèm các headers đặc thù trong mọi request:

```json
{
    "Authorization": "Bearer <access_token>",
    "x-service-name": "CAPP",
    "x-app-version": "1.10.3",
    "x-device-platform": "HomeAssistant",
    "x-device-family": "Integration",
    "x-device-identifier": "ha-vinfast-integration",
    "x-vin-code": "<số_khung_xe>",
    "x-player-identifier": "<user_id>"
}
```

## 6. Sơ đồ luồng hoạt động

1.  **Init (Khởi tạo)**: Login Auth0 -> Lấy Token.
2.  **Discovery**: Gọi `get-vehicles` -> Lưu VIN & UserID.
3.  **Setup**: Gọi `get-alias` -> Xây dựng bản đồ (Alias Map).
4.  **Polling (Định kỳ)**:
    - Tạo danh sách request objects từ Alias Map.
    - Gọi `telemetry/app/ping`.
    - Map kết quả trả về (LwM2M paths) ngược lại thành tên dễ đọc (Friendly Names).
    - Cập nhật các Sensors trong Home Assistant.
