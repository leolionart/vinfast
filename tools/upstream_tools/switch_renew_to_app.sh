#!/bin/bash
# Cập nhật systemd: dùng gia hạn bằng ĐĂNG NHẬP APP (đúng bản chất)
# thay cho bản đăng ký qua bridge (không tạo được grant).
set -e

SVC=/etc/systemd/system/vinfast-grant-renew.service
TMR=/etc/systemd/system/vinfast-grant-renew.timer

sudo tee "$SVC" >/dev/null <<'EOF'
[Unit]
Description=Gia hạn quyền telemetry/app/ping của VinFast (đăng nhập lại app qua adb)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=pi
Group=pi
WorkingDirectory=/home/pi/vinfast
Environment=VINFAST_ADB=192.168.100.35:5555
ExecStart=/home/pi/vinfast/env/bin/python3 /home/pi/vinfast/vf_grant_renew_app.py --email thaitvad@gmail.com
TimeoutStartSec=600
Nice=10
EOF

sudo tee "$TMR" >/dev/null <<'EOF'
[Unit]
Description=Kiểm tra & gia hạn grant VinFast mỗi 30 phút

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
AccuracySec=1min
Unit=vinfast-grant-renew.service

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now vinfast-grant-renew.timer
sudo systemctl reset-failed vinfast-grant-renew.service 2>/dev/null || true

echo "--- service ---"
systemctl cat vinfast-grant-renew.service | grep ExecStart
echo "--- timer ---"
systemctl list-timers vinfast-grant-renew.timer --no-pager | head -3
echo "--- chạy thử (grant đang tốt nên chỉ kiểm tra, không đăng nhập) ---"
sudo systemctl start vinfast-grant-renew.service
sleep 30
systemctl is-active vinfast-grant-renew.service || true
journalctl -u vinfast-grant-renew.service -n 5 --no-pager -o cat
