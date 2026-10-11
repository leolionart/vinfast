# VIRTUAL SENSORS (Dùng chung mọi dòng xe)
VIRTUAL_SENSORS = {
    # --- [dsh] Cảnh báo Waze Mod theo toạ độ xe ---
    "api_waze_status": ("Trạng thái dữ liệu Waze", None, "mdi:database-check-outline", None),
    "api_waze_nearest": ("Cảnh báo Waze gần nhất", None, "mdi:alert-circle-outline", None),
    "api_waze_nearest_m": ("Khoảng cách cảnh báo Waze", "m", "mdi:map-marker-distance", "distance"),
    "api_waze_nearby": ("Số cảnh báo Waze quanh xe", None, "mdi:alert-multiple-outline", None),
    "api_waze_camera_m": ("Khoảng cách camera Waze", "m", "mdi:camera-outline", "distance"),
    # [2.9.57] Đồng bộ từ capture app 2.26.11 — bảo dưỡng, triệu hồi, điểm VinClub.
    "api_next_maintenance_km": ("Bảo dưỡng kế tiếp (ODO)", "km", "mdi:wrench-clock", "distance"),
    "api_next_maintenance_date": ("Ngày bảo dưỡng kế tiếp", None, "mdi:calendar-wrench", "timestamp"),
    "api_recall_count": ("Số chiến dịch triệu hồi", None, "mdi:alert-decagram", None),
    "api_recall_campaigns": ("Chiến dịch triệu hồi", None, "mdi:alert-decagram-outline", None),
    "api_vf_points": ("Điểm VF (VinClub)", "điểm", "mdi:gift", None),
    "api_vinclub_joined": ("Đã tham gia VinClub", None, "mdi:account-star", None),
    "api_vehicle_status": ("Trạng thái hoạt động", None, "mdi:car-info", None),
    "api_current_address": ("Vị trí xe (Địa chỉ)", None, "mdi:map-marker", None),
    "api_trip_distance": ("Quãng đường chuyến đi (Trip)", "km", "mdi:map-marker-distance", "distance"),
    "api_trip_avg_speed": ("Tốc độ TB chuyến đi", "km/h", "mdi:speedometer-medium", "speed"),
    "api_trip_energy_used": ("Điện năng tiêu thụ Trip", "kWh", "mdi:lightning-bolt", "energy"),
    "api_trip_efficiency": ("Hiệu suất tiêu thụ Trip", "kWh/100km", "mdi:leaf-circle", None),
    "api_trip_charge_cost": ("Chi phí sạc chuyến đi", "VNĐ", "mdi:cash-fast", "monetary"),
    "api_static_capacity": ("Dung lượng pin thiết kế", "kWh", "mdi:car-battery", "energy"),
    "api_static_range": ("Quãng đường công bố (Max)", "km", "mdi:map-marker-distance", "distance"),
    "api_soh_calculated": ("Sức khỏe pin (SOH Tính toán)", "%", "mdi:heart-pulse", "battery"),
    "api_battery_degradation": ("Độ chai pin (Theo SOH)", "kWh", "mdi:battery-minus", "energy"),
    "api_est_range_degradation": ("Khả năng chai pin (Theo Range - Tham khảo)", "%", "mdi:battery-alert", None),
    "api_lifetime_efficiency": ("Hiệu suất tiêu thụ (Trung bình xe)", "kWh/100km", "mdi:leaf", None),
    "api_calc_max_range": ("Quãng đường thực tế (Đầy 100% pin)", "km", "mdi:map-marker-path", "distance"),
    "api_calc_remain_range": ("Quãng đường còn lại (Theo hiệu suất)", "km", "mdi:map-marker-distance", "distance"),
    "api_calc_range_per_percent": ("Quãng đường đi được mỗi 1% pin", "km", "mdi:ruler", "distance"),
    "api_best_efficiency_band": ("Dải tốc độ tối ưu nhất", None, "mdi:chart-bell-curve", None),
    "api_last_charge_start_soc": ("% Pin lúc cắm sạc (Lần cuối)", "%", "mdi:battery-arrow-down", "battery"),
    "api_last_charge_end_soc": ("% Pin lúc rút sạc (Lần cuối)", "%", "mdi:battery-arrow-up", "battery"),
    "api_last_charge_duration": ("Thời gian cắm sạc (Lần cuối)", "min", "mdi:timer-sand", "duration"),
    "api_last_charge_energy": ("Điện năng lấy từ lưới (Lần cuối)", "kWh", "mdi:flash", "energy"),
    "api_last_charge_efficiency": ("Hiệu suất sạc thực tế (Lần cuối)", "%", "mdi:car-electric-outline", None),
    "api_last_charge_power": ("Công suất sạc trung bình (Lần cuối)", "kW", "mdi:ev-plug-type2", "power"),
    "api_live_charge_power": ("Công suất sạc hiện tại", "kW", "mdi:flash", "power"),
    "api_daily_distance": ("Quãng đường đi trong ngày", "km", "mdi:map-marker-distance", "distance"),
    "api_daily_energy": ("Năng lượng tiêu thụ trong ngày", "kWh", "mdi:lightning-bolt", "energy"),
    "api_total_charge_cost_est": ("Tổng chi phí sạc quy đổi", "VNĐ", "mdi:cash-fast", "monetary"),

    "api_total_gas_cost": ("Tổng chi phí xăng tương đương", "VNĐ", "mdi:gas-station", "monetary"),
    "api_trip_gas_cost": ("Chi phí xăng chuyến đi", "VNĐ", "mdi:gas-station", "monetary"),
    "api_total_charge_sessions": ("Tổng số lần sạc", "lần", "mdi:battery-charging-100", None),
    "api_public_charge_sessions": ("Số lần sạc tại trạm", "lần", "mdi:ev-station", None),
    "api_home_charge_sessions": ("Số lần sạc tại nhà", "lần", "mdi:home-lightning-bolt-outline", None),
    "api_home_charge_kwh": ("Điện năng sạc tại nhà", "kWh", "mdi:home-battery", "energy"),
    "api_total_energy_charged": ("Tổng điện năng đã sạc", "kWh", "mdi:lightning-bolt", "energy"),
    "api_vehicle_model": ("Tên dòng xe", None, "mdi:car", None),
    "api_vehicle_name": ("Tên định danh xe", None, "mdi:account-car", None),
    "api_outside_temp": ("Nhiệt độ ngoài trời", "°C", "mdi:thermometer", "temperature"),
    "api_weather_condition": ("Thời tiết hiện tại", None, "mdi:weather-partly-cloudy", None),
    "api_hvac_load_estimate": ("Ước tính tải Điều hòa", None, "mdi:air-conditioner", None),
    "api_ai_advisor": ("Cố vấn Xe điện AI", None, "mdi:robot-outline", None),
    "api_vehicle_image": ("Hình ảnh xe URL", None, "mdi:image", None),
    "api_trip_route": ("Lộ trình GPS", None, "mdi:map-marker-path", None),
    "api_nearby_stations": ("Trạm sạc lân cận", None, "mdi:ev-station", None),
    "api_security_warning": ("Cảnh báo An ninh", None, "mdi:shield-alert", None),
    "api_driving_trend_json": ("Dữ liệu Xu hướng lái xe", None, "mdi:chart-bar", None),
    "api_debug_raw": ("System Debug Raw", None, "mdi:bug", None),
    "api_remaining_capacity": ("Dung lượng pin khả dụng", "kWh", "mdi:battery-charging-wireless-outline", "energy"),
    "api_since_charge_distance": ("Quãng đường từ lúc sạc", "km", "mdi:map-marker-distance", "distance"),
    "api_since_charge_energy_used": ("Tiêu thụ từ lúc sạc", "kWh", "mdi:lightning-bolt", "energy"),
    "api_since_charge_efficiency": ("Hiệu suất từ lúc sạc", "kWh/100km", "mdi:leaf-circle", None),
    "api_est_charge_remaining_duration": ("Thời gian sạc còn lại (Tính toán)", "min", "mdi:timer-sand", "duration"),
    "api_est_charge_completion_time": ("Giờ hoàn tất sạc (Tính toán)", None, "mdi:clock-check-outline", "timestamp"),
    "api_adaptive_range": ("Quãng đường còn lại (Thích ứng)", "km", "mdi:map-marker-path", "distance"),
    "api_odo_fallback_estimate": ("Tổng ODO ước tính", "km", "mdi:counter", "distance"),
    "api_odo_fallback_source": ("Nguồn ODO fallback", None, "mdi:database-search", None),
    "api_odo_fallback_estimate": ("Tổng ODO ước tính", "km", "mdi:counter", "distance"),
    "api_odo_fallback_source": ("Nguồn ODO fallback", None, "mdi:database-search", None),
    "api_odo_fallback_estimate": ("Tổng ODO ước tính", "km", "mdi:counter", "distance"),
    "api_odo_fallback_source": ("Nguồn ODO fallback", None, "mdi:database-search", None),
    "api_global_speed_efficiency": ("Hiệu suất Tốc độ Toàn cục", None, "mdi:chart-bar", None),

    # --- API mở rộng (extended_api.py) ---
    "api_profile_name": ("Chủ xe", None, "mdi:account", None),
    "api_profile_phone": ("SĐT chủ xe", None, "mdi:phone", None),
    "api_warranty_end": ("Bảo hành đến", None, "mdi:shield-check", None),
    "api_warranty_start": ("Bảo hành từ", None, "mdi:shield-outline", None),
    "api_warranty_years": ("Số năm bảo hành", "năm", "mdi:calendar-check", None),
    "api_warranty_mileage": ("Giới hạn km bảo hành", "km", "mdi:counter", "distance"),
    "api_drivers_count": ("Số người lái được cấp quyền", "người", "mdi:account-group", None),
    "api_alert_count": ("Số cảnh báo trên xe", "cảnh báo", "mdi:alert-circle-outline", None),
    "api_alert_summary": ("Nội dung cảnh báo", None, "mdi:alert-decagram-outline", None),
    "api_alert_json": ("Chi tiết cảnh báo (JSON)", None, "mdi:clipboard-alert-outline", None),
    "api_thief_state": ("Trạng thái chống trộm", None, "mdi:shield-car", None),
    "api_thief_armed": ("Chuông báo trộm đang bật", None, "mdi:bell-ring", None),
    "api_thief_alert": ("Có sự kiện báo trộm", None, "mdi:alarm-light", None),
    "api_thief_message": ("Nội dung cảnh báo trộm", None, "mdi:message-alert", None),
    "api_noti_unread": ("Có thông báo chưa đọc", None, "mdi:bell-badge", None),
    "api_battery_brand": ("Hãng pin", None, "mdi:car-battery", None),
    "api_battery_cell_balance": ("Cân bằng cell pin", None, "mdi:scale-balance", None),
    "api_battery_lv_status": ("Ắc quy 12V", None, "mdi:battery-outline", None),
    "api_last_charge_time": ("Thời điểm sạc gần nhất", None, "mdi:clock-outline", "timestamp"),
    "api_last_charge_type": ("Kiểu sạc gần nhất", None, "mdi:ev-plug-type2", None),
    "api_last_charge_status": ("Kết quả lần sạc gần nhất", None, "mdi:check-circle-outline", None),
    "api_last_charge_minutes": ("Thời lượng sạc gần nhất", "min", "mdi:timer-sand", "duration"),
    "api_last_charge_peak_power": ("Công suất sạc cao nhất", "kW", "mdi:flash", "power"),
    "api_last_charge_peak_temp": ("Nhiệt độ pin cao nhất", "°C", "mdi:thermometer-high", "temperature"),
    "api_driving_score": ("Điểm lái xe an toàn", "điểm", "mdi:steering", None),
    "api_driving_score_level": ("Xếp hạng lái xe", None, "mdi:medal-outline", None),
    "api_driving_score_json": ("Chi tiết điểm lái xe (JSON)", None, "mdi:chart-timeline-variant", None),
    "api_firmware_update_available": ("Có bản cập nhật firmware", None, "mdi:download-circle-outline", None),
    "api_firmware_in_progress": ("Firmware đang cập nhật", None, "mdi:progress-download", None),
    "api_tbox_version": ("Phiên bản T-Box (SOTA)", None, "mdi:cellphone-link", None),
    "api_sota_package": ("Gói phần mềm hiện tại", None, "mdi:package-variant-closed", None),
    "api_leasing_cost": ("Phí thuê pin tháng này", "VNĐ", "mdi:cash", "monetary"),
    "api_leasing_km": ("Km đi trong kỳ thuê pin", "km", "mdi:map-marker-distance", "distance"),
    "api_leasing_month": ("Kỳ thuê pin", None, "mdi:calendar-month", None),
    "api_leasing_target_soc": ("Target SOC (hợp đồng thuê pin)", "%", "mdi:battery-sync", "battery"),
    "api_parked_images": ("Ảnh vị trí đỗ (JSON)", None, "mdi:image-multiple", None),
    "api_battery_charging_habits": ("Thói quen sạc pin", None, "mdi:chart-donut", None),
    "api_battery_driving_habits": ("Thói quen lái xe", None, "mdi:chart-line", None),
    "api_battery_parking_habits": ("Thói quen đỗ xe", None, "mdi:parking", None),
    "api_profile_id": ("ID tài khoản", None, "mdi:identifier", None),
    "api_profile_email": ("Email tài khoản", None, "mdi:email", None),
    "api_thief_time": ("Thời điểm cảnh báo trộm", None, "mdi:clock-alert-outline", "timestamp"),
    "api_thief_lat": ("Vĩ độ khi báo trộm", "°", "mdi:crosshairs-gps", None),
    "api_thief_lon": ("Kinh độ khi báo trộm", "°", "mdi:crosshairs-gps", None),
    "api_battery_cell_balance_ok": ("Cell pin cân bằng", None, "mdi:check-circle-outline", None),
    "api_last_charge_temp_limit": ("Ngưỡng nhiệt độ pin", "°C", "mdi:thermometer-alert", "temperature"),
    "api_driving_score_period": ("Kỳ tính điểm lái xe", None, "mdi:calendar-range", None),
    "api_firmware_last_ok": ("Firmware cập nhật gần nhất (JSON)", None, "mdi:check-decagram", None),
    "api_sota_product": ("Nhóm sản phẩm SOTA", None, "mdi:package-variant", None),
    "api_leasing_odo_start": ("ODO đầu kỳ thuê pin", "km", "mdi:counter", "distance"),
    "api_leasing_odo_end": ("ODO cuối kỳ thuê pin", "km", "mdi:counter", "distance"),
    "api_leasing_free": ("Kỳ thuê pin miễn phí", None, "mdi:gift-outline", None),
    "api_current_charging_session": ("Phiên sạc hiện tại (JSON)", None, "mdi:ev-station", None),
}

