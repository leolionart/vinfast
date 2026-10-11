# Báo cáo kỹ thuật: Cơ chế xác thực VinFast UAA, Play Integrity & Bài học kinh nghiệm

**Dự án**: VinFast Connected Car (Home Assistant Integration)  
**Thời gian nghiên cứu**: 10-11/10/2026  
**Mục tiêu**: Giải mã luồng xác thực UAA của VinFast, xây dựng công cụ trích xuất bộ tứ thông tin xác thực (`uaa_client_instance_id`, `uaa_timestamp`, `uaa_signature`, `vinfast_private_key`) và tích hợp an toàn vào Home Assistant.

---

## 1. Bối cảnh & Vấn đề gốc của Home Assistant

Trên Home Assistant, integration VinFast mặc định chỉ yêu cầu `email` và `password`. Tuy nhiên, với các dòng xe và bản cập nhật server mới của VinFast (đặc biệt là các xe dùng giao thức EMQX/WAF), integration lập tức báo lỗi:
```text
VinFast [Failsafe]: Chưa đủ thông tin UAA (uaa_client_instance_id, uaa_signature, uaa_timestamp).
HA vẫn khởi động bình thường; vui lòng vào Cài đặt -> Tùy chọn để bổ sung.
```
Khi thiếu 4 thông số UAA này:
- Không thể quy đổi token CCP thông qua endpoint `/ccaruaa/oauth/token` (grant_type=app).
- Không thể ký header bảo mật WAF (`X-HASH`) cho các request telemetry hoặc điều khiển từ xa.
- Endpoint `POST /ccaraccessmgmt/api/v1/telemetry/app/ping` sẽ trả `403 Unauthorized` hoặc integration rơi vào trạng thái ngủ đông (không nhận được toạ độ, SOC pin, ODO).

---

## 2. Giải mã giao thức từ APK VinFast Companion (v2.26.11)

Bằng cách trích xuất APK gốc và dịch ngược mã nguồn (`AuthInternalApi.java`, `LoginRepositoryProvider.java`, `SecureClient.java`, `TokenInterceptor.java`, `ExchangeTokenInterceptor.java`), toàn bộ quy trình sinh UAA đã được làm rõ:

```text
[Auth0 Login]
      │  POST /oauth/token (grant_type=password, client_id, audience=API_BASE)
      ▼
[Auth0 Access Token] (~1050 ký tự)
      │
      ├───────────────────────────────┐
      ▼                               ▼
[GET /client/challenge]        [Sinh khoá RSA-2048]
      │ (Trả về nonceRegister)        │ (SPKI Base64 = osPublicKey)
      └──────────────┬────────────────┘
                     ▼
           [playNonce = sha256_hex(nonceRegister + osPublicKey)]
                     │
                     ▼
           [Play Integrity Token] (Google Play Services / Play Core)
                     │
                     ▼
           [POST /client/register]
           Body: {"integrityToken", "nonceRegister", "osPublicKey"}
                     │
                     ▼
           [clientInstanceId] (UUID 36 ký tự)
                     │
                     ├───────────────────────────────┐
                     ▼                               ▼
           [timestamp (millis)]            [Ký số RSA-SHA256]
                     │                     sig = Base64(Sign(sha256_hex(cid + ts)))
                     └──────────────┬────────────────┘
                                    ▼
           [POST /ccaruaa/oauth/token]
           Body Form: grant_type=app & timestamp & clientInstanceId & signature
           Header: Authorization: Basic Y2FwcDhPWFdEOWJGYkdpRkc6YnFGZ2pLQ0I2U0pqZ0w3bQ==
                                    │
                                    ▼
           [CCP Token] (Dùng cho toàn bộ API xe & Telemetry)
```

### Chi tiết các endpoint & định dạng dữ liệu:

1. **Auth0 Authentication**:
   - `POST https://vin3s.au.auth0.com/oauth/token`
   - Payload JSON:
     ```json
     {
       "grant_type": "password",
       "client_id": "jE5xt50qC7oIh1f32qMzA6hGznIU5mgH",
       "audience": "https://mobile.connected-car.vinfast.vn",
       "username": "<email>",
       "password": "<password>"
     }
     ```
   - Headers: `Content-Type: application/json`, `X-APP-VERSION: 2.26.11`.
   - Trả về: `access_token` Auth0 (dùng tạm cho challenge và register).

2. **Device Challenge**:
   - `GET https://mobile.connected-car.vinfast.vn/ccaruaa/api/v1/auth/client/challenge`
   - Headers: `Authorization: Bearer <auth0_token>`, `X-Device-Identifier: <app_ssaid>`.
   - Trả về:
     ```json
     {
       "code": 200000,
       "message": "Success",
       "data": { "value": "a9579892-7b8d-40cc-a4ec-2cc7da2036d5" }
     }
     ```
   - Giá trị `value` chính là `nonceRegister`.

