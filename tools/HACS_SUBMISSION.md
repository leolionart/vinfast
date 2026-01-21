# Hướng Dẫn Nộp Plugin Lên HACS Official

Để plugin của bạn xuất hiện trên "Chợ" HACS mặc định (người dùng tìm là thấy, không cần add link thủ công), bạn hãy làm theo các bước sau.

> **Lưu ý**: Tôi đã tạo sẵn file cấu hình tự động kiểm tra (`.github/workflows/hacs.yaml`) cho bạn. File này bắt buộc phải có để HACS chấp nhận.

---

## Bước 1: Chuẩn Bị trên GitHub của bạn

1. **Push code lên GitHub**: Đảm bảo toàn bộ code mới nhất (bao gồm file `.github/workflows/hacs.yaml` tôi vừa tạo) đã được đẩy lên repository GitHub của bạn.
2. **Kiểm tra "Actions"**:
   * Vào tab **Actions** trên trang GitHub repo của bạn.
   * Bạn sẽ thấy một workflow tên là **HACS Action** đang chạy (hoặc đã chạy xong).
   * Đảm bảo nó có **tick xanh lá cây (Success)**. Nếu sai, HACS sẽ từ chối ngay.
3. **Tạo Release Tự Động (One-Click)**:
   * Vào tab **Actions** trên repo GitHub của bạn.
   * Chọn workflow **"Publish New Version"** ở cột bên trái.
   * Bấm nút **Run workflow** (màu xanh bên phải).
   * Chọn loại update: `patch` (sửa lỗi), `minor` (tính năng mới), `major` (thay đổi lớn).
   * Bấm **Run workflow**. Hệ thống sẽ tự tăng số version trong file, tự commit, và tự tạo Release mới cho bạn!

---

## Bước 2: Nộp đơn lên HACS (Tạo Pull Request)

1. Truy cập kho dữ liệu của HACS: **[https://github.cohttps://storage.googleapis.com/prod-omniagent/images/Image-734x319-20260118-023313.pngm/hacs/default](https://github.com/hacs/default)**.
2. Bấm nút **Fork** (góc trên bên phải) để copy kho này về tài khoản của bạn.
3. Sau khi Fork xong, trong kho của bạn:

   * Vào folder `integration` (vì đây là integration, không phải plugin frontend).
   * Bạn sẽ thấy một danh sách rất dài các file `.json`. Đừng hoảng!
   * Bấm phím `.` (dấu chấm) trên bàn phím để mở trình chỉnh sửa web (VS Code for Web) cho dễ, HOẶC bấm **Add file > Create new file**.
   * Tuy nhiên, cách đúng quy định là sửa file `hacs/default` gốc. Nhưng HACS dùng một file danh sách chung.
   * *Đính chính*: Cấu trúc hiện tại của HACS default là một file list json khổng lồ.
   * **Cách đơn giản nhất**:
     1. Tại repo `hacs/default` (bản fork của bạn).
     2. Tìm file có tên đại loại như `data/integration.json` (hoặc kiểm tra file README của họ để biết file nào chứa danh sách). *Thực tế HACS giờ dùng script*.
     3. **Cách chuẩn nhất hiện nay (2024-2025):**
        * Vào link này: **[https://hacs.xyz/docs/publish/include](https://hacs.xyz/docs/publish/include)** (Đọc kỹ hướng dẫn chính chủ).
        * Họ yêu cầu bạn sửa file trong folder tương ứng.
        * Bạn vào folder `integration` trong repo `hacs/default` đã fork.
        * Tạo một file mới tên là `vinfast.json` (trùng với domain của bạn).
        * Dán nội dung sau vào file `vinfast.json` đó:
          ```json
          {
            "name": "VinFast Connected Car",
            "repo": "vinfastownersorg-cyber/vinfastowners"
          }
          ```
          *(Thay `vinfastownersorg-cyber/vinfastowners` bằng `tên-user-github-của-bạn/tên-repo-của-bạn`)*.
4. **Commit & Push**: Lưu file đó lại.
5. **Tạo Pull Request**:

   * Quay lại trang chính repo `hacs/default` của bạn.
   * Bạn sẽ thấy thông báo "This branch is 1 commit ahead of hacs:master".
   * Bấm **Contribute > Open Pull Request**.
   * Điền tiêu đề: `Add vinfast integration`.
   * Trong phần mô tả, tích vào các ô kiểm tra (checklist) xác nhận bạn đã tuân thủ quy định.
   * Bấm **Create Pull Request**.
6. **Chờ đợi**: Bot của HACS sẽ tự động kiểm tra. Nếu mọi thứ (file hacs.json, manifest.json, release, actions) ở repo của bạn đều chuẩn, PR sẽ được merge tự động hoặc bởi admin sau vài giờ/ngày.