# Ghi đè slug entity_id cho các cảm biến MỚI có tên chứa "Đ/đ".
# HA slugify() chuẩn hoá NFKD rồi bỏ ký tự ngoài ASCII, mà "Đ" không phân rã được
# nên bị xoá hẳn ("Bảo hành đến" -> "bao_hanh_en"). Bảng này chỉ áp cho cảm biến mới,
# KHÔNG đụng tới entity_id cũ để không phá cấu hình Lovelace đang chạy.
SENSOR_SLUG_OVERRIDES = {
    # --- [dsh] Waze ---
    "api_waze_status": "trang_thai_du_lieu_waze",
    "api_waze_nearest": "canh_bao_waze_gan_nhat",
    "api_waze_nearest_m": "khoang_cach_canh_bao_waze",
    "api_waze_nearby": "so_canh_bao_waze_quanh_xe",
    "api_waze_camera_m": "khoang_cach_camera_waze",
    "api_profile_phone": "sdt_chu_xe",
    "api_warranty_end": "bao_hanh_den",
    "api_drivers_count": "so_nguoi_lai_duoc_cap_quyen",
    "api_thief_armed": "chuong_bao_trom_dang_bat",
    "api_thief_alert": "co_su_kien_bao_trom",
    "api_noti_unread": "co_thong_bao_chua_doc",
    "api_last_charge_time": "thoi_diem_sac_gan_nhat",
    "api_last_charge_peak_temp": "nhiet_do_pin_cao_nhat",
    "api_driving_score": "diem_lai_xe_an_toan",
    "api_driving_score_json": "chi_tiet_diem_lai_xe_json",
    "api_firmware_in_progress": "firmware_dang_cap_nhat",
    "api_leasing_km": "km_di_trong_ky_thue_pin",
    "api_leasing_odo_start": "odo_dau_ky_thue_pin",
    "api_battery_parking_habits": "thoi_quen_do_xe",
    "api_parked_images": "anh_vi_tri_do_json",
    "api_thief_time": "thoi_diem_canh_bao_trom",
    "api_thief_lat": "vi_do_khi_bao_trom",
    "api_thief_lon": "kinh_do_khi_bao_trom",
    "api_last_charge_temp_limit": "nguong_nhiet_do_pin",
    "api_driving_score_period": "ky_tinh_diem_lai_xe",
}