3. **Thuật toán tính toán Nonce cho Play Integrity**:
   - Khởi tạo cặp khoá RSA 2048-bit tạm thời trong bộ nhớ RAM.
   - `osPublicKey`: Chuỗi Base64 của SubjectPublicKeyInfo (SPKI) dạng DER (`Base64.encodeToString(key.getEncoded(), 2)`), độ dài 392 ký tự.
   - `playNonce`: Băm SHA-256 của chuỗi ghép `nonceRegister + osPublicKey`, xuất dạng **hexadecimal viết thường** (độ dài 64 ký tự hex).
   - *(Lưu ý: Tham số trong mã nguồn app được đặt tên là `nonceBase64`, nhưng thực tế phương thức `SecureClient.d()` trả về chuỗi Hex SHA-256).*

4. **Yêu cầu Play Integrity Token**:
   - Gọi trực tiếp qua Google Play Core Integrity API:
     ```java
     IntegrityManager mgr = IntegrityManagerFactory.create(appContext);
     IntegrityTokenRequest req = IntegrityTokenRequest.builder().setNonce(playNonce).build();
     mgr.requestIntegrityToken(req);
     ```
   - Không cần thiết lập Cloud Project Number (Play Services tự động liên kết với project mặc định của app VinFast trên Play Console).
   - Kết quả trả về là một chuỗi JWE (~1300 ký tự).

5. **Đăng ký thiết bị (Client Registration)**:
   - `POST https://mobile.connected-car.vinfast.vn/ccaruaa/api/v1/auth/client/register`
   - Headers: `Authorization: Bearer <auth0_token>`, `Content-Type: application/json; charset=UTF-8`, các header định danh thiết bị (`X-Device-Identifier`, `X-APP-VERSION`, etc.).
   - Body JSON:
     ```json
     {
       "integrityToken": "<jwe_token>",
       "nonceRegister": "<nonceRegister>",
       "osPublicKey": "<osPublicKey>"
     }
     ```
   - Trả về:
     ```json
     {
       "code": 200000,
       "message": "Success",
       "data": { "clientInstanceId": "e08462f7-b6d6-4027-ae37-e4a7670a1eea" }
     }
     ```

