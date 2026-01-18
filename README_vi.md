# VinFast Connected Car cho Home Assistant

![VinFast Logo](images/logo.png)

Component tùy chỉnh này tích hợp xe **VinFast** vào Home Assistant, cho phép bạn theo dõi trạng thái xe, bao gồm mức pin, quãng đường di chuyển, áp suất lốp và nhiều thông tin khác.

> **Lưu ý**: Tích hợp này chỉ tập trung vào việc theo dõi trạng thái xe thông qua API của ứng dụng VinFast. Nó không bao gồm các tính năng OCPP/Trạm sạc.

## Các Dòng Xe Được Hỗ Trợ

- **VF e34**
- **VF 3**
- **VF 5**
- **VF 6**
- **VF 7**
- **VF 8**
- **VF 9**

## 🏁 Hướng Dẫn Cho Người Mới Bắt Đầu: Cài Đặt Dashboard

Nếu bạn là người mới sử dụng Home Assistant, hãy làm theo các bước sau để thiết lập một bảng điều khiển (dashboard) đẹp mắt cho xe VinFast của bạn.

### Bước 1: Cài Đặt Các Yêu Cầu Cần Thiết

Trước khi chạy script cài đặt, bạn cần cài đặt một số thứ sau:

1.  **"Terminal & SSH" Add-on** (Để chạy lệnh cài đặt):
    *   Truy cập **Settings (Cài đặt) > Add-ons > Add-on Store**.
    *   Tìm kiếm **"Terminal & SSH"**.
    *   Nhấn **Install (Cài đặt)** sau đó nhấn **Start (Khởi động)**.
    *   *Mẹo: Bật "Show in sidebar" (Hiển thị ở thanh bên) để dễ dàng truy cập.*