# COMMON SENSORS (Tất cả xe VF3, VF5, 6, 7, e34, VF8, VF9 đều có)
COMMON_SENSORS = {
    "00006_00001_00000": ("Vĩ độ (Latitude)", "°", "mdi:crosshairs-gps", None),
    "00006_00001_00001": ("Kinh độ (Longitude)", "°", "mdi:crosshairs-gps", None),
    "00006_00001_00002": ("Độ cao (Altitude)", "m", "mdi:elevation-rise", None),
    "00005_00001_00030": ("Phiên bản Phần mềm (FRP)", None, "mdi:update", None),
    "34196_00001_00004": ("Phiên bản T-Box", None, "mdi:cellphone-link", None),
    "34181_00001_00007": ("Biển số / Tên xe phụ", None, "mdi:card-text-outline", None),
    
    "34213_00001_00003": ("Khóa tổng", None, "mdi:lock", None),
    "34234_00001_00003": ("Trạng thái An ninh", None, "mdi:shield-car", None),
    "34186_00005_00004": ("Đèn nháy cảnh báo", None, "mdi:car-light-alert", None),
    "34205_00001_00001": ("Chế độ Giao xe (Valet)", None, "mdi:account-tie-hat", None),
    "34206_00001_00001": ("Chế độ Cắm trại (Camp)", None, "mdi:tent", None),
    "34207_00001_00001": ("Chế độ Thú cưng (Pet)", None, "mdi:paw", None),

    "10351_00002_00050": ("Cửa tài xế", None, "mdi:car-door", None),
    "10351_00001_00050": ("Cửa phụ", None, "mdi:car-door", None),
    "10351_00006_00050": ("Cốp sau", None, "mdi:car-door", None),
    "10351_00005_00050": ("Nắp Capo", None, "mdi:car-door", None),
    "34215_00002_00002": ("Kính tài xế", None, "mdi:window-open", None),
    "34215_00001_00002": ("Kính phụ", None, "mdi:window-open", None),
    
    "34213_00003_00003": ("Trạng thái Mô-tơ Kính", None, "mdi:car-door-window", None),
    "34213_00002_00003": ("Trạng thái Mô-tơ Cốp", None, "mdi:car-back", None),

    "34213_00004_00003": ("Trạng thái nháy đèn pha", None, "mdi:car-light-high", None),
    "34184_00001_00004": ("Trạng thái điều hòa", None, "mdi:air-conditioner", None),
    "34184_00001_00011": ("Chế độ lấy gió", None, "mdi:car-windshield-outline", None),
    "34184_00001_00012": ("Hướng gió điều hòa", None, "mdi:fan", None),
    "34184_00001_00009": ("Sấy kính", None, "mdi:car-defrost-front", None),
    "34184_00001_00025": ("Mức quạt gió", "Mức", "mdi:fan-speed-1", None),
    "34184_00001_00041": ("Mức độ làm lạnh", "Mức", "mdi:snowflake", None),
}