6. **Chữ ký UAA & Trao đổi Token CCP**:
   - Lấy `timestamp` hiện tại theo epoch milliseconds (`System.currentTimeMillis()`).
   - Chuỗi cần ký: Băm SHA-256 hex của chuỗi `clientInstanceId + timestamp`.
   - `signature`: Ký số chuỗi hex trên bằng thuật toán `SHA256withRSA` (PKCS#1 v1.5 padding) sử dụng Private Key tương ứng của `osPublicKey`, xuất kết quả ra Base64.
   - `POST https://mobile.connected-car.vinfast.vn/ccaruaa/oauth/token`
   - Headers:
     ```http
     Authorization: Basic Y2FwcDhPWFdEOWJGYkdpRkc6YnFGZ2pLQ0I2U0pqZ0w3bQ==
     Content-Type: application/x-www-form-urlencoded
     X-TIMESTAMP: <timestamp>
     ```
   - Body Form:
     ```text
     grant_type=app&timestamp=<timestamp>&clientInstanceId=<clientInstanceId>&signature=<signature>
     ```
   - Trả về: `access_token` (CCP Token).

7. **Bí mật về `X-Device-Identifier`**:
   - `TokenInterceptor.java` lấy giá trị từ `Settings.Secure.getString(context.getContentResolver(), "android_id")`.
   - **Cảnh báo**: Từ Android 8.0 trở đi, Google phân vùng SSAID (Android ID) theo từng cặp `(Signing Key + User UID)`. 
   - Lệnh `adb shell settings get secure android_id` chỉ trả về SSAID của tiến trình shell (`com.android.shell`). SSAID mà app VinFast nhìn thấy hoàn toàn khác. Do đó bắt buộc phải đọc SSAID từ bên trong tiến trình app VinFast.

---

## 3. Cầu nối Frida Bridge (`tools/harvest_frida/`)

Để tự động hoá toàn bộ quy trình mà không cần phụ thuộc vào module Zygisk ngoài, chúng tôi đã phát triển bộ công cụ Frida Bridge:

- **`frida_mint.js`**: Chạy ngầm bên trong tiến trình app VinFast. Script tự động lấy Application Context, nạp Play Core Integrity classes, gọi API xin token cho nonce tuỳ ý, và bắt kết quả gửi ngược lại qua kênh IPC `send()`.
- **`bridge.py`**: Trình điều khiển phía máy chủ/máy tính giao tiếp với điện thoại qua USB/TCP. Đính kèm vào app VinFast, trích xuất SSAID thực sự của app, và điều phối cấp token Play Integrity trong vòng 1-2 giây.
- **`vinfast_harvest.py`**: Kịch bản chạy dòng lệnh độc lập. Tự động Auth0 -> Challenge -> Tạo RSA -> Sinh Nonce -> Gọi Bridge -> Đăng ký Client -> Ký UAA -> Xuất file cấu hình `harvest_result.json` chứa đủ 4 trường UAA.
- **`run_hook.py` & `frida_hook.js`**: Công cụ reverse-engineering chuyên dụng để hook `TokenInterceptor` và `SecureClient`, giám sát gói tin và ép app VinFast chạy lại toàn bộ luồng đăng ký qua cơ chế cache-miss giả lập.

---

## 4. Tại sao Play Integrity thất bại trên máy Android Root / Unlock Bootloader?

Trong quá trình thực nghiệm trên thiết bị Redmi Note 8 Pro (đã unlock bootloader và cài Magisk 27.0), dù Frida Bridge sinh được Play Integrity token thật, lệnh gọi `/client/register` lên máy chủ VinFast luôn bị từ chối với lỗi:
```json
{
  "code": 400905,
  "message": "Invalid integrity token",
  "errors": null
}
```

### Nguyên nhân phần cứng & cơ chế xác thực:
1. **Kiểm tra phần cứng TEE (Keymaster 4.0)**:
   - Dùng công cụ `KeyAttestation` để kiểm tra trực tiếp TEE phần cứng của máy (không qua bất kỳ module hook nào).
   - TEE báo cáo dứt khoát: **`Bootloader is unlocked`**.
   - Mặc dù các thuộc tính hệ thống như `ro.boot.flash.locked=1` và `ro.boot.verifiedbootstate=green` có thể bị các module giả mạo ở tầng user-space, chứng thư TEE phần cứng vẫn chứa cờ `rootOfTrust.deviceLocked = false`.
2. **Tiêu chuẩn kiểm duyệt của máy chủ VinFast**:
   - Máy chủ VinFast gửi token lên Google để kiểm tra và bắt buộc phải có chứng chỉ **`MEETS_DEVICE_INTEGRITY`**.
   - Khi thiết bị bị unlock bootloader, Google chỉ cấp mức **`MEETS_BASIC_INTEGRITY`** (hoặc `UNRECOGNIZED_VERSION`). Máy chủ VinFast kiểm tra cờ này và lập tức trả về lỗi `400905`.
3. **Thất bại của các module giả mạo (TrickyStore, IntegrityBox, ZygiskNext)**:
   - **TrickyStore (Software Mode)**: TrickyStore chuyển attestation sang dùng keybox phần mềm (`DeviceID="sw"`). Kết quả là chuỗi chứng chỉ bị biến thành `AOSP software attestation root certificate`. Máy chủ Google phát hiện thiết bị có TEE phần cứng nhưng lại dùng chứng chỉ phần mềm nên đánh trượt `DEVICE_INTEGRITY`.
   - **Keybox phần cứng bị thu hồi (Revocation List)**: Để có `DEVICE_INTEGRITY`, TrickyStore cần một file `keybox.xml` phần cứng hợp lệ. Chúng tôi đã quét và đối chiếu hơn 15 keybox phần cứng rò rỉ công khai trên GitHub với danh sách thu hồi của Google (`https://android.googleapis.com/attestation/status`, danh sách đen hơn 1700 chứng chỉ). Toàn bộ các keybox công khai hiện nay đều đã bị Google thu hồi phía server.
   - **IntegrityBox (Local Spoofing)**: Chế độ `spoofProvider` của IntegrityBox chỉ sinh ra token giả lập nội bộ (~938 ký tự) để đánh lừa các ứng dụng kiểm tra offline. Khi gửi lên server VinFast (server xác thực online với Google), chữ ký token bị từ chối ngay lập tức.
   - **Kết luận quy luật an ninh**: Không có bất kỳ module Magisk hay thủ thuật phần mềm nào có thể "un-revoke" một khoá mật mã đã bị Google đưa vào danh sách đen ở máy chủ.

---

## 5. Kết luận & Hướng đi bền vững

1. **Khái niệm Harvest**: Quy trình Harvest UAA và khoá RSA chỉ cần thực hiện **một lần duy nhất** trên một thiết bị hợp lệ (hoặc thiết bị có keybox xịn chưa bị thu hồi). Sau khi có được `uaa_client_instance_id`, `uaa_timestamp`, `uaa_signature` và `vinfast_private_key`, các thông số này có thể lưu trữ và tái sử dụng lâu dài trên Home Assistant mà không cần điện thoại phải online liên tục.
2. **Duy trì quyền Telemetry (Grant Renewal)**: 
   - Sau khi Home Assistant đã có bộ UAA, quyền gọi `telemetry/app/ping` sẽ gắn với phiên đăng nhập của app trên điện thoại.
   - Khi grant hết hạn, giải pháp chuẩn xác nhất là dùng script tự động hoá ADB (`tools/upstream_tools/vf_grant_renew_app.py`) để điều khiển app VinFast đăng nhập lại trên máy điện thoại phụ, duy trì phiên mà không cần can thiệp Play Integrity nữa.