2.  **Cài Đặt HACS** (Nếu bạn chưa có):
    *   **Yêu cầu**: Bạn cần có tài khoản GitHub. [Đăng ký tại đây](https://github.com/join) nếu chưa có.
    *   Mở **Terminal** vừa cài đặt ở bước 1.
    *   Gõ lệnh sau và nhấn Enter:
        ```bash
        wget -O - https://get.hacs.xyz | bash
        ```
    *   Sau khi chạy xong, hãy **Khởi động lại Home Assistant**.
    *   Sau khi khởi động lại, vào **Settings > Devices & Services > Add Integration**, tìm kiếm "HACS".
    *   Tích chọn tất cả các ô xác nhận và nhấn Submit.
    *   Copy mã code hiển thị, nhấn vào link GitHub, đăng nhập và cấp quyền (Authorize) cho HACS.
    *   Xong! HACS đã được cài đặt (bạn có thể cần xóa cache trình duyệt nếu chưa thấy nó hiện ở thanh bên).

3.  **Cài Đặt VinFast Plugin** (Đây là bước quan trọng nhất):
    *   Mở **HACS** trong Home Assistant.
    *   Chọn **Integrations**.
    *   Nhấn dấu 3 chấm góc trên phải > **Custom repositories**.
    *   Dán link kho lưu trữ này vào: `https://github.com/leolionart/vinfast`
    *   Chọn category là **Integration**.
    *   Nhấn **Add**.
    *   Sau đó tìm "VinFast Connected Car" trong danh sách và nhấn **Download**.
    *   Khởi động lại Home Assistant.

4.  **Custom Cards** (Qua HACS - Bắt buộc để dashboard hiển thị đúng):
    *   Truy cập **HACS > Frontend**.
    *   Nhấn **+ Explore & Download Repositories**.
    *   Tìm kiếm và cài đặt 3 card sau:
        1.  `button-card`
        2.  `layout-card`
        3.  `card-mod`
    *   **Khởi động lại Home Assistant** lần nữa sau khi cài xong.

### Bước 2: Chạy Trình Cài Đặt Tự Động (Wizard)

Bây giờ chúng ta sẽ chạy một đoạn mã đơn giản để tự động viết code cho dashboard.

1.  Mở **Terminal** (từ thanh bên hoặc menu Add-ons).
2.  Gõ lệnh sau để đi đến thư mục plugin:
    ```bash
    cd /config/custom_components/vinfast
    ```
3.  Chạy trình cài đặt:
    ```bash
    python3 setup_dashboard.py
    ```
4.  **Làm theo các hướng dẫn trên màn hình:**
    *   **Entity Prefix**: Nhập tiền tố entity của bạn. (ví dụ: nếu cảm biến của bạn là `sensor.vf8_battery`, hãy gõ `vf8`).
    *   **Choice (Lựa chọn)**: Gõ `1` cho Dashboard Full (Wall Panel) hoặc `2` cho Card Đơn giản.

### Bước 2: Chạy Trình Cài Đặt Tự Động (Wizard)

Bây giờ chúng ta sẽ chạy một đoạn mã đơn giản để tự động viết code cho dashboard.

1.  Mở **Terminal** (từ thanh bên hoặc menu Add-ons).
2.  Gõ lệnh sau để đi đến thư mục plugin:
    ```bash
    cd /config/custom_components/vinfast
    ```
3.  Chạy trình cài đặt:
    ```bash
    python3 setup_dashboard.py
    ```
4.  **Làm theo các hướng dẫn trên màn hình:**
    *   **Entity Prefix**: Nhập tiền tố entity của bạn. (ví dụ: nếu cảm biến của bạn là `sensor.vf8_battery`, hãy gõ `vf8`).
    *   **Choice (Lựa chọn)**: Gõ `1` cho Dashboard Full (Wall Panel) hoặc `2` cho Card Đơn giản.

### Bước 3: Thêm Vào Dashboard

1.  Script sẽ thông báo đã lưu một file (ví dụ: `my_vinfast_dashboard.yaml`).
2.  Mở file đó ra (bạn có thể dùng add-on **File Editor**) và copy toàn bộ nội dung.
3.  Đi đến **Dashboard** của bạn.
4.  Nhấn **Edit Dashboard** (biểu tượng cây bút).
5.  **Dành cho Card Đơn giản**: Nhấn **Add Card** > Kéo xuống chọn **Manual** > Dán nội dung đã copy vào.
6.  **Dành cho Wall Panel**: Nhấn vào dấu 3 chấm góc trên cùng > **Raw Configuration Editor** (nếu muốn thay thế toàn bộ giao diện), HOẶC tạo một View mới và chọn chế độ "Panel".

## Cài Đặt qua HACS

1. Mở **HACS** trong Home Assistant.
2. Vào mục **Integrations**.
3. Nhấn vào dấu 3 chấm ở góc trên bên phải và chọn **Custom repositories**.
4. Dán đường dẫn của repository này vào.
5. Chọn **Integration** ở mục category.
6. Nhấn **Add** và sau đó cài đặt "VinFast Connected Car".
7. Khởi động lại Home Assistant.

## Cấu Hình

1. Đi tới **Settings > Devices & Services**.
2. Nhấn **Add Integration** và tìm kiếm **VinFast**.
3. Nhập thông tin tài khoản VinFast (email và mật khẩu) và chọn khu vực (region).
4. Xe của bạn sẽ được tìm thấy và thêm vào như các thiết bị (devices).

## Tùy Chọn Dashboard

### Lựa chọn 1: Full Wall Panel Dashboard

Một dashboard phong cách glassmorphism trong suốt, tuyệt đẹp, hoàn hảo cho máy tính bảng gắn tường.

* Chạy lệnh `python3 setup_dashboard.py` và chọn Option 1.
* Yêu cầu cài đặt `button-card`, `layout-card`, và `card-mod` từ HACS.

### Lựa chọn 2: Simple Card (Card Đơn giản)

![VinFast Card](https://storage.googleapis.com/prod-omniagent/images/Image-518x752-20260117-032430.png)

Một thẻ (card) tổng hợp đầy đủ thông tin để thêm vào dashboard hiện có của bạn.

* Chạy lệnh `python3 setup_dashboard.py` và chọn Option 2.

- **Sensors**: Pin, Quãng đường, Trạng thái sạc, ODO, Áp suất lốp, Nhiệt độ, v.v.
- **Binary Sensors**: Cửa, Khóa, Cốp xe, Nắp capo.
- **Switch**: Điều khiển điều hòa (Yêu cầu ghép nối/pairing).

## Bản quyền

Dựa trên công việc của cộng đồng chủ xe VinFast.