# LỚP CỘNG THÊM DÀNH CHO XE CÓ 4 CỬA
REAR_DOORS_WINDOWS = {
    "10351_00004_00050": ("Cửa sau tài xế", None, "mdi:car-door", None),
    "10351_00003_00050": ("Cửa sau phụ", None, "mdi:car-door", None),
    "34215_00004_00002": ("Kính sau tài xế", None, "mdi:window-open", None),
    "34215_00003_00002": ("Kính sau phụ", None, "mdi:window-open", None),
}

# PLATFORM A BASE (VF3, VF5, e34, VF6, VF7)
PLATFORM_A_BASE = COMMON_SENSORS.copy()
PLATFORM_A_BASE.update({
    "34183_00001_00009": ("Phần trăm Pin", "%", "mdi:battery", "battery"),
    "34183_00001_00011": ("Quãng đường dự kiến", "km", "mdi:map-marker-distance", "distance"),
    "34183_00001_00001": ("Vị trí cần số", None, "mdi:car-shift-pattern", None),
    "34183_00001_00002": ("Tốc độ hiện tại", "km/h", "mdi:speedometer", "speed"),
    "34183_00001_00003": ("Tổng ODO", "km", "mdi:counter", "distance"),
    "34183_00001_00010": ("Trạng thái Lái (Ready)", None, "mdi:car-key", None), 
    
    "34183_00001_00029": ("Phanh tay điện tử", None, "mdi:car-brake-parking", None),
    "34183_00001_00035": ("Công tắc Phanh chân", None, "mdi:car-brake-fluid-level", None),
    
    "34183_00001_00005": ("Pin 12V (Ắc quy)", "%", "mdi:car-battery", "battery"),
    "34220_00001_00001": ("Sức khỏe pin (SOH)", "%", "mdi:heart-pulse", "battery"),
    
    "34193_00001_00031": ("Cắm súng sạc (Plug)", None, "mdi:ev-plug-type2", None),
    "34193_00001_00005": ("Trạng thái sạc", None, "mdi:ev-station", None), 
    "34193_00001_00007": ("Thời gian sạc còn lại", "min", "mdi:timer-outline", "duration"),
    
    "34193_00001_00026": ("Thời gian sạc ước tính", "min", "mdi:timer-sand", "duration"),
    "34193_00001_00013": ("Giờ hoàn tất sạc dự kiến", None, "mdi:clock-check-outline", None),
    "34193_00001_00032": ("Relay hệ thống sạc", None, "mdi:electric-switch", None),
    "34193_00001_00016": ("Mã phiên sạc (Session ID)", None, "mdi:identifier", None),
    
    "34183_00001_00007": ("Nhiệt độ ngoài trời", "°C", "mdi:thermometer", "temperature"),
    "34183_00001_00015": ("Nhiệt độ trong xe", "°C", "mdi:thermometer", "temperature"),
    "34224_00001_00005": ("Nhiệt độ điều hòa cài đặt", "°C", "mdi:thermostat", "temperature"),
})

