# VinFast IoT Provider: Tài liệu kỹ thuật

## 1. Mục tiêu

Integration phải chạy được với nhiều dòng xe, nhiều đời app/server. Provider không được suy luận từ model xe hoặc hard-code theo một tài khoản. Nguồn sự thật là `iotProvider` của đúng VIN do VinFast trả về.

Luồng tổng quát:

```text
Config Flow
  -> Auth0/UAA token
  -> GET /ccarusermgnt/api/v1/user-vehicle
  -> chọn đúng vinCode
  -> đọc iotProvider
  -> POST credentials(provider)
  -> kết nối MQTT AWS hoặc EMQX
  -> nhận telemetry / heartbeat
```

## 2. REST API

Base URL VN hiện tại:

```text
https://mobile.connected-car.vinfast.vn
```

### 2.1 Danh sách xe

```http
GET /ccarusermgnt/api/v1/user-vehicle
Authorization: Bearer <vf-token>
```

Chọn phần tử theo `vinCode` đã cấu hình. Nếu chưa cấu hình VIN, ưu tiên phần tử `isSelected`, sau đó mới dùng phần tử đầu tiên.

Các trường quan trọng:

```json
{
  "vinCode": "<VIN>",
  "marketingName": "VF...",
  "userId": "<account-id>",
  "iotProvider": "AWS"
}
```

`iotProvider` hiện quan sát được: `AWS`, `EMQX`. Giá trị không biết được cảnh báo và chuẩn hóa thành `None`; chưa có connector tương ứng. Khi không có giá trị hỗ trợ lúc khởi động, tầng MQTT vẫn dùng AWS làm mặc định, rồi có thể thử EMQX. Đây không phải hỗ trợ tự động provider mới.

### 2.2 Credentials

Endpoint:

```http
POST /ccarusermgnt/api/v1/auth0/account/client/credentials
Authorization: Bearer <vf-token>
Content-Type: application/json

{"vinCode":"<VIN>","iotProvider":"AWS"}
```

hoặc:

```json
{"vinCode":"<VIN>","iotProvider":"EMQX"}
```

AWS trả STS fields:

```json
{
  "accessKeyId": "<short-lived>",
  "secretKeyId": "<short-lived>",
  "sessionToken": "<short-lived>",
  "expiration": "<ISO-8601>"
}
```

EMQX trả JWT trong `sessionToken`; JWT có `scope=mqttconnection`, `authorities` chứa `ROLE_MQTT_CONNECTION`, và claim VIN. Không log toàn bộ token.

Server cũ có thể không hỗ trợ POST cho AWS. Code chỉ fallback sang:

```http
GET /ccarusermgnt/api/v1/auth0/account/client/credentials
```

GET fallback chỉ dùng khi POST trả `404` hoặc `405`; không dùng GET để quyết định provider.

## 3. MQTT transports

### 3.1 AWS IoT

- Host: `prod.iot.connected-car.vinfast.vn`
- Port: `443`
- Transport: WebSocket Secure (`wss`)
- Authentication: AWS SigV4 presigned URL
- Region hiện tại: `ap-southeast-1`
- Heartbeat resource: `34183/1/54 = "1"`; khi xe di chuyển dùng `"2"`.

### 3.2 EMQX

- Host: `ccp-mqtt.vinfast.vn`
- Port: `8884`
- Transport: MQTT 3.1.1 over TLS
- Username: email đăng nhập
- Password: EMQX JWT từ POST credentials
- CA: `root_ca_prod.pem`
- Heartbeat resource: `34183/1/54 = "CONNECTED"`.

TLS EMQX dùng certificate verification, hostname check, bundled CA và `VERIFY_X509_PARTIAL_CHAIN`. Không vô hiệu hóa TLS verification trong bản chia sẻ.

### 3.3 Topics

Integration subscribe:

```text
/mobile/{VIN}/push
monitoring/server/{VIN}/push
control/server/{VIN}/push
/server/{VIN}/remctrl
```

Heartbeat publish:

```text
/vehicles/{VIN}/push/connected/heartbeat
```

## 4. Chọn provider và fallback

### Khởi động

1. Auth0/UAA hoàn tất.
2. Lấy danh sách xe.
3. Match đúng VIN.
4. Lưu provider server trả về.
5. Lấy credentials theo provider.
6. Kết nối MQTT.

### Refresh server

Mỗi 15 phút, gọi lại `user-vehicle` cho đúng VIN. Nếu server đổi provider, integration ngắt transport cũ và kết nối transport mới. Điều này hỗ trợ migration AWS/EMQX theo từng nhóm xe.

### Không có telemetry

- Sau 300 giây kể từ khi kết nối mà không có MQTT message, thử provider còn lại.
- Sau mỗi lần thử thất bại, tăng thời gian probe: 5, 10, 20, tối đa 30 phút.
- Nhận được message sẽ reset backoff về 5 phút.
- Không chuyển provider chỉ vì model xe hoặc vì credential endpoint trả về AWS GET.
- Xe ngủ có thể không phát telemetry; backoff ngăn việc reconnect liên tục.

## 5. Tương thích server tương lai

Đã xử lý:

- Nhiều VIN trong một account.
- `iotProvider` khác chữ hoa/thường.
- API credentials POST mới và GET AWS cũ.
- Server trả provider chưa biết: log cảnh báo, không silent fallback sai.
- Provider server đổi sau khi integration đang chạy.
- CA VinFast được đóng gói, tránh phụ thuộc trust store hệ điều hành.

Chưa tự động xử lý:

- Provider mới ngoài AWS/EMQX.
- Broker host/port/protocol mới nếu server đổi transport.
- API schema đổi hoàn toàn hoặc endpoint đổi tên.

Khi server thêm provider mới, cần bổ sung ba phần: credential validator, transport connector, heartbeat format; sau đó thêm test integration với dữ liệu giả lập.

## 6. Bảo mật

Không đưa vào bản chia sẻ:

- Password VinFast.
- Auth0/UAA/VF token.
- AWS `accessKeyId`, `secretKeyId`, `sessionToken`.
- EMQX JWT.
- Private key PEM.
- `.storage`, config entries, telemetry raw, log chứa VIN/email.

Private key và UAA là dữ liệu vận hành; nhập qua Home Assistant Config Flow. Nếu token từng bị công khai, revoke/đăng nhập lại trước khi chia sẻ.

## 7. Chẩn đoán

Log cần tìm:

```text
Đang gọi lấy danh sách xe
Khởi tạo kết nối AWS IoT WSS MQTT thành công
Khởi tạo kết nối EMQX MQTT
Provider AWS MQTT đã kết nối
Provider EMQX MQTT đã kết nối
[FALLBACK]
Server đổi provider
```

Không coi `connected` là đủ: phải kiểm tra message telemetry sau khi subscribe. Không có message sau 300 giây mới kích hoạt fallback.

## 8. Kiểm thử release

```bash
python -m py_compile custom_components/vinfast/*.py
python tests/provider_smoke.py
```

Kiểm thử live chỉ dùng account thử nghiệm, không lưu output credential. Kiểm tra tối thiểu:

1. Account/xe `AWS`.
2. Account/xe `EMQX`.
3. Multi-vehicle account với VIN không nằm ở phần tử đầu tiên.
4. API server trả provider khác sau refresh.
5. Xe ngủ: backoff không reconnect liên tục.
6. EMQX TLS: hostname và CA verification thành công.
