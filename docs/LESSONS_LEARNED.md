# Lỗi đã mắc & quy tắc phòng ngừa

Ghi lại từ phiên làm việc 2026-10-10 (VinFast VF6/VF3 + OnePlus 6T).
Mỗi mục: **triệu chứng → nguyên nhân → quy tắc**.

---

## A. Thao tác phá hoại (nghiêm trọng nhất)

### A1. `Remove-Item -Include` xoá sạch gói staged
**Triệu chứng:** toàn bộ `vinfast_iot_provider_share_2.9.56\` còn **0 file**; lệnh chỉ
định xoá file `.bak` nhưng xoá hết.
**Nguyên nhân:** `Get-ChildItem -LiteralPath <dir> -Recurse -File -Include '*.bak*'` —
`-Include` **không hoạt động đúng với `-LiteralPath`**, nên nó trả về **mọi file**;
ống dẫn sang `Remove-Item` xoá tất.
**Hậu quả:** mất component staged, 6 tài liệu, mọi file trong gói. Khôi phục được nhờ
component trên Pi + zip cũ, nhưng tốn thời gian và suýt mất việc.
**Quy tắc:**
1. **Không bao giờ** dùng `-Include`/`-Exclude` với `-LiteralPath`. Dùng `-Filter`
   (một mẫu) hoặc `Where-Object`:
   ```powershell
   Get-ChildItem -LiteralPath $dir -Recurse -File |
       Where-Object { $_.Name -like '*.bak*' } | Remove-Item
   ```
2. **Trước mọi lệnh xoá/ghi đè**: in `Resolve-Path` của đích **và** danh sách file sắp
   bị tác động, rồi mới chạy.
3. Thao tác phá hoại thì chạy thử ở thư mục tạm trước.
4. Giữ **bản sao ngoài thư mục đang sửa** (zip theo mốc) trước khi dọn dẹp.

### A2. Xoá proxy Android không sạch → app mất mạng
**Triệu chứng:** app VinFast báo *"Vui lòng kiểm tra kết nối mạng và thử lại"* dù WiFi
tốt, `curl` từ điện thoại vẫn chạy.
**Nguyên nhân:** chỉ xoá `http_proxy`, còn sót `global_http_proxy_host` /
`global_http_proxy_port` trỏ về `192.168.100.246:8082` (mitmdump đã tắt) → mọi request
của app đi vào proxy chết.
**Bằng chứng:** `okhttp: proxySelectEnd: [HTTP @ 192.168.100.246/<unresolved>:8082]`
→ `connectFailed`.
**Quy tắc — xoá đủ 5 khoá:**
```bash
settings delete global http_proxy
settings delete global global_http_proxy_host
settings delete global global_http_proxy_port
settings delete global global_http_proxy_exclusion_list
settings delete global global_proxy_pac_url
```
Nghiệm thu bằng **log của app**, không chỉ `settings get`.

### A3. Để lại trạng thái tạm trên điện thoại
**Quy tắc:** script đụng vào điện thoại phải có **khối dọn dẹp ở cuối** (IME gốc,
proxy) và in ra trạng thái sau khi dọn.

---

## B. Chẩn đoán sai nguyên nhân

### B1. Tin comment có sẵn trong code là sự thật
**Triệu chứng:** nhiều tháng tin `telemetry/app/ping` trả 403 nghĩa là "TCU đang ngủ".
**Thực tế:** 403 do **`X-Device-Identifier` sai** — cùng token, cùng body, chỉ đổi
device id → 200.
**Quy tắc:** coi comment/giả định cũ là **giả thuyết cần kiểm chứng**; dựng thí nghiệm
chỉ đổi **một** biến.

### B2. Kết luận "đã sửa xong" sau một lần thử thành công
**Triệu chứng:** ping 200 lúc 14:17 → tuyên bố xong; 15:38 lại 403.
**Thực tế:** grant có TTL ≈ 15 phút, gắn với phiên đăng nhập app.
**Quy tắc:** đo lại sau ≥30 phút, hoặc ghi rõ điều kiện đi kèm.

### B3. Coi HTTP 200 là bằng chứng có tác dụng
**Triệu chứng:** `POST /ccaraccessmgmt/api/v1/remote/app/wakeup` → `200 Success`, kết
luận xe đã thức. Thực tế không có dữ liệu nào về.
**Quy tắc:** định nghĩa **kết quả quan sát được** trước khi sửa.

### B4. Suy kiểu dữ liệu từ DTO *response*
**Thực tế:** DTO đó là response; app gửi **chuỗi** (`"34183"`).
**Quy tắc:** kiểu của **request** lấy từ request DTO hoặc gói tin bắt được.

### B5. Kết luận thiếu tính năng chỉ vì grep không thấy
**Thực tế:** `sota/current-package`, `noti is-unread` có sẵn, nhưng path nằm trong
**hằng số** nên regex tìm literal không khớp.
**Quy tắc:** grep cả hằng số path; loại trừ `backups/`, `__pycache__`, `test/`.

### B6. Kiểm tra cấu trúc mà không kiểm tra ngữ nghĩa
**Triệu chứng:** `standard=True` báo bản `const.py` xuất ra "đạt chuẩn", nhưng
`CONF_UAA_CLIENT_INSTANCE_ID` đã bị ghi đè thành giá trị UAA.
**Nguyên nhân:** hàm so sánh chỉ bỏ dòng động rồi so **văn bản**, không kiểm tra từng
hằng số có **giá trị đúng** không.
**Quy tắc:** bài kiểm tra phải khẳng định **giá trị kỳ vọng của từng trường**.

---

## C. Lỗi kỹ thuật cụ thể

### C1. Regex thay thế không neo → ghi đè nhầm
**Triệu chứng:** `render_const()` ghi giá trị UAA đè lên `CONF_UAA_*` vì mẫu
`(UAA_CLIENT_INSTANCE_ID\s*=\s*")` khớp cả `CONF_UAA_CLIENT_INSTANCE_ID`.
**Quy tắc:** chặn tiền tố (`(?<![A-Za-z0-9_])`), neo đầu dòng (`^(?m)`), và **`count=1`**.

### C2. Di chuyển khối code làm sai phạm vi biến
**Triệu chứng:** `name '_rc' is not defined` — `_rc` tính trong `_setup_emqx()` nhưng
dùng ở ngoài.
**Nguyên nhân:** vá bằng "chèn thêm" mà không xoá khối cũ; mẫu `old_string` không khớp
nên **câm lặng bỏ qua**.
**Quy tắc:** sau mỗi lần vá, **grep lại** đúng token liên quan; coi cảnh báo "không khớp
mẫu" là **lỗi**, không phải thông tin.

### C3. Đoán offset lệnh DEX bằng cách cộng độ dài
**Triệu chứng:** offset `const/16 v14,128` bị lệch; byte đọc được `0x12` thay vì `0x13`.
**Quy tắc:** dùng **mẫu byte + ngữ cảnh lệnh kế tiếp**, và `assert` trước khi ghi.

### C4. Vá DEX mà không tính lại checksum/signature
```
signature (SHA-1)  = sha1(raw[32:])      -> ghi raw[12:32]
checksum (Adler32) = adler32(raw[12:])   -> ghi raw[8:12]
```
rồi **parse lại bằng androguard** để xác nhận.

### C5. Sửa file bằng mỏ neo quá ngắn
**Triệu chứng:** vô tình xoá docstring của `parse_battery_leasing`.
**Quy tắc:** mỏ neo phải **duy nhất và đủ dài**; sau mỗi `edit` đọc lại vùng vừa sửa.

### C6. Giả định HA đã nạp giá trị mới
**Quy tắc:** ghi log giá trị đang dùng ngay tại nhánh code sử dụng nó (`[CONST-SYNC]`).

### C7. `device_class: timestamp` nhưng giá trị là chuỗi
**Triệu chứng:** `ValueError: Invalid datetime: ... provides state
2026-12-18T17:00:00+00:00:<class 'str'>`.
**Nguyên nhân:** parser trả chuỗi ISO; nhánh cũ chỉ biết đổi epoch thô.
**Quy tắc:** khi đặt `device_class` của HA, bảo đảm kiểu giá trị khớp.

---

## D. Lỗi quy trình

### D1. Nhồi script nhiều dòng qua `ssh "..."`
**Triệu chứng:** hàng chục lần lỗi cú pháp; tốn thời gian cho việc không phải logic.
**Quy tắc:** **viết ra file** (`.sh`/`.py`) → `scp` → chạy. PowerShell nuốt `$_`,
`$(...)` trong chuỗi kép — nên không dùng `ssh "...python3 -c ..."`.

### D2. Giả định adb còn kết nối
**Quy tắc:** đầu mỗi script có `adb connect <ip:port>`; kiểm tra `adb devices`.

### D3. Không nêu tác dụng phụ
**Triệu chứng:** bridge đăng ký lại làm app bị đăng xuất mà không báo trước.
**Quy tắc:** nêu rõ tác dụng phụ và **khôi phục trạng thái ban đầu**.

### D4. Không kiểm tra service sau khi cài
**Triệu chứng:** systemd đánh `failed` vì exit code 1 (một tài khoản ping 403 —
không phải lỗi tiến trình).
**Quy tắc:** exit code phản ánh **tiến trình chạy đúng không**, không phải kết quả
nghiệp vụ từng mục.

---

## Checklist trước khi báo "đã xong"

- [ ] Đã cô lập **một** biến, lặp lại được ≥ 2 lần.
- [ ] Đã đo lại sau ≥ 30 phút, hoặc ghi rõ điều kiện đi kèm.
- [ ] Kết quả nghiệm thu là **dữ liệu quan sát được**, không phải HTTP 200.
- [ ] Bài kiểm tra khẳng định **giá trị từng trường**, không chỉ "khớp mẫu".
- [ ] **Trước mọi lệnh xoá**: đã in `Resolve-Path` + danh sách file sắp bị tác động.
- [ ] Đã khôi phục mọi trạng thái tạm (proxy, IME, app, service).
- [ ] Đã đọc log của hệ thống đích, không chỉ log của script.
- [ ] Đã ghi lại tác dụng phụ và giới hạn.