# BỘ MÃ CHUYÊN BIỆT CHO NỀN TẢNG A (VF5, VF6, VF7, VF e34)
PLATFORM_VF567_SENSORS = PLATFORM_A_BASE.copy()
PLATFORM_VF567_SENSORS.update(REAR_DOORS_WINDOWS)

# Fix lỗi 2 cảm biến Khóa cửa cùng tồn tại trên VF6
if "34213_00001_00003" in PLATFORM_VF567_SENSORS:
    del PLATFORM_VF567_SENSORS["34213_00001_00003"]

PLATFORM_VF567_SENSORS.update({
    "56789_00001_00005": ("Trạng thái Đèn Pha", None, "mdi:car-light-high", None),
    "34206_00001_00001": ("Khóa tổng", None, "mdi:lock", None), 
})

# PLATFORM B BASE (VF8, VF9)
PLATFORM_B_BASE = COMMON_SENSORS.copy()
PLATFORM_B_BASE.update(REAR_DOORS_WINDOWS) 
PLATFORM_B_BASE.update({
    "34180_00001_00011": ("Phần trăm Pin", "%", "mdi:battery", "battery"),
    "34180_00001_00007": ("Quãng đường dự kiến", "km", "mdi:map-marker-distance", "distance"),
    "34187_00000_00000": ("Vị trí cần số", None, "mdi:car-shift-pattern", None),
    "34188_00000_00000": ("Tốc độ hiện tại", "km/h", "mdi:speedometer", "speed"),
    "34199_00000_00000": ("Tổng ODO", "km", "mdi:counter", "distance"),
    "34180_00001_00010": ("Trạng thái Lái (Ready)", None, "mdi:car-key", None),
    "34181_00000_00000": ("Pin 12V (Ắc quy)", "%", "mdi:car-battery", "battery"),
    
    "34183_00000_00001": ("Trạng thái sạc", None, "mdi:ev-station", None),
    "34183_00000_00004": ("Cắm súng sạc (Plug)", None, "mdi:ev-plug-type2", None),
    "34183_00000_00009": ("Thời gian sạc còn lại", "min", "mdi:timer-outline", "duration"),
    "34183_00000_00012": ("Công suất sạc (Trạm)", "kW", "mdi:flash", "power"),
    
    "34189_00000_00000": ("Nhiệt độ ngoài trời", "°C", "mdi:thermometer", "temperature"),
    "34190_00000_00000": ("Nhiệt độ trong xe", "°C", "mdi:thermometer", "temperature"),
})