import os
import json
import logging
from homeassistant.components.http import HomeAssistantView

_LOGGER = logging.getLogger(__name__)

class VinFastTripsView(HomeAssistantView):
    url = "/api/vinfast/trips"
    name = "api:vinfast:trips"
    requires_auth = True

    def __init__(self, api):
        self.api = api

    async def get(self, request):
        # Lấy hass từ request context để tránh lỗi khi self.hass chưa được inject
        hass = request.app.get("hass") or getattr(self, "hass", None)

        vin = request.query.get("vin")
        if not vin:
            return self.json({"error": "Missing VIN parameter"}, status_code=400)
            
        year = request.query.get("year")
        month = request.query.get("month")
        
        if year and month:
            month_str = str(month).zfill(2)
            file_name = f"vinfast_trips_archive_{vin.lower()}_{year}_{month_str}.json"
        else:
            file_name = f"vinfast_trips_{vin.lower()}.json"
            
        file_path = os.path.join(self.api.storage_dir, file_name)
        if not os.path.exists(file_path):
            return self.json([])
            
        try:
            def read_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            if hass:
                data = await hass.async_add_executor_job(read_file)
            else:
                data = read_file()
            return self.json(data)
        except Exception as e:
            _LOGGER.error(f"VinFast View Error reading trips: {e}")
            return self.json({"error": str(e)}, status_code=500)


class VinFastChargeHistoryView(HomeAssistantView):
    url = "/api/vinfast/charge_history"
    name = "api:vinfast:charge_history"
    requires_auth = True

    def __init__(self, api):
        self.api = api

    async def get(self, request):
        hass = request.app.get("hass") or getattr(self, "hass", None)

        vin = request.query.get("vin")
        if not vin:
            return self.json({"error": "Missing VIN parameter"}, status_code=400)

        want_full = request.query.get("full", "0") == "1"

        file_path = os.path.join(self.api.storage_dir, f"vinfast_charge_history_{vin.lower()}.json")
        if not os.path.exists(file_path):
            return self.json([])

        try:
            def read_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            if hass:
                data = await hass.async_add_executor_job(read_file)
            else:
                data = read_file()

            # Format mới: dict với metadata + sessions
            if isinstance(data, dict) and "sessions" in data:
                sessions = data["sessions"]
                if want_full:
                    # Trả về toàn bộ cache kèm metadata
                    return self.json(data)
                else:
                    # Backward compat: chỉ trả 20 phiên gần nhất dạng list
                    return self.json(sessions[:20])

            # Format cũ: list thuần → backward compat
            if isinstance(data, list):
                return self.json(data)

            return self.json([])
        except Exception as e:
            _LOGGER.error(f"VinFast View Error reading charge history: {e}")
            return self.json({"error": str(e)}, status_code=500)



class VinFastChangelogView(HomeAssistantView):
    url = "/api/vinfast/changelog"
    name = "api:vinfast:changelog"
    requires_auth = True

    def __init__(self, api):
        self.api = api

    async def get(self, request):
        hass = request.app.get("hass") or getattr(self, "hass", None)

        vin = request.query.get("vin")
        if not vin:
            return self.json({"error": "Missing VIN parameter"}, status_code=400)
            
        file_path = os.path.join(self.api.storage_dir, f"vinfast_changelog_{vin.lower()}.json")
        if not os.path.exists(file_path):
            return self.json([])
            
        try:
            def read_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            if hass:
                data = await hass.async_add_executor_job(read_file)
            else:
                data = read_file()
            return self.json(data)
        except Exception as e:
            _LOGGER.error(f"VinFast View Error reading changelog: {e}")
            return self.json({"error": str(e)}, status_code=500)


class VinFastStateView(HomeAssistantView):
    url = "/api/vinfast/state"
    name = "api:vinfast:state"
    requires_auth = True

    def __init__(self, api):
        self.api = api

    async def get(self, request):
        hass = request.app.get("hass") or getattr(self, "hass", None)

        vin = request.query.get("vin")
        if not vin:
            return self.json({"error": "Missing VIN parameter"}, status_code=400)
            
        file_path = os.path.join(self.api.storage_dir, f"vinfast_state_{vin.lower()}.json")
        if not os.path.exists(file_path):
            return self.json({})
            
        try:
            def read_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            if hass:
                data = await hass.async_add_executor_job(read_file)
            else:
                data = read_file()
            return self.json(data)
        except Exception as e:
            _LOGGER.error(f"VinFast View Error reading state: {e}")
            return self.json({"error": str(e)}, status_code=500)
