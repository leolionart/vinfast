#!/bin/bash
# Cài systemd timer gia hạn grant VinFast (chạy bằng user pi vì adb server thuộc user này)
set -e

SVC=/etc/systemd/system/vinfast-grant-renew.service
TMR=/etc/systemd/system/vinfast-grant-renew.timer

sudo tee "$SVC" >/dev/null <<'EOF'
[Unit]
Description=Gia hạn quyền telemetry/app/ping của VinFast (qua bridge Play Integrity)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=pi
Group=pi
WorkingDirectory=/home/pi/vinfast
Environment=VINFAST_ADB=192.168.100.35:5555
ExecStart=/home/pi/vinfast/env/bin/python3 /home/pi/vinfast/vf_grant_renew.py --quiet
TimeoutStartSec=600
Nice=10
EOF

sudo tee "$TMR" >/dev/null <<'EOF'
[Unit]
Description=Chạy gia hạn grant VinFast mỗi 30 phút

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

echo "--- timer ---"
systemctl list-timers vinfast-grant-renew.timer --no-pager | head -3
echo "--- chạy thử ngay ---"
sudo systemctl start vinfast-grant-renew.service
sleep 45
systemctl is-active vinfast-grant-renew.service
echo "--- log ---"
tail -6 /home/pi/vinfast/vf_grant_renew.log
