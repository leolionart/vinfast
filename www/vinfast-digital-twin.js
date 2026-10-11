// Bảng biên giới Việt Nam (lược bớt từ OSM, ~8 km mỗi điểm): dùng để phát hiện lộ trình đi ra nước ngoài
const VN_BORDER = '22.4,102.144;22.34,102.19;22.28,102.234;22.221,102.278;22.171,102.334;22.126,102.395;22.073,102.449;22.035,102.515;21.963,102.527;21.925,102.594;21.862,102.633;21.794,102.661;21.723,102.652;21.654,102.677;21.671,102.752;21.719,102.81;21.791,102.815;21.731,102.859;21.725,102.936;21.67,102.986;21.598,102.991;21.537,102.949;21.478,102.905;21.407,102.919;21.34,102.891;21.285,102.839;21.238,102.898;21.166,102.903;21.115,102.959;21.063,103.012;21.003,103.059;20.937,103.09;20.907,103.161;20.876,103.231;20.835,103.295;20.806,103.366;20.804,103.443;20.761,103.505;20.747,103.583;20.704,103.646;20.666,103.712;20.732,103.747;20.796,103.783;20.862,103.814;20.891,103.884;20.897,103.961;20.906,104.038;20.963,104.09;20.955,104.167;20.933,104.243;20.902,104.314;20.839,104.354;20.797,104.418;20.762,104.485;20.699,104.524;20.673,104.596;20.608,104.563;20.548,104.519;20.511,104.453;20.476,104.383;20.406,104.405;20.369,104.471;20.414,104.532;20.422,104.609;20.475,104.661;20.415,104.705;20.373,104.643;20.306,104.616;20.234,104.626;20.213,104.7;20.198,104.775;20.157,104.838;20.155,104.915;20.1,104.965;20.034,104.933;19.968,104.903;19.922,104.844;19.849,104.837;19.789,104.796;19.755,104.724;19.703,104.663;19.631,104.651;19.625,104.574;19.641,104.499;19.673,104.431;19.692,104.356;19.696,104.28;19.697,104.203;19.663,104.135;19.655,104.058;19.586,104.082;19.517,104.108;19.456,104.067;19.403,104.015;19.36,103.952;19.326,103.885;19.273,103.939;19.233,104.003;19.237,104.081;19.2,104.148;19.161,104.213;19.121,104.278;19.077,104.34;19.037,104.403;18.989,104.46;18.978,104.536;18.916,104.574;18.87,104.636;18.837,104.705;18.793,104.765;18.784,104.842;18.788,104.918;18.74,104.975;18.73,105.052;18.715,105.127;18.66,105.177;18.597,105.141;18.528,105.115;18.455,105.108;18.392,105.15;18.329,105.185;18.287,105.247;18.266,105.32;18.194,105.327;18.159,105.394;18.205,105.452;18.157,105.51;18.088,105.54;18.026,105.58;17.983,105.643;17.914,105.619;17.855,105.663;17.786,105.687;17.725,105.729;17.673,105.782;17.629,105.844;17.504,105.968;17.371,106.082;17.323,106.137;17.273,106.201;17.265,106.277;17.201,106.32;17.134,106.356;17.083,106.409;17.012,106.428;16.981,106.497;16.928,106.548;16.799,106.551;16.694,106.551;16.628,106.583;16.593,106.649;16.521,106.648;16.453,106.676;16.412,106.738;16.471,106.783;16.531,106.825;16.49,106.886;16.418,106.894;16.363,106.943;16.309,106.993;16.307,107.069;16.276,107.138;16.205,107.148;16.146,107.192;16.13,107.265;16.075,107.314;16.063,107.389;16.032,107.458;15.963,107.437;15.898,107.404;15.887,107.33;15.851,107.264;15.786,107.229;15.721,107.262;15.65,107.278;15.614,107.343;15.545,107.367;15.49,107.416;15.479,107.49;15.413,107.521;15.414,107.597;15.343,107.608;15.271,107.616;15.203,107.59;15.139,107.625;15.069,107.61;15.047,107.538;15.014,107.471;14.944,107.49;14.904,107.552;14.832,107.549;14.757,107.536;14.687,107.557;14.616,107.544;14.545,107.53;14.476,107.505;14.406,107.488;14.371,107.422;14.301,107.406;14.228,107.401;14.168,107.359;14.096,107.353;14.022,107.358;13.999,107.428;13.931,107.453;13.859,107.47;13.785,107.463;13.744,107.533;13.67,107.566;13.599,107.584;13.529,107.618;13.36,107.631;13.197,107.558;13.122,107.534;13.027,107.496;12.956,107.487;12.884,107.498;12.827,107.543;12.757,107.56;12.687,107.577;12.615,107.583;12.543,107.578;12.472,107.567;12.403,107.546;12.337,107.516;12.294,107.457;12.27,107.388;12.331,107.348;12.325,107.274;12.297,107.207;12.259,107.144;12.201,107.1;12.144,107.054;12.095,107;12.067,106.932;12.069,106.859;12.073,106.785;12.011,106.748;11.964,106.693;11.973,106.616;11.968,106.538;11.98,106.466;11.907,106.447;11.835,106.442;11.767,106.416;11.7,106.444;11.697,106.371;11.68,106.299;11.727,106.241;11.749,106.171;11.756,106.097;11.775,106.025;11.705,106.004;11.647,105.959;11.675,105.892;11.628,105.834;11.562,105.863;11.493,105.884;11.421,105.89;11.349,105.88;11.282,105.908;11.214,105.934;11.191,106.007;11.129,106.045;11.08,106.099;11.076,106.173;11.007,106.194;10.947,106.151;10.875,106.169;10.79,106.191;10.809,106.118;10.831,106.044;10.879,105.988;10.841,105.921;10.863,105.85;10.939,105.836;11.003,105.793;11.023,105.723;10.985,105.659;10.966,105.588;10.95,105.516;10.96,105.443;10.916,105.384;10.86,105.338;10.891,105.272;10.911,105.199;10.922,105.115;10.912,105.042;10.84,105.049;10.773,105.08;10.701,105.062;10.663,104.998;10.618,104.939;10.556,104.903;10.52,104.839;10.519,104.765;10.538,104.689;10.528,104.616;10.479,104.559;10.425,104.51;10.357,104.348;10.155,104.071;10.22,104.102;10.292,104.106;10.364,104.106;10.427,104.07;10.474,104.014;10.447,103.946;10.396,103.894;10.4,103.821;10.328,103.823;10.272,103.87;10.222,103.927;10.152,103.945;10.075,103.961;9.411,103.052;9.122,103.294;8.995,103.482;8.209,104.767;8.179,104.867;8.291,105.674;8.346,106.055;8.398,106.422;8.431,106.653;8.465,106.754;9.378,108.431;9.79,109.181;9.838,109.239;9.902,109.275;10.763,109.402;11.707,109.537;12.602,109.666;12.743,109.667;12.917,109.657;13.623,109.585;13.926,109.554;14.605,109.463;15.411,109.355;15.5,109.32;15.797,109.024;16.166,108.656;16.334,108.481;17.111,107.692;17.296,107.503;17.527,107.296;18.043,106.833;18.132,106.754;18.237,106.658;18.767,106.265;18.86,106.195;19.187,106.167;19.301,106.157;19.411,106.269;19.49,106.35;20.077,106.952;20.239,107.119;20.446,107.332;20.534,107.541;20.826,107.953;20.887,108.018;21.059,108.183;21.21,108.209;21.276,108.135;21.452,108.095;21.519,108.059;21.544,107.986;21.587,107.924;21.641,107.873;21.654,107.796;21.629,107.723;21.607,107.646;21.612,107.569;21.597,107.493;21.663,107.463;21.62,107.401;21.674,107.35;21.734,107.306;21.707,107.234;21.752,107.173;21.794,107.109;21.816,107.033;21.885,107.056;21.946,107.013;21.93,106.937;21.982,106.881;21.982,106.803;21.981,106.724;22.049,106.699;22.121,106.693;22.193,106.678;22.265,106.684;22.334,106.66;22.34,106.581;22.412,106.568;22.483,106.582;22.553,106.601;22.579,106.675;22.631,106.729;22.698,106.76;22.766,106.785;22.833,106.753;22.889,106.703;22.895,106.624;22.925,106.552;22.909,106.476;22.874,106.407;22.872,106.329;22.889,106.251;22.958,106.224;22.993,106.152;22.996,106.072;22.957,106.005;22.944,105.928;22.954,105.851;23.004,105.791;23.049,105.73;23.075,105.657;23.069,105.577;23.14,105.563;23.196,105.513;23.257,105.47;23.295,105.403;23.35,105.351;23.34,105.273;23.274,105.238;23.269,105.16;23.266,105.08;23.218,105.02;23.178,104.954;23.152,104.881;23.118,104.812;23.044,104.821;22.978,104.853;22.917,104.809;22.862,104.758;22.823,104.689;22.82,104.611;22.82,104.53;22.764,104.478;22.727,104.41;22.726,104.332;22.762,104.263;22.833,104.268;22.825,104.19;22.809,104.113;22.753,104.063;22.687,104.029;22.615,104.027;22.544,104.015;22.526,103.938;22.571,103.873;22.625,103.819;22.686,103.77;22.738,103.71;22.79,103.657;22.743,103.597;22.674,103.574;22.609,103.54;22.643,103.471;22.707,103.432;22.777,103.411;22.806,103.34;22.747,103.296;22.677,103.275;22.647,103.204;22.586,103.161;22.523,103.124;22.463,103.08;22.458,103.002;22.484,102.929;22.55,102.892;22.611,102.848;22.647,102.778;22.683,102.708;22.709,102.634;22.729,102.559;22.78,102.501;22.727,102.447;22.684,102.384;22.611,102.388;22.558,102.332;22.503,102.282;22.432,102.267;22.434,102.188'.split(';').map(p => p.split(',').map(Number));
class VinFastDigitalTwin extends HTMLElement {
  // Chú thích cho khối: Khởi tạo biến và thông số cho thẻ Digital Twin
  setConfig(config) {
    this.config = config || {};
    const configuredEntity = String(this.config.entity || '');
    this._entityPrefix = this.config.entity_prefix || (
      configuredEntity.startsWith('sensor.')
        ? configuredEntity.replace('sensor.', '').replace(/_trang_thai_hoat_dong$/, '')
        : null
    );
    this._map = null;
    this._polyline = null;
    this._marker = null;
    this._stationLayer = null;
    this._historyLayerGroup = null; 
    this._leafletLoaded = false;
    this._lastLat = null;
    this._lastLon = null;
    
    this._lastHeadingLat = null;
    this._lastHeadingLon = null;
    this._currentAngle = undefined; 
    
    this._isReplaying = false;
    this._isPaused = false;
    this._currentReplayIdx = 0;
    this._animationFrameId = null;
    
    this._rawRouteCoords = []; 
    this._smoothedRouteCoords = []; 

    this._showStations = localStorage.getItem('vf_show_stations') === 'true';
    this._stationFilter = localStorage.getItem('vf_station_filter') || 'ALL'; 
    this._currentStations = []; 
    this._prevStationStr = null;
    this._chargeHistoryData = [];
    
    this._effToggleTimer = null;
    this._effToggleState = false;
    this._lastAiMessage = ""; 

    this._tripsData = {}; 
    this._dayStats = {};  
    this._currentDate = new Date(); 
    this._todayStr = this.formatDate(this._currentDate);
    this._selectedDateStr = 'LIVE'; 
    this._addressCache = {};
    
    this._lastTotalSessions = undefined;

    // Khối Lộ trình / Dẫn đường / Trạm sạc trên tuyến
    this._routeLayer = null;
    this._routePlan = null;
    this._routeGeo = null;
    this._routeDest = null;
    this._routeBusy = false;
    this._pickDestMode = false;
    this._mapClickBound = false;
  }
  // Kết thúc khối.

  // Chú thích cho khối: Các hàm tính toán tiện ích (JSON, Khoảng cách GPS, Hướng xe)
  safeParseJSON(str) {
      if (!str) return [];
      if (typeof str !== 'string') return str; 
      try { return JSON.parse(str); }
      catch(e) {
          try { 
              let fixedStr = str.replace(/'/g, '"').replace(/True/g, 'true').replace(/False/g, 'false').replace(/None/g, 'null');
              return JSON.parse(fixedStr); 
          }
          catch(e2) { return []; }
      }
  }

  getDistanceFromLatLonInM(lat1, lon1, lat2, lon2) {
      const R = 6371000; 
      const dLat = (lat2-lat1) * Math.PI / 180;
      const dLon = (lon2-lon1) * Math.PI / 180; 
      const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2); 
      return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }

  formatMins(totalMins) {
      if (totalMins < 60) return `${totalMins}p`;
      const h = Math.floor(totalMins / 60);
      const m = totalMins % 60;
      return m > 0 ? `${h}g ${m}p` : `${h}g`;
  }

  formatDate(dateObj) {
      if (isNaN(dateObj.getTime())) return "1970-01-01"; 
      const y = dateObj.getFullYear();
      const m = String(dateObj.getMonth() + 1).padStart(2, '0');
      const d = String(dateObj.getDate()).padStart(2, '0');
      return `${y}-${m}-${d}`;
  }

  async getAddressFromCoords(lat, lon) {
      if (!lat || !lon) return "Không xác định";
      const cacheKey = `${parseFloat(lat).toFixed(4)},${parseFloat(lon).toFixed(4)}`;
      if (this._addressCache[cacheKey]) return this._addressCache[cacheKey];
      try {
          const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=16`);
          if (!response.ok) throw new Error("API Error");
          const data = await response.json();
          let address = data.display_name || "Không xác định";
          const parts = address.split(', ');
          if (parts.length > 3) address = parts.slice(0, 3).join(', ');
          this._addressCache[cacheKey] = address;
          return address;
      } catch (e) { return `${parseFloat(lat).toFixed(4)}, ${parseFloat(lon).toFixed(4)}`; }
  }

  cleanRouteData(points) {
      if (!points || !Array.isArray(points) || points.length === 0) return [];
      return points.map(p => {
          if (Array.isArray(p)) return [Number(p[0]), Number(p[1]), Number(p[2] || 0), Number(p[3] || 0)];
          return [Number(p.lat), Number(p.lon), Number(p.speed_kmh || 0), Number(p.timestamp_ms || 0)];
      }).filter(p => Number.isFinite(p[0]) && Number.isFinite(p[1]) && Math.abs(p[0]) <= 90 && Math.abs(p[1]) <= 180 && (p[0] !== 0 || p[1] !== 0));
  }

  _smoothRouteData(points) {
      const route = this.cleanRouteData(points);
      if (route.length < 3) return route;
      return route.map((point, index) => {
          if (index === 0 || index === route.length - 1) return point;
          const before = route[index - 1], after = route[index + 1];
          return [(before[0] + point[0] + after[0]) / 3, (before[1] + point[1] + after[1]) / 3, point[2], point[3]];
      });
  }

  getBearing(startLat, startLng, destLat, destLng) {
    // Compute bearing.
      startLat = startLat * Math.PI / 180; startLng = startLng * Math.PI / 180;
      destLat = destLat * Math.PI / 180; destLng = destLng * Math.PI / 180;
      const y = Math.sin(destLng - startLng) * Math.cos(destLat);
      const x = Math.cos(startLat) * Math.sin(destLat) - Math.sin(startLat) * Math.cos(destLat) * Math.cos(destLng - startLng);
      let brng = Math.atan2(y, x);
      return (brng * 180 / Math.PI + 360) % 360;
  }

  _splitRouteByGap(points, maxDistM = 250) {
      if (!points || points.length < 2) return [points || []];
      const segments = []; let seg = [points[0]];
      for (let i = 1; i < points.length; i++) {
          const prev = points[i - 1], cur = points[i];
          const dLat = (cur[0] - prev[0]) * Math.PI / 180, dLon = (cur[1] - prev[1]) * Math.PI / 180;
          const a = Math.sin(dLat/2)**2 + Math.cos(prev[0]*Math.PI/180)*Math.cos(cur[0]*Math.PI/180)*Math.sin(dLon/2)**2;
          const dist = 6371000 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
          if (dist > maxDistM) { if (seg.length) segments.push(seg); seg = []; }
          seg.push(cur);
      }
      if (seg.length) segments.push(seg);
      return segments.length ? segments : [points];
  }

  _smoothRotation(targetAngle) {
      if (this._currentAngle === undefined) { this._currentAngle = targetAngle; return targetAngle; }
      let diff = targetAngle - (this._currentAngle % 360);
      diff = ((diff + 540) % 360) - 180;
      this._currentAngle += diff;
      return this._currentAngle;
  }

  getCarIcon(angle = 0, speed = null) {
      if(typeof L === 'undefined') return null;
      const arrowSvg = `<svg class="car-dir-svg" viewBox="0 0 24 24" fill="#2563eb" stroke="white" stroke-width="2" style="position: absolute; top: 0; left: 0; transform: rotate(${angle}deg); transform-origin: center; transition: transform 0.05s linear; width: 28px; height: 28px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); z-index: 1000;"><path d="M12 2L22 20L12 17L2 20L12 2Z"/></svg>`;
      let speedDisplay = speed !== null && speed > 0 ? 'block' : 'none';
      let speedVal = speed !== null ? Math.round(speed) : 0;
      const speedBadge = `<div class="car-speed-badge" style="position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%); background: #10b981; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid white; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.3); z-index: 1001; display: ${speedDisplay}; transition: all 0.1s;">${speedVal} km/h</div>`;
      return L.divIcon({ className: '', html: `<div style="position: relative; width: 28px; height: 28px;">${arrowSvg}${speedBadge}</div>`, iconSize: [28, 28], iconAnchor: [14, 14] });
  }
  // Kết thúc khối.

  // Chú thích cho khối: Khởi tạo thư viện Bản đồ Leaflet
  loadLeaflet() {
    if (this._leafletLoaded) return;
    this._leafletLoaded = true;
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.onload = () => { setTimeout(() => this.initMap(), 200); };
    document.head.appendChild(script);
  }

  initMap() {
    const mapEl = this.querySelector('#vf-map-canvas');
    if (!mapEl || typeof L === 'undefined' || this._map) return;
    
    this._map = L.map(mapEl, { zoomControl: false });
    L.control.zoom({ position: 'bottomright', zoomInTitle: 'Phóng to', zoomOutTitle: 'Thu nhỏ' }).addTo(this._map);
    
    const zoomCtrl = mapEl.querySelector('.leaflet-control-zoom');
    if(zoomCtrl) { zoomCtrl.style.marginBottom = '25px'; zoomCtrl.style.marginRight = '12px'; zoomCtrl.style.border = 'none'; zoomCtrl.style.boxShadow = '0 4px 10px rgba(0,0,0,0.1)'; }
    
    L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', { maxZoom: 20, subdomains: ['mt0', 'mt1', 'mt2', 'mt3'] }).addTo(this._map);
    
    this._marker = L.marker([0, 0], {icon: this.getCarIcon(0, 0), opacity: 0, zIndexOffset: 1000}).addTo(this._map);
    this._polyline = L.polyline([], { color: '#2563eb', weight: 6, opacity: 0.85, lineCap: 'round', lineJoin: 'round', smoothFactor: 2.5 }).addTo(this._map);
    this._stationLayer = L.layerGroup().addTo(this._map);
    this._historyLayerGroup = L.layerGroup().addTo(this._map);
    this._routeLayer = L.layerGroup().addTo(this._map);
        this._signLayer = L.layerGroup().addTo(this._map);
    
    new IntersectionObserver((entries) => { 
        if (entries[0].isIntersecting && this._map) setTimeout(() => this._map.invalidateSize(), 100); 
    }).observe(mapEl);
  }
  // Kết thúc khối.

  // Chú thích cho khối: Đọc dữ liệu Offline Lịch sử JSON
  async fetchChargeHistory(vin) {
      if (!vin) return;
      try {
          if (this._hass && this._hass.callApi) {
              const apiData = await this._hass.callApi('GET', `vinfast/charge_history?vin=${vin.toLowerCase()}`);
              if (apiData) {
                  this._chargeHistoryData = apiData;
                  this.renderChargeHistory();
                  return;
              }
          }
      } catch (e) { console.log("VinFast API fallback cho Charge History"); }

      try {
          const res = await fetch(`/local/vinfast_charge_history_${vin.toLowerCase()}.json?v=${new Date().getTime()}`);
          if (res.ok) {
              this._chargeHistoryData = await res.json();
              this.renderChargeHistory();
          }
      } catch(e) {}
  }

  async fetchTripHistory(vin) {
    const vinStr = (vin || '').toLowerCase();
    let allTripsRaw = [];
    let apiSuccess = false;

    try {
        if (this._hass && this._hass.callApi) {
            const apiData = await this._hass.callApi('GET', `vinfast/trips?vin=${vinStr}`);
            if (Array.isArray(apiData)) {
                allTripsRaw = allTripsRaw.concat(apiData);
                apiSuccess = true;
            }
        }
    } catch(e) { console.log("VinFast API fallback cho Trips"); }

    if (!apiSuccess) {
        try {
            const resMain = await fetch(`/local/vinfast_trips_${vinStr}.json?v=${new Date().getTime()}`);
            if (resMain.ok) {
                const data = await resMain.json();
                if (Array.isArray(data)) allTripsRaw = allTripsRaw.concat(data);
            }
        } catch(e) {}
    }

    let d = new Date();
    for (let i = 0; i < 6; i++) {
        let y = d.getFullYear();
        let m = String(d.getMonth() + 1).padStart(2, '0');
        let archApiSuccess = false;

        try {
            if (this._hass && this._hass.callApi) {
                const apiData = await this._hass.callApi('GET', `vinfast/trips?vin=${vinStr}&year=${y}&month=${m}`);
                if (Array.isArray(apiData)) {
                    allTripsRaw = allTripsRaw.concat(apiData);
                    archApiSuccess = true;
                }
            }
        } catch(e) {}

        if (!archApiSuccess) {
            let archUrl = `/local/vinfast_trips_archive_${vinStr}_${y}_${m}.json`;
            try {
                const resArch = await fetch(`${archUrl}?v=${new Date().getTime()}`);
                if (resArch.ok) {
                    const dataArch = await resArch.json();
                    if (Array.isArray(dataArch)) allTripsRaw = allTripsRaw.concat(dataArch);
                }
            } catch(e) {}
        }
        d.setMonth(d.getMonth() - 1); 
    }

    let uniqueTripsMap = new Map();
    allTripsRaw.forEach(trip => {
        let tId = trip.id || trip.timestamp;
        if (!uniqueTripsMap.has(tId)) {
            uniqueTripsMap.set(tId, trip);
        }
    });
    
    let rawTrips = Array.from(uniqueTripsMap.values());
    let groupedData = {};

    if (rawTrips && Array.isArray(rawTrips) && rawTrips.length > 0) {
        rawTrips.forEach(trip => {
            let dateStr = "";
            if (trip.date && typeof trip.date === 'string') {
                let parts = trip.date.split(/[-/]/);
                if (parts.length === 3) {
                    if (parts[0].length === 4) dateStr = `${parts[0]}-${parts[1].padStart(2,'0')}-${parts[2].padStart(2,'0')}`;
                    else dateStr = `${parts[2]}-${parts[1].padStart(2,'0')}-${parts[0].padStart(2,'0')}`;
                }
            }
            if (!dateStr) {
                let ts = trip.id || trip.timestamp;
                let dtObj = new Date((ts && ts > 1e11) ? ts : (ts ? ts * 1000 : Date.now()));
                if (isNaN(dtObj.getTime())) dtObj = new Date();
                dateStr = this.formatDate(dtObj);
            }

            if (!groupedData[dateStr]) groupedData[dateStr] = [];

            const rawRoute = Array.isArray(trip.raw_route) && trip.raw_route.length ? trip.raw_route : [];
            const legacyRoute = Array.isArray(trip.route) ? trip.route : [];
            groupedData[dateStr].push({
                id: trip.id || new Date().getTime(),
                time: Number(trip.start_timestamp || trip.timestamp || trip.id || 0),
                end_time: Number(trip.end_timestamp || trip.timestamp || trip.id || 0),
                duration: Number(trip.duration || 0),
                distance: Number(trip.distance || 0),
                energy_used: Number(trip.energy_used || 0),
                start_time_str: trip.start_time || "--:--",
                end_time_str: trip.end_time || "--:--",
                // ponytail: route is filtered display data; raw_route remains diagnostic source.
                route: legacyRoute.length ? legacyRoute : rawRoute,
                raw_route: rawRoute,
                raw_recovery: rawRoute.length ? 'preserved' : 'legacy-only'
            });
        });

        this._tripsData = {};
        this._dayStats = {};

        for (let day in groupedData) {
            groupedData[day].sort((a, b) => a.time - b.time);
            let dayTrips = groupedData[day];
            
            let drivingMins = 0; let totalDistance = 0; let pauseSecs = 0; let parkingSecs = 0; let maxSpeed = 0;
            let startTime = dayTrips[0]?.start_time_str || "--:--"; 
            let endTime = dayTrips[dayTrips.length - 1]?.end_time_str || "--:--";

            dayTrips.forEach((trip, i) => {
                drivingMins += trip.duration; 
                totalDistance += trip.distance;
                if (Array.isArray(trip.route)) {
                    trip.route.forEach(pt => { if (Array.isArray(pt) && pt.length > 2 && pt[2] > maxSpeed) maxSpeed = pt[2]; });
                }

                if (i < dayTrips.length - 1) {
                    const tripEnd = trip.end_time || (trip.time + (trip.duration * 60));
                    let gapSecs = dayTrips[i+1].time - tripEnd;
                    if (gapSecs < 0) gapSecs = 0;
                    trip.pauseAfter = gapSecs; 
                    if (gapSecs < 900) pauseSecs += gapSecs; else parkingSecs += gapSecs; 
                } else {
                    trip.pauseAfter = 0;
                }
            });

            this._tripsData[day] = dayTrips;
            this._dayStats[day] = {
                startTime, endTime, drivingMins, totalDistance: totalDistance.toFixed(1),
                pauseMins: Math.round(pauseSecs / 60), parkingMins: Math.round(parkingSecs / 60), maxSpeed: Math.round(maxSpeed)
            };
        }
    }
    
    // Raw daily track is diagnostic-only. Trip playback remains segmented by saved trip.
    this._trackData = {};
    for (const day of Object.keys(groupedData)) {
        const compact = day.replaceAll('-', '');
        try {
            const rawRes = await fetch(`/api/vinfast/trip_track?vin=${vinStr}&date=${compact}&mode=raw`).then(r => r.ok ? r.json() : null);
            const raw = this.cleanRouteData(rawRes?.points || []);
            if (raw.length) this._trackData[day] = { raw };
        } catch (e) { console.debug('VinFast raw track unavailable', day); }
    }

    this.renderCalendar();
    this.switchMode();
    if (typeof this.renderStatsChart === 'function') this.renderStatsChart(7);
    this.renderTodayTrips();
    this.renderDailyConsumption();
  }
  // Kết thúc khối.

  // Chú thích cho khối: Quét và Gợi ý Trạm Sạc / Nút Dẫn đường Map
  checkAndShowSmartSuggestion(soc, heading) {
      const suggestCard = this.querySelector('#vf-smart-suggestion');
      if (!suggestCard || !this._currentStations || this._currentStations.length === 0) return;
      if (soc > 30 || heading === null) { suggestCard.style.display = 'none'; return; }
      
      const modelState = this._hass && this._entityPrefix ? this._hass.states[`sensor.${this._entityPrefix}_ten_dong_xe`] : null;
      const carModel = modelState ? (modelState.state || "").toUpperCase() : "";

      let validStations = this._currentStations;
      if (carModel.includes("VF3") || carModel.includes("VF 3")) {
          validStations = validStations.filter(st => st.power >= 20); 
      }

      let bestStation = null;
      for (let st of validStations) {
          if (st.avail > 0 && st.dist < 20) {
              let stationBearing = this.getBearing(this._lastLat, this._lastLon, st.lat, st.lng);
              let diff = Math.abs(stationBearing - heading);
              if (diff > 180) diff = 360 - diff;
              if (diff < 45 || st.dist < 3.0) {
                  if (!bestStation || st.dist < bestStation.dist) bestStation = st;
              }
          }
      }
      
      if (bestStation) {
          this.querySelector('#vf-suggest-name').innerText = bestStation.name;
          let exactDist = bestStation.dist;
          if (this._lastLat && this._lastLon && this._map) {
              let distMeters = this._map.distance([this._lastLat, this._lastLon], [bestStation.lat, bestStation.lng]);
              exactDist = (distMeters / 1000).toFixed(1);
          }
          this.querySelector('#vf-suggest-dist').innerText = exactDist;
          this.querySelector('#vf-suggest-power').innerText = bestStation.power;
          this.querySelector('#vf-suggest-avail').innerText = `${bestStation.avail}/${bestStation.total}`;
          
          let navUrl = `https://www.google.com/maps/dir/?api=1&destination=${bestStation.lat},${bestStation.lng}`;
          if (this._lastLat && this._lastLon) {
              navUrl = `https://www.google.com/maps/dir/?api=1&origin=${this._lastLat},${this._lastLon}&destination=${bestStation.lat},${bestStation.lng}&travelmode=driving`;
          }
          
          const btnNav = this.querySelector('#btn-suggest-nav');
          if (btnNav) btnNav.onclick = () => window.open(navUrl, '_blank');
          suggestCard.style.display = 'block';
      } else { suggestCard.style.display = 'none'; }
  }

  renderStations() {
      if (!this._stationLayer || !this._map || typeof L === 'undefined') return;
      this._stationLayer.clearLayers();
      if (!this._showStations || !Array.isArray(this._currentStations) || this._selectedDateStr !== 'LIVE') return; 

      const modelState = this._hass && this._entityPrefix ? this._hass.states[`sensor.${this._entityPrefix}_ten_dong_xe`] : null;
      const carModel = modelState ? (modelState.state || "").toUpperCase() : "";

      let validStations = this._currentStations;
      if (carModel.includes("VF3") || carModel.includes("VF 3")) {
          validStations = validStations.filter(st => st.power >= 20); 
      }

      validStations.forEach(st => {
          const isDC = st.power >= 20;
          if (this._stationFilter === 'DC' && !isDC) return;
          if (this._stationFilter === 'AC' && isDC) return;

          if (st.lat && st.lng) {
              let exactDist = st.dist; 
              if (this._lastLat && this._lastLon) {
                  let distMeters = this._map.distance([this._lastLat, this._lastLon], [st.lat, st.lng]);
                  exactDist = (distMeters / 1000).toFixed(1); 
              }

              let ratio = st.total > 0 ? (st.avail / st.total) * 100 : 0;
              let pinColor = '', statusText = '';
              if (st.total === 0 || st.avail === 0) { pinColor = '#dc2626'; statusText = 'Hết chỗ'; }
              else if (ratio < 30) { pinColor = '#f97316'; statusText = 'Sắp kín'; }
              else if (ratio < 50) { pinColor = '#eab308'; statusText = 'Đông'; }
              else if (ratio < 80) { pinColor = '#0ea5e9'; statusText = 'Trống'; }
              else { pinColor = '#16a34a'; statusText = 'Vắng'; }

              let boltCount = st.power >= 120 ? 3 : (st.power >= 20 ? 2 : 1);
              let boltsHtml = Array(boltCount).fill(`<ha-icon icon="mdi:flash" style="--mdc-icon-size: 16px; margin: 0 -2px;"></ha-icon>`).join('');
              const pinWidth = boltCount === 1 ? 30 : (boltCount === 2 ? 42 : 54);

              const stationIcon = L.divIcon({ 
                  className: 'custom-station-marker', 
                  html: `<div style="background-color: ${pinColor}; border: 2px solid white; border-radius: 14px; padding: 2px; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 3px 6px rgba(0,0,0,0.3); height: 26px; width: ${pinWidth}px;">${boltsHtml}</div>`, 
                  iconSize: [pinWidth, 26], iconAnchor: [pinWidth / 2, 13] 
              });

              let navUrl = `https://www.google.com/maps/dir/?api=1&destination=${st.lat},${st.lng}`;
              if (this._lastLat && this._lastLon) {
                  navUrl = `https://www.google.com/maps/dir/?api=1&origin=${this._lastLat},${this._lastLon}&destination=${st.lat},${st.lng}&travelmode=driving`;
              }
              
              const popupContent = `
                  <div style="font-family:sans-serif; min-width: 170px;">
                      <b style="font-size: 13px; color: #1e3a8a;">${st.name}</b><br>
                      <div style="margin-top: 6px; font-size: 12px;">
                          🚗 Cách xe: <b style="color: #ef4444;">${exactDist} km</b><br>
                          ⚡ Công suất: <b>${st.power} kW</b><br>
                          🔌 Trụ trống: <b style="color:${pinColor}; font-size:14px;">${st.avail} / ${st.total}</b>
                      </div>
                      <a href="${navUrl}" target="_blank" style="display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 10px; background: #2563eb; color: white; padding: 8px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 12px; transition: background 0.2s;">
                          Chỉ đường
                      </a>
                  </div>
              `;
              L.marker([st.lat, st.lng], {icon: stationIcon}).bindPopup(popupContent).addTo(this._stationLayer);
          }
      });
  }
  // Kết thúc khối.

  // Chú thích cho khối: Hiển thị Lịch, Cụm Chức năng (Replay / Station Filter)
  renderCalendar() {
      const year = this._currentDate.getFullYear();
      const month = this._currentDate.getMonth();
      const monthNames = ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"];
      
      const elMonthYear = this.querySelector('#cal-month-year');
      if(elMonthYear) elMonthYear.innerText = `${monthNames[month]} ${year}`;

      const firstDay = new Date(year, month, 1).getDay(); 
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      
      let gridHtml = `
          <div class="cal-day-name">CN</div><div class="cal-day-name">T2</div><div class="cal-day-name">T3</div>
          <div class="cal-day-name">T4</div><div class="cal-day-name">T5</div><div class="cal-day-name">T6</div><div class="cal-day-name">T7</div>
      `;

      for (let i = 0; i < firstDay; i++) { gridHtml += `<div class="cal-day disabled"></div>`; }

      for (let day = 1; day <= daysInMonth; day++) {
          const checkDateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          let classes = "cal-day";
          if (checkDateStr === this._todayStr) classes += " today";
          if (checkDateStr === this._selectedDateStr) classes += " active";
          if (this._tripsData[checkDateStr] && this._tripsData[checkDateStr].length > 0) classes += " has-trip";

          gridHtml += `<div class="cal-day ${classes}" data-date="${checkDateStr}">${day}</div>`;
      }

      const gridEl = this.querySelector('#cal-grid');
      if(gridEl) gridEl.innerHTML = gridHtml;

      const days = this.querySelectorAll('.cal-day:not(.disabled)');
      days.forEach(el => {
          el.addEventListener('click', (e) => {
              this._selectedDateStr = e.target.getAttribute('data-date');
              this.renderCalendar(); 
              this.switchMode();
              this.querySelector('#cal-dropdown').style.display = 'none';
          });
      });
  }

  changeMonth(offset) {
      this._currentDate.setMonth(this._currentDate.getMonth() + offset);
      this.renderCalendar();
  }

  switchMode() {
      const statsPanel = this.querySelector('#stats-panel');
      const liveTools = this.querySelector('#live-tools');
      const historyTools = this.querySelector('#history-tools');
      const tripFilter = this.querySelector('#history-trip-filter');
      
      const liveIndicator = this.querySelector('#icon-live-indicator');
      const calIcon = this.querySelector('#icon-cal-mode');

      this._historyLayerGroup.clearLayers();
      if (this._isReplaying) {
          this._isReplaying = false;
          cancelAnimationFrame(this._animationFrameId);
      }

      if (this._selectedDateStr === 'LIVE') {
          if(statsPanel) statsPanel.style.display = 'none';
          if(liveTools) liveTools.style.display = 'contents';
          if(historyTools) historyTools.style.display = 'none';
          if(tripFilter) tripFilter.style.display = 'none';
          
          if(liveIndicator) liveIndicator.style.display = 'block';
          if(calIcon) calIcon.style.color = '#334155';

          if (this._marker) this._marker.setOpacity(1);
          
          if (this._hass && this._entityPrefix) {
              const s = this._hass.states[`sensor.${this._entityPrefix}_lo_trinh_gps`];
              const routeJsonStr = s && s.attributes ? s.attributes.route_json : null;
              if (routeJsonStr) {
                  let parsedData = this.safeParseJSON(routeJsonStr);
                  this._rawRouteCoords = this.cleanRouteData(parsedData);
                  this._smoothedRouteCoords = this._smoothRouteData(this._rawRouteCoords);
                  this._polyline.setLatLngs(this._smoothedRouteCoords.map(p => [p[0], p[1]]));
              }
          }
          this.renderStations();
          if (this._routePlan) this._drawRoutePlan();
          if (this._lastLat && this._map) this._map.setView([this._lastLat, this._lastLon], 15);
      } else {
          if(statsPanel) statsPanel.style.display = 'flex';
          if(liveTools) liveTools.style.display = 'none'; 
          if(historyTools) historyTools.style.display = 'contents'; 
          if(tripFilter) tripFilter.style.display = 'flex';
          
          if(liveIndicator) liveIndicator.style.display = 'none';
          if(calIcon) calIcon.style.color = '#2563eb';

          if (this._marker) this._marker.setOpacity(0); 
          this._polyline.setLatLngs([]); 
          if (this._stationLayer) this._stationLayer.clearLayers(); 
          if (this._routeLayer) this._routeLayer.clearLayers();
          if (this._toggleRoutePanel) this._toggleRoutePanel(false);
          this._setPickMode(false);

          const dailySegments = this._tripsData[this._selectedDateStr];
          if (!dailySegments || dailySegments.length === 0) {
              if(statsPanel) statsPanel.style.display = 'none';
              if(historyTools) historyTools.style.display = 'none';
              if(tripFilter) tripFilter.style.display = 'none';
              return;
          }

          const tripSelector = this.querySelector('#trip-selector');
          if (tripSelector) {
              tripSelector.innerHTML = '<option value="all">Tổng hợp ngày</option>';
              dailySegments.forEach((t, i) => {
                  let opt = document.createElement('option');
                  opt.value = i;
                  opt.innerText = `Chuyến ${i+1} (${t.start_time_str})`;
                  tripSelector.appendChild(opt);
              });
              
              const newTripSelector = tripSelector.cloneNode(true);
              tripSelector.parentNode.replaceChild(newTripSelector, tripSelector);
              newTripSelector.addEventListener('change', (e) => {
                  let val = e.target.value;
                  this._renderHistoryMap(this._selectedDateStr, val === 'all' ? 'all' : parseInt(val));
              });
          }

          this._renderHistoryMap(this._selectedDateStr, 'all');
      }
      
      this.updateDynamicTripStats();
  }

  _renderHistoryMap(dateStr, tripIndex) {
      this._historyLayerGroup.clearLayers();
      if (this._isReplaying) {
          this._isReplaying = false;
          cancelAnimationFrame(this._animationFrameId);
          const iconReplay = this.querySelector('#icon-replay');
          if (iconReplay) iconReplay.setAttribute('icon', 'mdi:play-circle');
      }

      const dayTrips = this._tripsData[dateStr];
      if (!dayTrips || dayTrips.length === 0) return;

      let tripsToRender = tripIndex === 'all' ? dayTrips : [dayTrips[tripIndex]];
      const isRawMode = true;

      const btnMode = this.querySelector('#btn-route-mode');
      if (btnMode) {
          btnMode.innerText = 'RAW';
          btnMode.style.color = '#f59e0b';
          btnMode.disabled = true;
          btnMode.title = 'Lộ trình GPS nguyên bản';
      }
      
      let chargeDuration = 0;
      if (tripIndex === 'all' && this._chargeHistoryData) {
          const [y, m, d] = dateStr.split('-');
          const matchDate1 = `${d}/${m}/${y}`;
          const matchDate2 = `${d}-${m}-${y}`;
          this._chargeHistoryData.forEach(c => {
              if (c.date && (c.date === matchDate1 || c.date === matchDate2 || c.date.includes(matchDate1))) {
                  chargeDuration += parseInt(c.duration || 0);
              }
          });
      }

      let totalDist = 0, totalDrive = 0, totalPause = 0, totalPark = 0, maxSpd = 0;
      let startT = tripsToRender[0]?.start_time_str || "--:--";
      let endT = tripsToRender[tripsToRender.length - 1]?.end_time_str || "--:--";
      
      if (tripIndex === 'all') {
          const stats = this._dayStats[dateStr];
          if (stats) {
              totalDist = stats.totalDistance;
              totalDrive = stats.drivingMins;
              totalPause = stats.pauseMins;
              totalPark = stats.parkingMins;
              maxSpd = stats.maxSpeed;
          }
      } else {
          const t = tripsToRender[0];
          totalDist = t.distance.toFixed(1);
          totalDrive = t.duration;
          totalPause = 0; totalPark = 0;
          if (Array.isArray(t.route)) {
              t.route.forEach(pt => { if (Array.isArray(pt) && pt.length > 2 && pt[2] > maxSpd) maxSpd = pt[2]; });
          }
      }

      this.querySelector('#stat-time-a').innerText = startT;
      this.querySelector('#stat-time-b').innerText = endT;
      this.querySelector('#stat-dist').innerText = `${totalDist} km`; 
      this.querySelector('#stat-drive').innerText = this.formatMins(totalDrive);
      this.querySelector('#stat-pause').innerText = this.formatMins(totalPause);
      this.querySelector('#stat-park').innerText = this.formatMins(totalPark);
      this.querySelector('#stat-speed').innerText = `${maxSpd} km/h`;
      
      const chargeMetric = this.querySelector('#metric-charge');
      const statCharge = this.querySelector('#stat-charge');
      if (chargeDuration > 0 && chargeMetric && statCharge) {
          chargeMetric.style.display = 'flex';
          statCharge.innerText = this.formatMins(chargeDuration);
      } else if (chargeMetric) {
          chargeMetric.style.display = 'none';
      }

      const elAddrA = this.querySelector('#stat-addr-a');
      const elAddrB = this.querySelector('#stat-addr-b');
      elAddrA.innerText = "Đang dịch tọa độ...";
      elAddrB.innerText = "Đang dịch tọa độ...";

      if (tripsToRender[0].route && Array.isArray(tripsToRender[0].route) && tripsToRender[0].route.length > 0 && Array.isArray(tripsToRender[0].route[0])) {
          this.getAddressFromCoords(tripsToRender[0].route[0][0], tripsToRender[0].route[0][1]).then(addr => elAddrA.innerText = addr);
      }
      
      const lastRouteSegment = tripsToRender[tripsToRender.length-1].route;
      if (lastRouteSegment && Array.isArray(lastRouteSegment) && lastRouteSegment.length > 0) {
          const lPt = lastRouteSegment[lastRouteSegment.length-1];
          if(Array.isArray(lPt)) {
             this.getAddressFromCoords(lPt[0], lPt[1]).then(addr => elAddrB.innerText = addr);
          }
      }

      let bounds = L.latLngBounds();
      let flatCoordsForReplay = [];
      let replaySegments = [];
      let stopCount = 1;

      tripsToRender.forEach((segmentObj, index) => {
          let segmentCoords = segmentObj.route?.length ? segmentObj.route : segmentObj.raw_route;
          segmentCoords = this._smoothRouteData(segmentCoords || []);
          if (segmentCoords.length === 0) return;

          replaySegments.push(segmentCoords);
          flatCoordsForReplay.push(...segmentCoords);

          const latlngs = segmentCoords.map(pt => [pt[0], pt[1]]);
          L.polyline(latlngs, { color: '#2563eb', weight: 5, opacity: 0.8, lineJoin: 'round', smoothFactor: 0, noClip: true }).addTo(this._historyLayerGroup);
          latlngs.forEach(ll => bounds.extend(ll));

          if (index === 0) {
              L.marker(latlngs[0], { icon: L.divIcon({ className: 'marker-start' }) }).addTo(this._historyLayerGroup);
          }

          if (index < tripsToRender.length - 1 && tripIndex === 'all') {
              let pauseMins = Math.round((segmentObj.pauseAfter || 0) / 60);
              let isParking = pauseMins >= 15;
              let iconClass = isParking ? 'marker-park' : 'marker-pause';
              let currentStopNum = stopCount++;

              let marker = L.marker(latlngs[latlngs.length - 1], { icon: L.divIcon({ className: iconClass, html: currentStopNum }) }).addTo(this._historyLayerGroup);
              let popupHtml = `
                  <div style="font-family:sans-serif; text-align:center; min-width: 140px;">
                      <div style="font-size:11px; font-weight:800; color:${isParking ? '#ef4444' : '#f59e0b'}; margin-bottom:6px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">
                          <ha-icon icon="${isParking ? 'mdi:parking' : 'mdi:timer-sand'}" style="--mdc-icon-size:14px; margin-bottom:-2px;"></ha-icon>
                          ${isParking ? 'ĐIỂM ĐỖ XE' : 'ĐIỂM DỪNG'} #${currentStopNum}
                      </div>
                      <div style="font-size:12px; color:#475569; font-weight:600;">
                          Thời gian:<br><span style="color:#0f172a; font-weight:900; font-size:14px;">${this.formatMins(pauseMins)}</span>
                      </div>
                      <div style="font-size:10px; color:#64748b; margin-top:4px;">(Trước chuyến đi số ${index+2})</div>
                  </div>
              `;
              marker.bindPopup(popupHtml);
          }

          if (index === tripsToRender.length - 1) {
              const lastPt = segmentCoords[segmentCoords.length - 1];
              const speed = Array.isArray(lastPt) && lastPt.length > 2 ? lastPt[2] : 0;
              let endIcon = speed > 2.0 ? L.divIcon({ className: 'marker-continue', html: '❯' }) : L.divIcon({ className: 'marker-end-flag', html: '🏁' });
              L.marker(latlngs[latlngs.length - 1], { icon: endIcon }).addTo(this._historyLayerGroup);
          }
      });

      this._replaySegments = replaySegments;
      this._rawRouteCoords = flatCoordsForReplay;
      this._smoothedRouteCoords = flatCoordsForReplay;
      if (bounds.isValid()) {
          this._map.fitBounds(bounds, { padding: [40, 40] }); 
      } 
  }
  // Kết thúc khối.

  // Chú thích cho khối: Thống kê Dải Tốc Độ Tối Ưu (Đồng bộ cảm biến và sửa lỗi chiều dài chuỗi)
  _legacyUpdateDynamicTripStats() {
    const speedElTarget = this.querySelector('#vf-stat-speed');
    const dtSpeedChart = this.querySelector('#dt-speed-chart');
    const speedLbl = this.querySelector('#lbl-speed-title');
    
    const p = this._entityPrefix;
    if (!p || !this._hass) return;

    const speedSensor = this._hass.states[`sensor.${p}_dai_toc_do_toi_uu_nhat`] || this._hass.states[`sensor.${p}_toc_do_toi_uu_nhat`];
    let speedBandStr = speedSensor ? speedSensor.state : '--';
    
    // Sửa lỗi: Xóa điều kiện (speedBandStr.length > 20) gây mất dữ liệu khi chuỗi hiển thị quá dài
    if (!speedSensor || speedBandStr === 'unknown' || speedBandStr === 'unavailable') {
        speedBandStr = '--';
    }

    let hasSensorData = false;
    let maxVal = 0;
    let bars = [];

    const sObj = speedSensor || this._hass.states[`sensor.${p}_co_van_xe_dien_ai`];
    if (sObj && sObj.attributes) {
        for (let key in sObj.attributes) {
            let lowerKey = key.toLowerCase();
            // Loại trừ các attribute phụ (Quãng đường, Tiêu hao) để chỉ lấy giá trị hiệu suất km/1%
            if ((lowerKey.includes('dải') || lowerKey.includes('dai_') || lowerKey.includes('km/h') || lowerKey.match(/^[0-9]+(-|_)[0-9]+/)) && !lowerKey.includes('quãng') && !lowerKey.includes('tiêu') && !lowerKey.includes('distance') && !lowerKey.includes('drop')) { 
                let valStr = String(sObj.attributes[key]); 
                let num = parseFloat(valStr.split(' ')[0]); 
                if (!isNaN(num)) {
                    if (num > maxVal) maxVal = num; 
                    let label = key.replace(/Dải|dải|km\/h|_/ig, ' ').trim();
                    if(label.includes('-') || label.includes('>')) {
                         bars.push({label: label, val: num, rawStr: valStr}); 
                         hasSensorData = true;
                    }
                }
            }
        }
    }

    if (hasSensorData) {
        if (speedElTarget && speedBandStr !== '--') { 
            let spd = String(speedBandStr).split(' km/h')[0]; 
            speedElTarget.innerHTML = `${spd}<span class="stat-unit">km/h</span>`; 
        } else if (speedElTarget) {
            speedElTarget.innerHTML = '--';
        }
        if (speedLbl) speedLbl.innerText = "DẢI TỐC ĐỘ TỐI ƯU";
    } 
    else {
        let speedBands = { "0-30": 0, "30-50": 0, "50-70": 0, "70-90": 0, ">90": 0 };
        let coordsToAnalyze = [];
        if (this._selectedDateStr === 'LIVE') {
            if (this._smoothedRouteCoords && this._smoothedRouteCoords.length > 0) coordsToAnalyze = [this._smoothedRouteCoords];
        } else {
            let flatHistory = [];
            (this._tripsData[this._selectedDateStr] || []).forEach(seg => { 
                if (Array.isArray(seg.route)) flatHistory.push(...seg.route); 
            });
            if (flatHistory.length > 0) coordsToAnalyze = [flatHistory];
        }
        
        let foundData = false;
        coordsToAnalyze.forEach(segment => {
            if (!Array.isArray(segment)) return;
            for (let i = 0; i < segment.length - 1; i++) {
                if (!segment[i] || !segment[i+1]) continue;
                let ptA = segment[i]; let ptB = segment[i+1];
                let dist = this.getDistanceFromLatLonInM(ptA[0], ptA[1], ptB[0], ptB[1]) / 1000;
                let spd = ptB[2] || 0;
                if (spd > 2 && dist > 0) {
                    foundData = true;
                    if (spd < 30) speedBands["0-30"] += dist;
                    else if (spd < 50) speedBands["30-50"] += dist;
                    else if (spd < 70) speedBands["50-70"] += dist;
                    else if (spd < 90) speedBands["70-90"] += dist;
                    else speedBands[">90"] += dist;
                }
            }
        });
        
        if (foundData) {
            let bestBand = "0-30"; let maxDist = 0;
            for (let key in speedBands) {
                if (speedBands[key] > maxDist) { maxDist = speedBands[key]; bestBand = key; }
            }
            
            if (speedElTarget) {
                if (speedBandStr !== '--') {
                    let spd = String(speedBandStr).split(' km/h')[0]; 
                    speedElTarget.innerHTML = `${spd}<span class="stat-unit">km/h</span>`; 
                } else {
                    speedElTarget.innerHTML = `${bestBand}<span class="stat-unit">km/h</span>`;
                }
            }
            if (speedLbl) speedLbl.innerText = "DẢI TỐC ĐỘ TỐI ƯU";
            
            bars = []; maxVal = 0;
            for (let key in speedBands) {
                let d = parseFloat(speedBands[key].toFixed(1));
                if (d > maxVal) maxVal = d;
                bars.push({ label: key, val: d, unit: 'km' }); 
            }
            hasSensorData = true; 
        } else {
            if (speedElTarget) {
                if (speedBandStr !== '--') {
                    let spd = String(speedBandStr).split(' km/h')[0]; 
                    speedElTarget.innerHTML = `${spd}<span class="stat-unit">km/h</span>`; 
                } else {
                    speedElTarget.innerHTML = '--';
                }
            }
            if (speedLbl) speedLbl.innerText = "DẢI TỐC ĐỘ TỐI ƯU";
        }
    }
    
    if (hasSensorData && bars.length > 0) {
        bars.sort((a,b) => {
           let aNum = parseInt(a.label.split('-')[0].replace('>', '')) || 0;
           let bNum = parseInt(b.label.split('-')[0].replace('>', '')) || 0;
           return aNum - bNum;
        });
        let htmlChart = '';
        bars.forEach(b => {
            let pct = maxVal > 0 ? Math.round((b.val / maxVal) * 100) : 0;
            let displayVal = b.unit ? `${b.val} km` : (b.rawStr ? b.rawStr : b.val);
            htmlChart += `<div style="display:flex; align-items:center; gap:8px;"><div style="width:35px; font-size:10px; text-align:right; font-weight:bold; color:var(--secondary-text-color, #475569);">${b.label}</div><div style="flex:1; background:var(--divider-color, #e2e8f0); height:8px; border-radius:4px; overflow:hidden;"><div style="width:${pct}%; height:100%; background:${pct === 100 ? '#eab308' : '#3b82f6'}; transition: width 0.5s;"></div></div><div style="width:65px; font-size:10px; font-weight:bold; color:var(--primary-text-color, #1e3a8a); text-align:left;">${displayVal}</div></div>`;
        });
        if (dtSpeedChart) dtSpeedChart.innerHTML = htmlChart;
    } else {
        if (dtSpeedChart) dtSpeedChart.innerHTML = `<div style="text-align:center; padding:10px; color:#94a3b8; font-size:11px;">Chưa đủ dữ liệu phân tích</div>`;
    }
  }
  // Kết thúc khối.

  // Chú thích cho khối: Cập nhật dữ liệu từ biến HASS (Xử lý Pin, trạng thái, AI) lên Card HTML
  set hass(hass) {
    this._hass = hass;

    if (!this._entityPrefix) {
        for (let key in hass.states) {
            if (key.startsWith('sensor.') && key.endsWith('_trang_thai_hoat_dong')) {
                this._entityPrefix = key.replace('sensor.', '').replace('_trang_thai_hoat_dong', '');
                break;
            }
        }
    }
    const p = this._entityPrefix;
    if (!p) return;

    const vinStr = p.includes('_') ? p.split('_')[1] : p;

    const getValidState = (suffix) => {
        const s = hass.states[`sensor.${p}_${suffix}`];
        return (s && s.state !== 'unavailable' && s.state !== 'unknown' && s.state !== '') ? s.state : null;
    };

    const currentTripDistance = Number(getValidState('quang_duong_chuyen_di_trip') || 0);
    if (this.content && Number(this._lastTripDistance || 0) > 0 && currentTripDistance === 0) {
        this.fetchTripHistory(vinStr);
    }
    this._lastTripDistance = currentTripDistance;

    const getAttr = (suffix, attrKey) => {
        const s = hass.states[`sensor.${p}_${suffix}`];
        return (s && s.attributes && s.attributes[attrKey]) ? s.attributes[attrKey] : null;
    };

    const formatTimeSince = (dateString) => {
        if (!dateString) return "";
        const s = Math.floor((new Date() - new Date(dateString)) / 1000);
        if (s < 60) return "vừa xong";
        const m = Math.floor(s / 60); if (m < 60) return `${m} phút trước`;
        const h = Math.floor(m / 60); if (h < 24) return `${h} giờ trước`;
        return `${Math.floor(h / 24)} ngày trước`;
    };

    if (!this.content) {
      this.content = true;
      
      this.innerHTML = `
        <ha-card class="vf-card">
          <div class="vf-card-container">
            <div class="vf-summary-grid">
              <div class="vf-summary-col vf-summary-left">
                <div class="vf-summary-item vf-plate-item"><ha-icon icon="mdi:car-info"></ha-icon><span id="vf-name">Đang tải...</span></div>
                <div class="vf-summary-item" id="vf-weather-summary"><ha-icon icon="mdi:weather-partly-cloudy"></ha-icon><span id="vf-weather-text">--</span></div>
                <div class="vf-summary-item vf-security-item"><div id="vf-doors-container"></div></div>
              </div>
              <div class="vf-summary-col vf-summary-right">
                <div class="vf-summary-item vf-odo"><span class="vf-odo-label">ODO</span><span class="vf-odo-value"><span id="vf-odo-int"></span> <span class="vf-odo-unit">km</span></span></div>
                <div class="vf-summary-item"><ha-icon icon="mdi:car-connected"></ha-icon><span id="vf-vehicle-status">Đang đỗ</span></div>
                <div class="vf-summary-item vf-current-status"><div id="vf-status-badge" class="vf-status-badge"></div></div>
                <div class="vf-summary-item" id="vf-sign-item" style="display:none;"><ha-icon id="vf-sign-icon" icon="mdi:parking-off"></ha-icon><span id="vf-sign-text"></span></div>
              </div>
            </div>

            <div class="vf-car-stage" id="vf-car-stage">
              <img id="vf-car-img" src="" alt="VinFast Car" onerror="this.src='https://public.s3.connected-car.vinfast.vn/content/carimage/EI13_2024_CE18.png'">
              <div class="vf-tire vf-tire-fl" id="tire-fl" style="display:none;"><ha-icon icon="mdi:tire"></ha-icon><br><span></span> <span class="tire-unit">bar</span></div>
              <div class="vf-tire vf-tire-fr" id="tire-fr" style="display:none;"><ha-icon icon="mdi:tire"></ha-icon><br><span></span> <span class="tire-unit">bar</span></div>
              <div class="vf-tire vf-tire-rl" id="tire-rl" style="display:none;"><ha-icon icon="mdi:tire"></ha-icon><br><span></span> <span class="tire-unit">bar</span></div>
              <div class="vf-tire vf-tire-rr" id="tire-rr" style="display:none;"><ha-icon icon="mdi:tire"></ha-icon><br><span></span> <span class="tire-unit">bar</span></div>
            </div>

            <div class="vf-controls-area">
              <div class="vf-gears"><span class="gear" id="gear-P">P</span><span class="gear" id="gear-R">R</span><span class="gear" id="gear-N">N</span><span class="gear" id="gear-D">D</span></div>
              <div class="vf-speed" id="vf-speed-container"><span id="vf-speed"></span><span class="vf-speed-unit">km/h</span></div>
            </div>

            <div class="vf-charging-banner" id="vf-charging-banner" style="display: none;">
                <div class="charging-left">
                    <div class="charging-title"><ha-icon icon="mdi:ev-plug-type2"></ha-icon><span id="vf-charge-status-text">Hệ thống đang sạc</span></div>
                    <div class="charging-details">Giới hạn: <span id="vf-charge-limit" style="font-weight:bold; margin-left:4px;">--%</span><span style="margin:0 8px;opacity:0.5;">|</span>Công suất: <span id="vf-charge-power" style="font-weight:bold; margin-left:4px;">-- kW</span></div>
                </div>
                <div class="charging-right"><span id="vf-charge-time" class="charging-time">--</span><div class="charging-time-label"><span>phút</span><span>còn lại</span></div></div>
            </div>

            <div class="vf-remote-bar" id="vf-remote-controls">
                <div class="remote-btn" id="btn-rc-lock" title="Khóa cửa"><ha-icon icon="mdi:lock"></ha-icon></div>
                <div class="remote-btn" id="btn-rc-unlock" title="Mở cửa"><ha-icon icon="mdi:lock-open"></ha-icon></div>
                <div class="remote-btn" id="btn-rc-horn" title="Bấm còi"><ha-icon icon="mdi:bullhorn"></ha-icon></div>
                <div class="remote-btn" id="btn-rc-lights" title="Nháy đèn"><ha-icon icon="mdi:car-light-high"></ha-icon></div>
            </div>

            <div class="vf-stats-grid">
              <div class="stat-box clickable" id="box-batt-range">
                <div class="box-main">
                  <ha-icon id="icon-batt-range" icon="mdi:battery-charging-60" style="color: #10b981;"></ha-icon>
                  <div class="stat-info"><div class="stat-label" id="lbl-batt-range">MỨC PIN</div><div class="stat-val" id="vf-stat-batt-range">--</div></div>
                </div>
              </div>
              <div class="stat-box clickable" id="box-sensors">
                <div class="box-main">
                  <ha-icon icon="mdi:car-cog" style="color: #8b5cf6;"></ha-icon>
                  <div class="stat-info"><div class="stat-label">CẢM BIẾN</div><div class="stat-val" id="vf-stat-sensors" style="font-size: 13px;">--</div></div>
                </div>
              </div>

              <div class="stat-detail-container" id="detail-container-1">
                  <div class="stat-detail-content" id="detail-batt-range">
                      <div class="detail-row"><span>Sức khỏe Pin (SOH):</span> <b id="dt-soh" style="color:#10b981;">--</b></div>
                      <div class="detail-row"><span>Hiệu suất sạc cuối:</span> <b id="dt-charge-eff" style="color:#f59e0b;">--</b></div>
                      <div class="detail-row"><span>Thực tế (Đầy 100%):</span> <b id="dt-range-ai" style="color:#3b82f6;">--</b></div>
                      <div class="detail-row" style="border-bottom:none; padding-bottom:0;">
                          <div style="display:flex; flex-direction:column; gap:8px; width:100%; margin-top:5px;">
                              <div style="display:flex; justify-content:space-between; align-items:center; background:var(--primary-background-color, white); padding:8px 12px; border-radius:8px; border:1px solid var(--divider-color, #e2e8f0);">
                                  <div style="display:flex; align-items:center; gap:6px; color:var(--secondary-text-color, #475569);"><ha-icon icon="mdi:leaf-off" style="color:#ef4444; --mdc-icon-size:16px;"></ha-icon>Hao hụt dự kiến:</div>
                                  <b id="dt-range-drop-trip" style="font-size:13px; color:#ef4444;">--</b>
                              </div>
                          </div>
                      </div>
                  </div>
                  <div class="stat-detail-content" id="detail-sensors" style="padding:10px;">
                      <div id="sensor-list-container" style="max-height: 180px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px;"></div>
                  </div>
              </div>

              <div class="stat-box clickable" id="box-eff">
                <div class="box-main">
                  <ha-icon icon="mdi:leaf" style="color: #10b981;"></ha-icon>
                  <div class="stat-info"><div class="stat-label" id="lbl-eff">HIỆU SUẤT TB</div><div class="stat-val" id="vf-stat-eff">--</div></div>
                </div>
              </div>
              <div class="stat-box clickable" id="box-speed">
                <div class="box-main">
                  <ha-icon icon="mdi:chart-bell-curve" style="color: #eab308;"></ha-icon>
                  <div class="stat-info"><div class="stat-label" id="lbl-speed-title">DẢI TỐC ĐỘ TỐI ƯU</div><div class="stat-val" id="vf-stat-speed">--</div></div>
                </div>
              </div>

              <div class="stat-detail-container" id="detail-container-2">
                  <div class="stat-detail-content" id="detail-eff">
                      <div class="detail-row"><span>Tổng điện vòng đời:</span> <b id="dt-total-kwh" style="color:#f59e0b;">--</b></div>
                      <div class="detail-row"><span>Tổng tiền sạc:</span> <b id="dt-total-cost">--</b></div>
                  </div>
                  <div class="stat-detail-content" id="detail-speed">
                      <div style="font-size:10px; color:var(--secondary-text-color, #64748b); margin-bottom:6px;">Phân tích theo dải tốc độ:</div>
                      <div id="dt-speed-chart" style="display:flex; flex-direction:column; gap:4px;">Chưa đủ dữ liệu phân tích</div>
                  </div>
              </div>
              
              <div class="stat-box clickable" id="box-trip">
                <div class="box-main">
                  <ha-icon icon="mdi:map-marker-path" style="color: #8b5cf6;"></ha-icon>
                  <div class="stat-info"><div class="stat-label">TRIP HIỆN TẠI</div><div class="stat-val" id="vf-stat-trip">--</div></div>
                </div>
              </div>
              <div class="stat-box clickable" id="box-charge">
                <div class="box-main">
                  <ha-icon icon="mdi:ev-station" style="color: #f59e0b;"></ha-icon>
                  <div class="stat-info"><div class="stat-label">LỊCH SỬ SẠC</div><div class="stat-val" id="vf-stat-charge-count">--</div></div>
                </div>
              </div>
              
              <div class="stat-detail-container" id="detail-container-3">
                  <div class="stat-detail-content" id="detail-trip">
                      <div class="detail-row"><span>Tốc độ trung bình:</span> <b id="dt-trip-avg-speed">--</b></div>
                      <div class="detail-row"><span>Tiêu thụ chuyến:</span> <b id="dt-trip-energy" style="color:#eab308;">--</b></div>
                      <div id="dt-trip-list" style="max-height:220px; overflow-y:auto; margin-top:8px;"></div>
                  </div>
                  <div class="stat-detail-content" id="detail-charge" style="padding:0; overflow:hidden;">
                      <div style="padding:15px; border-bottom:1px solid var(--divider-color, #e2e8f0); display:flex; gap:10px; background:var(--secondary-background-color, #f8fafc);">
                          <div style="flex:1; background:var(--primary-background-color, white); padding:10px; border-radius:8px; border:1px solid var(--divider-color, #e2e8f0); text-align:center;">
                              <div style="font-size:10px; color:var(--secondary-text-color, #64748b); font-weight:bold;">SẠC TRẠM</div>
                              <div style="font-size:18px; font-weight:900; color:#2563eb;" id="inline-pub-sessions">--</div>
                          </div>
                          <div style="flex:1; background:var(--primary-background-color, white); padding:10px; border-radius:8px; border:1px solid var(--divider-color, #e2e8f0); text-align:center;">
                              <div style="font-size:10px; color:var(--secondary-text-color, #64748b); font-weight:bold;">SẠC NHÀ</div>
                              <div style="font-size:18px; font-weight:900; color:#10b981;"><span id="inline-home-sessions">--</span><span style="font-size:11px; font-weight:normal; color:var(--secondary-text-color, #64748b);"> lần</span></div>
                              <div style="font-size:10px; color:#10b981; font-weight:bold; margin-top:2px;"><span id="inline-home-kwh">--</span> kWh</div>
                          </div>
                      </div>
                      <div style="padding:10px 15px; font-size:11px; font-weight:bold; color:var(--secondary-text-color, #94a3b8); text-transform:uppercase; background:var(--primary-background-color, white);">Lần sạc gần nhất</div>
                      <div id="vf-inline-charge-list" style="max-height: 200px; overflow-y: auto; background:var(--primary-background-color, white); padding:0 15px 10px 15px;"></div>
                  </div>
              </div>
              
              <div class="stat-box clickable" id="box-daily">
                <div class="box-main">
                  <ha-icon icon="mdi:calendar-today" style="color: #38bdf8;"></ha-icon>
                  <div class="stat-info"><div class="stat-label">TIÊU THỤ HÔM NAY</div><div class="stat-val" id="vf-stat-daily-dist">--</div></div>
                </div>
              </div>
              <div class="stat-box clickable" id="box-stats">
                <div class="box-main">
                  <ha-icon icon="mdi:chart-bar" style="color: #ec4899;"></ha-icon>
                  <div class="stat-info"><div class="stat-label">THỐNG KÊ LÁI XE</div><div class="stat-val" id="vf-stat-total-dist">--</div></div>
                </div>
              </div>

              <div class="stat-box clickable" id="box-health">
                <div class="box-main">
                  <ha-icon icon="mdi:shield-check" style="color: #10b981;"></ha-icon>
                  <div class="stat-info"><div class="stat-label">TÌNH TRẠNG &amp; BẢO DƯỠNG</div><div class="stat-val" id="vf-stat-health">--</div></div>
                </div>
              </div>
              
              <div class="stat-detail-container" id="detail-container-4">
                  <div class="stat-detail-content" id="detail-daily">
                      <div class="detail-row"><span>Tiêu thụ hôm nay:</span> <b id="dt-daily-energy" style="color:#38bdf8;">--</b></div>
                      <div id="dt-daily-list" style="max-height:260px; overflow-y:auto; margin-top:8px;"></div>
                  </div>
                  <div class="stat-detail-content" id="detail-stats" style="padding:15px; font-size:12px;">
                      <div style="display:flex; flex-wrap:wrap; gap:4px; justify-content:space-between; margin-bottom:10px;">
                          <button class="stats-period-btn active" data-period="7">7 Ngày</button>
                          <button class="stats-period-btn" data-period="30">30 Ngày</button>
                          <button class="stats-period-btn" data-period="60">60 Ngày</button>
                          <button class="stats-period-btn" data-period="365">1 Năm</button>
                          <button class="stats-period-btn" data-period="all">Toàn thời gian</button>
                      </div>
                      <div style="display:flex; justify-content:space-between; margin-bottom:15px; font-weight:bold; color:var(--primary-text-color, #1e293b);">
                          <div style="text-align:center;"><div style="font-size:10px; color:var(--secondary-text-color, #64748b);">QUÃNG ĐƯỜNG</div><span id="dt-stats-dist" style="color:#8b5cf6;">-- km</span></div>
                          <div style="text-align:center;"><div style="font-size:10px; color:var(--secondary-text-color, #64748b);">TIÊU THỤ</div><span id="dt-stats-energy" style="color:#eab308;">-- kWh</span></div>
                          <div style="text-align:center;"><div style="font-size:10px; color:var(--secondary-text-color, #64748b);">HIỆU SUẤT</div><span id="dt-stats-eff" style="color:#10b981;">--</span></div>
                      </div>
                      <div id="stats-chart-container" style="height:140px; display:flex; align-items:flex-end; gap:6px; padding-top:15px; padding-bottom: 25px; border-bottom:1px solid var(--divider-color, #e2e8f0); overflow-x: auto; overflow-y: hidden; scroll-behavior: smooth;">
                          <div style="text-align:center; width:100%; color:#94a3b8; font-size:11px;">Đang tải biểu đồ...</div>
                      </div>
                  </div>
              </div>

              <div class="stat-detail-container" id="detail-container-5">
                  <div class="stat-detail-content" id="detail-health">
                      <div id="vf-health-body" style="padding:4px 0;">Đang tải dữ liệu...</div>
                      <button id="vf-health-refresh" style="margin-top:12px; width:100%; padding:9px; border-radius:8px; border:1px solid var(--divider-color, #e2e8f0); background:var(--primary-background-color, #fff); color:var(--primary-text-color, #1e293b); font-weight:bold; font-size:12px; cursor:pointer;">Làm mới dữ liệu mở rộng</button>
                  </div>
              </div>
            </div> 

            <div id="vf-ai-advisor-container" style="display: none; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 16px; padding: 15px; margin-bottom: 16px; color: white; box-shadow: 0 4px 15px rgba(37,99,235,0.2); transition: all 0.3s ease;">
                <div id="vf-ai-header" style="display: flex; align-items: center; justify-content: space-between; cursor: pointer;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight: bold; font-size: 14px;">
                        <ha-icon icon="mdi:robot-outline" style="color: #60a5fa;"></ha-icon>
                        Chuyên gia AI Đánh giá
                    </div>
                    <ha-icon id="vf-ai-chevron" icon="mdi:chevron-up" style="transition: transform 0.3s ease;"></ha-icon>
                </div>
                <div id="vf-ai-content" style="max-height: 200px; margin-top: 8px; overflow: hidden; transition: all 0.3s ease;">
                    <div id="vf-ai-text" style="font-size: 12px; line-height: 1.5; color: #e2e8f0; font-style: italic;">
                        Đang chờ phân tích chuyến đi...
                    </div>
                </div>
            </div>

            <div class="vf-address-bar" id="vf-address-container">
                <ha-icon icon="mdi:map-marker-radius" style="color: #ef4444; flex-shrink: 0;"></ha-icon>
                <span id="vf-current-address" style="font-weight: 600; color: var(--primary-text-color, #1f2937); font-size: 13px;">Đang tải vị trí hiện tại...</span>
            </div>

            <div class="map-and-cal-wrapper">
              
              <div style="position: absolute; top: 12px; left: 12px; z-index: 1000; display: flex; gap: 8px; width: calc(100% - 60px); pointer-events: none;">
                  <div class="cal-toggle-btn glass-panel" id="btn-toggle-cal" title="Xem Lịch sử hành trình" style="pointer-events: auto;">
                      <ha-icon id="icon-cal-mode" icon="mdi:calendar-month" style="color: #334155; --mdc-icon-size:20px;"></ha-icon>
                      <ha-icon id="icon-live-indicator" icon="mdi:record-circle" style="color: #ef4444; position: absolute; top: -2px; right: -2px; animation: pulseRed 2s infinite; --mdc-icon-size:12px;"></ha-icon>
                  </div>

                  <div id="history-trip-filter" class="glass-panel" style="display: none; align-items: center; padding: 0 10px; flex: 1; max-width: 170px; height: 34px; box-sizing: border-box; pointer-events: auto;">
                      <ha-icon icon="mdi:format-list-bulleted" style="--mdc-icon-size:16px; color:#2563eb; margin-right:4px;"></ha-icon>
                      <select id="trip-selector" style="background:transparent; border:none; outline:none; font-weight:bold; font-size:12px; color:#0f172a; cursor:pointer; width:100%; text-overflow:ellipsis; appearance:none; -webkit-appearance:none; padding-right:15px; position:relative; z-index:2;">
                          <option value="all">Tổng hợp ngày</option>
                      </select>
                      <ha-icon icon="mdi:chevron-down" style="--mdc-icon-size:18px; color:#64748b; margin-left:-20px; z-index:1;"></ha-icon>
                  </div>
              </div>

              <div class="cal-dropdown" id="cal-dropdown">
                  <button id="btn-live-mode" style="width:100%; background:#ef4444; color:white; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer; margin-bottom:10px; display:flex; justify-content:center; align-items:center; gap:6px;">
                      <ha-icon icon="mdi:record-circle-outline" style="--mdc-icon-size:18px;"></ha-icon> TRỞ VỀ LIVE
                  </button>
                  <div class="cal-header">
                      <button class="cal-btn" id="btn-prev-month"><ha-icon icon="mdi:chevron-left"></ha-icon></button>
                      <span id="cal-month-year">Đang tải...</span>
                      <button class="cal-btn" id="btn-next-month"><ha-icon icon="mdi:chevron-right"></ha-icon></button>
                  </div>
                  <div class="cal-grid" id="cal-grid"></div>
              </div>

              <div class="vf-map-container">
                  <div id="vf-map-canvas" style="width:100%; height:100%; background:var(--secondary-background-color, #e5e7eb); z-index:1;"></div>
                  
                  <div class="map-controls glass-panel" id="map-controls">
                    <button class="map-btn" id="btn-locate" title="Định vị xe"><ha-icon icon="mdi:crosshairs-gps"></ha-icon></button>
                    
                    <div id="live-tools" style="display:contents;">
                        <div class="map-divider"></div>
                        <div style="position:relative; display:flex; flex-direction:column; align-items:center;">
                            <button class="map-btn" id="btn-stations" title="Tắt/Bật Trạm sạc"><ha-icon icon="mdi:ev-station" style="color:#2563eb;"></ha-icon></button>
                            <button class="map-btn text-btn" id="btn-filter-station" style="display:none; height:18px; margin-top:2px;" title="Lọc trạm AC/DC">ALL</button>
                        </div>
                        <div class="map-divider"></div>
                        <button class="map-btn" id="btn-route-plan" title="Lộ trình &amp; trạm sạc trên tuyến"><ha-icon icon="mdi:map-marker-path" style="color:#7c3aed;"></ha-icon></button>
                    </div>

                    <div id="history-tools" style="display:none; flex-direction:column; gap:4px;">
                        <div class="map-divider"></div>
                        <button class="map-btn text-btn" id="btn-route-mode" disabled style="width: auto; padding: 0 4px; font-weight: bold; font-size: 10px; color: #f59e0b;" title="Lộ trình GPS nguyên bản">RAW</button>
                        <div class="map-divider"></div>
                        <button class="map-btn" id="btn-replay" title="Phát lại Lộ trình"><ha-icon id="icon-replay" icon="mdi:play-circle" style="color:#10b981;"></ha-icon></button>
                    </div>
                  </div>

                  <div id="vf-smart-suggestion" style="display:none; position:absolute; bottom:12px; left:50%; transform:translateX(-50%); background:var(--card-background-color, rgba(255,255,255,0.95)); backdrop-filter:blur(10px); padding:12px; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.2); width:85%; z-index:1000; border:2px solid #f59e0b;">
                     <div style="font-size:11px; color:#f59e0b; font-weight:800; margin-bottom:4px; display:flex; align-items:center; gap:4px;"><ha-icon icon="mdi:alert" style="--mdc-icon-size:14px;"></ha-icon> PIN THẤP - GỢI Ý SẠC TRÊN TUYẾN</div>
                     <div id="vf-suggest-name" style="font-size:14px; font-weight:bold; color:var(--primary-text-color, #1e3a8a); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">--</div>
                     <div style="font-size:12px; color:var(--secondary-text-color, #475569); margin-top:2px;">Phía trước <b id="vf-suggest-dist">--</b> km • <b id="vf-suggest-power">--</b> kW • Trống: <b id="vf-suggest-avail" style="color:#16a34a;">--</b></div>
                     <button id="btn-suggest-nav" style="margin-top:8px; width:100%; background:#2563eb; color:white; border:none; border-radius:8px; padding:6px; font-weight:bold; cursor:pointer;">Dẫn đường ngay</button>
                  </div>

                  <div id="vf-route-panel" style="display:none; position:absolute; top:8px; left:8px; right:52px; max-height:80%; overflow-y:auto; background:var(--card-background-color, rgba(255,255,255,0.97)); backdrop-filter:blur(10px); padding:10px; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.25); z-index:1300; border:1px solid var(--divider-color, #e2e8f0);">
                     <div style="display:flex; justify-content:space-between; align-items:center;">
                         <b style="font-size:12px; color:var(--primary-text-color, #1e3a8a); display:flex; align-items:center; gap:4px;"><ha-icon icon="mdi:map-marker-path" style="--mdc-icon-size:16px;"></ha-icon> LỘ TRÌNH &amp; TRẠM SẠC</b>
                         <button id="btn-route-close" style="background:none; border:none; padding:0; cursor:pointer; color:#64748b;"><ha-icon icon="mdi:close" style="--mdc-icon-size:18px;"></ha-icon></button>
                     </div>
                     <textarea id="vf-route-input" rows="2" placeholder="Dán link Google Maps, hoặc nhập địa chỉ điểm đến..." style="width:100%; box-sizing:border-box; margin-top:6px; padding:6px 8px; border-radius:8px; border:1px solid var(--divider-color, #cbd5e1); background:var(--card-background-color, #fff); color:var(--primary-text-color, #1e293b); font-size:12px; font-family:inherit; resize:vertical;"></textarea>
                     <div style="display:flex; gap:6px; margin-top:6px;">
                         <button id="btn-route-pick" style="flex:1; background:#f1f5f9; color:#334155; border:none; border-radius:8px; padding:6px; font-weight:bold; font-size:11px; cursor:pointer;">Chọn trên bản đồ</button>
                         <button id="btn-route-go" style="flex:1; background:#2563eb; color:white; border:none; border-radius:8px; padding:6px; font-weight:bold; font-size:11px; cursor:pointer;">Tính lộ trình</button>
                     </div>
                     <div id="vf-route-status" style="display:none; font-size:11px; margin-top:6px;"></div>
                     <div id="vf-route-result" style="display:none; margin-top:6px;"></div>
                  </div>
              </div>
            </div>

            <div class="stats-panel" id="stats-panel" style="display:none;">
                <div class="stat-endpoint">
                    <div class="endpoint-icon icon-a">A</div>
                    <div class="endpoint-info">
                        <div class="endpoint-time" id="stat-time-a">--:--</div>
                        <div class="endpoint-address" id="stat-addr-a">Đang lấy vị trí...</div>
                    </div>
                </div>
                
                <div class="stat-trip-metrics">
                    <div class="metric-item" title="Quãng đường"><ha-icon icon="mdi:road-variant" style="color:#8b5cf6;"></ha-icon> <div class="metric-text"><span id="stat-dist">0 km</span><span>Quãng đường</span></div></div>
                    <div class="metric-item" title="Thời gian lái xe"><ha-icon icon="mdi:steering" style="color:#2563eb;"></ha-icon> <div class="metric-text"><span id="stat-drive">0p</span><span>Lái xe</span></div></div>
                    <div class="metric-item" title="Dừng chờ (<15p)"><ha-icon icon="mdi:timer-sand" style="color:#f59e0b;"></ha-icon> <div class="metric-text"><span id="stat-pause">0p</span><span>Dừng chờ</span></div></div>
                    <div class="metric-item" title="Đỗ xe (>15p)"><ha-icon icon="mdi:parking" style="color:#ef4444;"></ha-icon> <div class="metric-text"><span id="stat-park">0p</span><span>Đỗ xe</span></div></div>
                    <div class="metric-item" id="metric-charge" style="display: none;" title="Thời gian sạc"><ha-icon icon="mdi:ev-plug-type2" style="color:#10b981;"></ha-icon> <div class="metric-text"><span id="stat-charge">0p</span><span>Sạc pin</span></div></div>
                    <div class="metric-item" title="Tốc độ tối đa"><ha-icon icon="mdi:speedometer" style="color:#64748b;"></ha-icon> <div class="metric-text"><span id="stat-speed">0 km/h</span><span>Max Speed</span></div></div>
                </div>

                <div class="stat-endpoint">
                    <div class="endpoint-icon icon-b">B</div>
                    <div class="endpoint-info">
                        <div class="endpoint-time" id="stat-time-b">--:--</div>
                        <div class="endpoint-address" id="stat-addr-b">Đang lấy vị trí...</div>
                    </div>
                </div>
            </div>

          </div>
        </ha-card>
      `;

      const style = document.createElement('style');
      style.textContent = `
        @import url('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css');
        .leaflet-control-attribution { display: none !important; }
        .vf-card { isolation: isolate; border-radius: 24px; background: var(--card-background-color, #ffffff); box-shadow: 0 4px 20px rgba(0,0,0,0.05); font-family: -apple-system, sans-serif;}
        .vf-card-container { padding: clamp(14px, 4vw, 20px); }
        .vf-summary-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); column-gap: clamp(12px, 5vw, 28px); margin-bottom: 4px; width: 100%; box-sizing: border-box; }
        .vf-summary-col { display: grid; grid-template-rows: repeat(3, minmax(34px, auto)); align-content: start; gap: 6px; min-width: 0; }
        .vf-summary-right { text-align: right; }
        .vf-summary-item { display: flex; align-items: center; gap: 7px; min-width: 0; color: var(--primary-text-color, #1f2937); font-size: 13px; font-weight: 750; line-height: 1.25; }
        .vf-summary-right .vf-summary-item { justify-content: flex-end; }
        .vf-summary-item ha-icon { --mdc-icon-size: 18px; flex: 0 0 auto; color: #2563eb; }
        .vf-plate-item { font-size: clamp(18px, 5vw, 23px); font-weight: 900; letter-spacing: .3px; white-space: nowrap; }
        .vf-plate-item ha-icon { --mdc-icon-size: 21px; }
        #vf-weather-summary ha-icon { color: #38bdf8; }
        #vf-weather-text, #vf-vehicle-status { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .vf-odo { flex-direction: column; align-items: flex-end; gap: 0; }
        .vf-odo-label { font-size: 10px; font-weight: 800; color: #2563eb; letter-spacing: .08em; }
        .vf-odo-value { font-size: clamp(18px, 5vw, 24px); font-weight: 900; color: var(--primary-text-color, #1f2937); white-space: nowrap; }
        .vf-odo-unit { font-size: 10px; font-weight: 700; color: var(--secondary-text-color, #64748b); }
        .vf-security-item, .vf-current-status { min-height: 30px; }
        #vf-doors-container { display: flex; flex-wrap: wrap; gap: 4px; max-width: 100%; }
        .vf-status-badge { position: static; display: inline-flex; max-width: 100%; background: #2563eb; color: white; padding: 5px 10px; border-radius: 999px; font-size: 11px; font-weight: 800; line-height: 1.2; white-space: normal; text-align: right; box-sizing: border-box; }
        .vf-car-stage { position: relative; height: clamp(170px, 45vw, 220px); display: flex; justify-content: center; align-items: center; margin: 2px 0 6px; transition: filter 0.3s; }
        .vf-car-stage.low-battery { filter: drop-shadow(0 0 15px rgba(239,68,68,0.3)); }
        .vf-car-stage img { max-width: min(92%, 430px); max-height: 100%; object-fit: contain; filter: drop-shadow(0 18px 18px rgba(0,0,0,0.18)); z-index: 1; }
        .vf-tire { position: absolute; background: var(--card-background-color, rgba(255,255,255,0.85)); backdrop-filter: blur(8px); padding: 4px 8px; border-radius: 12px; border: 1px solid var(--divider-color, #e5e7eb); font-size: 11px; font-weight: 800; color: var(--primary-text-color, #1f2937); text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); z-index: 5; }
        .vf-tire ha-icon { --mdc-icon-size: 14px; color: var(--secondary-text-color, #6b7280); } .tire-unit { font-size: 9px; font-weight: 600; color: var(--secondary-text-color, #6b7280); }
        .vf-tire-fl { bottom: 10%; left: 0; } .vf-tire-fr { top: 15%; left: 0; } .vf-tire-rl { bottom: 10%; right: 0; } .vf-tire-rr { top: 15%; right: 0; }
        .vf-controls-area { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; margin-bottom: 12px; align-items: center; width: 100%; }
        .vf-gears { display: flex; justify-content: space-evenly; align-items: center; min-width: 0; background: var(--secondary-background-color, rgba(243,244,246,0.8)); padding: 9px 12px; border-radius: 30px; gap: clamp(10px, 4vw, 18px); box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); }
        .gear { font-size: 15px; font-weight: 800; color: var(--secondary-text-color, #9ca3af); transition: all 0.3s; position: relative; line-height: 22px; }
        .gear.active { color: #2563eb; font-size: 21px; transform: none; } .gear.active::after { content: ''; position: absolute; bottom: -3px; left: 50%; transform: translateX(-50%); width: 4px; height: 4px; background: #2563eb; border-radius: 50%; }
        .vf-speed { display: flex; align-items: baseline; justify-content: center; min-width: 76px; background: rgba(37,99,235,0.1); border: 1px solid rgba(37,99,235,0.3); padding: 7px 12px; border-radius: 22px; box-sizing: border-box; }
        .vf-speed span:first-child { font-size: 24px; font-weight: 900; color: #2563eb; } .vf-speed-unit { font-size: 9px; font-weight: bold; color: #2563eb; margin-left: 3px; }
        .door-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; border-radius: 999px; font-size: 10px; font-weight: 800; background: var(--card-background-color, rgba(255,255,255,0.95)); border: 1px solid var(--divider-color, #e5e7eb); color: var(--primary-text-color, #374151); max-width: 100%; box-sizing: border-box; }
        .door-badge.open { background: rgba(239, 68, 68, 0.1); border-color: #ef4444; color: #ef4444; animation: pulseRed 1.5s infinite; }
        .leaflet-marker-icon { transition: transform 0.5s ease-out, top 0.5s ease-out, left 0.5s ease-out !important; }
        .door-badge.open.warning { background: rgba(245, 158, 11, 0.1); border-color: #f59e0b; color: #f59e0b; animation: pulseOrange 2s infinite; }
        .door-badge ha-icon { --mdc-icon-size: 15px; }
        @keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); } 70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
        @keyframes pulseOrange { 0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); } 70% { box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); } 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); } }
        
        .stats-period-btn { background: var(--secondary-background-color, #f1f5f9); border: none; padding: 6px 8px; border-radius: 8px; font-size: 11px; font-weight: bold; color: var(--secondary-text-color, #64748b); cursor: pointer; transition: all 0.2s; flex: 1 1 0; min-width: 0; margin: 0 3px; white-space: nowrap; }
        .stats-period-btn:first-child { margin-left: 0; } .stats-period-btn:last-child { margin-right: 0; }
        .stats-period-btn.active { background: #2563eb; color: white; box-shadow: 0 2px 8px rgba(37,99,235,0.3); }
        .stats-bar-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; flex: 0 0 calc(100% / 7 - 6px); min-width: 28px; height: 100%; position: relative; }
        .stats-bar { width: 14px; background: linear-gradient(to top, #3b82f6, #60a5fa); border-radius: 4px 4px 0 0; position: relative; transition: height 0.5s ease; min-height: 2px; }
        .stats-bar-label { font-size: 9px; color: var(--secondary-text-color, #94a3b8); position: absolute; bottom: -20px; text-align: center; white-space: nowrap; transform: rotate(-45deg); }
        .stats-bar-val { font-size: 8px; font-weight: bold; color: var(--primary-text-color, #1e293b); position: absolute; top: -14px; text-align: center; width: 100%; }
        #stats-chart-container { max-width: 100%; min-width: 0; box-sizing: border-box; overscroll-behavior-x: contain; }
        #stats-chart-container > * { max-width: 100%; }
        #stats-chart-container::-webkit-scrollbar { height: 4px; }
        #stats-chart-container::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }

        .vf-charging-banner { display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 15px 20px; border-radius: 16px; margin-bottom: 16px; animation: pulseChargeGlow 2.5s infinite; }
        .charging-left { display: flex; flex-direction: column; gap: 4px; }
        .charging-title { font-size: 15px; font-weight: 800; display:flex; align-items:center; gap:8px; line-height: 1.2;}
        .charging-title ha-icon { --mdc-icon-size: 20px; }
        .charging-details { font-size: 12px; display:flex; align-items:center; opacity: 0.9;}
        .charging-right { display: flex; align-items: baseline; gap: 4px; text-align: right;}
        .charging-time { font-size: 28px; font-weight: 900; line-height: 1;}
        .charging-time-label { font-size: 11px; display: flex; flex-direction: column; text-align: left; line-height: 1.2; opacity: 0.9;}
        @keyframes pulseChargeGlow { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); } 70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); } 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }

        .vf-remote-bar { display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; padding: 10px; background: var(--secondary-background-color, rgba(243,244,246,0.5)); border-radius: 16px;}
        .remote-btn { display: flex; align-items: center; justify-content: center; width: 45px; height: 45px; background: var(--card-background-color, white); border: 1px solid var(--divider-color, #e5e7eb); border-radius: 50%; color: var(--primary-text-color, #4b5563); cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: all 0.2s ease;}
        .remote-btn ha-icon { --mdc-icon-size: 22px; } .remote-btn:hover { background: rgba(37,99,235,0.1); color: #2563eb; transform: translateY(-2px);}
        
        .vf-stats-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 10px; margin-bottom: 20px; width: 100%; max-width: 100%; overflow: hidden; box-sizing: border-box; }
        .stat-box { display: flex; align-items: center; gap: 8px; background: var(--secondary-background-color, rgba(243, 244, 246, 0.6)); padding: 10px; border-radius: 12px; border: 1px solid var(--divider-color, rgba(229, 231, 235, 0.8)); transition: all 0.2s; cursor: pointer; height: 60px; box-sizing: border-box; min-width: 0; max-width: 100%; overflow: hidden; }
        .stat-box:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); background: var(--card-background-color, white); }
        .stat-box.active-box { border-color: #2563eb; background: var(--card-background-color, white); box-shadow: 0 4px 12px rgba(37,99,235,0.15); transform: translateY(-2px); }
        /* Thẻ "Tình trạng & bảo dưỡng" là ô lẻ cuối hàng: kéo rộng gấp 2 cho vừa lưới */
        #box-health { grid-column: 1 / -1; }
        
        .box-main { display: flex; align-items: center; gap: 8px; width: 100%; }
        .box-main ha-icon { flex-shrink: 0; --mdc-icon-size: 22px; }
        .stat-info { display: flex; flex-direction: column; min-width: 0; width: 100%; justify-content: center; overflow: hidden; height: 40px; }
        .stat-label { font-size: 10px; font-weight: 700; color: var(--secondary-text-color, #6b7280); text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; transition: color 0.3s;}
        .stat-val { font-size: 14px; font-weight: 800; color: var(--primary-text-color, #1f2937); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: opacity 0.3s ease-in-out; line-height: 1.2; display: block; }
        @media (max-width: 360px) {
          .vf-summary-grid { column-gap: 8px; }
          .vf-summary-item { font-size: 11px; gap: 4px; }
          .vf-plate-item, .vf-odo-value { font-size: 17px; }
          .vf-plate-item ha-icon, .vf-summary-item ha-icon { --mdc-icon-size: 16px; }
          .vf-gears { gap: 5px; padding-inline: 8px; }
          .vf-controls-area { gap: 6px; }
          .vf-speed { min-width: 68px; padding-inline: 8px; }
          .vf-remote-bar { gap: 8px; padding: 8px; }
          .remote-btn { width: 40px; height: 40px; }
        }

        .stat-unit { font-size: 0.7em; font-weight: 600; color: var(--secondary-text-color, #6b7280); margin-left: 3px; }
        .stat-detail-container { grid-column: 1 / -1; display: none; animation: slideDown 0.2s ease-out; transform-origin: top; margin-top: -5px; min-width: 0; width: 100%; max-width: 100%; overflow: hidden; box-sizing: border-box; }
        .stat-detail-content { background: var(--secondary-background-color, #f8fafc); border-radius: 12px; padding: 15px; border: 1px solid var(--divider-color, #93c5fd); box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); display: none; color: var(--primary-text-color, #1f2937); min-width: 0; max-width: 100%; overflow: hidden; box-sizing: border-box;}
        .detail-row { display: flex; justify-content: space-between; font-size: 12px; color: var(--primary-text-color, #475569); padding: 6px 0; border-bottom: 1px dashed var(--divider-color, #e2e8f0); }
        .detail-row:last-child { border-bottom: none; padding-bottom: 0; }
        @keyframes slideDown { from { opacity: 0; transform: scaleY(0.95); } to { opacity: 1; transform: scaleY(1); } }
        
        /* ĐỊA CHỈ & MAP WRAPPER */
        .vf-address-bar { background: var(--secondary-background-color, #f3f4f6); border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; border: 1px solid var(--divider-color, #e5e7eb);}
        .map-and-cal-wrapper { position: relative; z-index: 2; margin-bottom: 12px; }
        .vf-map-container { position:relative; border-radius:16px; overflow:hidden; border:1px solid var(--divider-color, #e5e7eb); width: 100%; height: 45vh; min-height: 350px; z-index: 1;}
        
        /* HIỆU ỨNG GLASSMORPHISM */
        .glass-panel { background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-radius: 10px; display: flex; }
        
        /* NÚT LỊCH GÓC TRÁI */
        .cal-toggle-btn { z-index: 1000; padding: 6px; cursor: pointer; align-items: center; justify-content: center; transition: 0.2s; display: flex;}
        .cal-toggle-btn:hover { background: rgba(255,255,255,1); transform: scale(1.05); }
        
        /* DROPDOWN LỊCH RESPONSIVE */
        .cal-dropdown { position: absolute; top: 60px; left: 12px; z-index: 1001; background: white; border-radius: 14px; padding: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); width: calc(100% - 24px); max-width: 320px; display: none; flex-direction: column; border: 1px solid #e2e8f0; box-sizing: border-box;}
        .cal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 700; color: #0f172a; font-size: 15px;}
        .cal-btn { background: transparent; border: none; cursor: pointer; font-size: 16px; padding: 6px; border-radius: 8px; display: flex; align-items: center; justify-content: center;}
        .cal-btn:hover { background: #f1f5f9; }
        .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; text-align: center;}
        .cal-day-name { font-weight: 700; color: #64748b; font-size: 11px; margin-bottom: 4px; display: flex; align-items: center; justify-content: center;}
        .cal-day { padding: 0; margin: 0; width: 100%; border-radius: 50%; cursor: pointer; position: relative; color: #334155; aspect-ratio: 1; display: flex; align-items: center; justify-content: center; box-sizing: border-box; font-weight: 600; font-size: clamp(11px, 3.5vw, 13px); border: 2px solid transparent;}
        .cal-day:hover { background: #e0f2fe; }
        .cal-day.disabled { color: #cbd5e1; cursor: default; } .cal-day.disabled:hover { background: transparent; }
        .cal-day.today { border-color: #f59e0b; color: #d97706; font-weight: 700; } 
        .cal-day.active { background: #2563eb; color: white; font-weight: 700; border-color: #2563eb; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.4);}
        .cal-day.has-trip::after { content: ''; position: absolute; bottom: 4px; left: 50%; transform: translateX(-50%); width: 4px; height: 4px; background-color: #10b981; border-radius: 50%; }
        .cal-day.active.has-trip::after { background-color: white; }

        /* BẢNG THỐNG KÊ MỚI (TRỤC THỜI GIAN) NẰM NGOÀI BẢN ĐỒ */
        .stats-panel { background: var(--card-background-color, #ffffff); border-radius: 16px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); display: none; flex-direction: column; gap: 4px; border: 1px solid var(--divider-color, #e5e7eb); margin-bottom: 16px;}
        .stat-endpoint { display: flex; align-items: center; gap: 12px; }
        .endpoint-icon { width: 28px; height: 28px; border-radius: 50%; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px; flex-shrink: 0; }
        .icon-a { background: #10b981; box-shadow: 0 2px 5px rgba(16, 185, 129, 0.3); }
        .icon-b { background: #ef4444; box-shadow: 0 2px 5px rgba(239, 68, 68, 0.3); }
        .endpoint-info { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
        .endpoint-time { font-weight: 800; font-size: 14px; color: #0f172a; line-height: 1.2;}
        .endpoint-address { font-size: 12px; color: #475569; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        .stat-trip-metrics { display: flex; flex-wrap: wrap; gap: 8px; padding: 10px 0; margin: 4px 0 4px 13px; border-left: 2px dashed #cbd5e1; padding-left: 24px; }
        .metric-item { flex: 1 1 calc(33.333% - 8px); min-width: 80px; display: flex; align-items: center; gap: 8px; background: #f8fafc; padding: 8px; border-radius: 8px; border: 1px solid #e2e8f0; }
        .metric-item ha-icon { --mdc-icon-size: 18px; }
        .metric-text { display: flex; flex-direction: column; }
        .metric-text span:first-child { font-weight: 800; font-size: 13px; color: #0f172a; line-height: 1.2;}
        .metric-text span:last-child { font-size: 10px; color: #64748b; }

        /* BỘ NÚT ĐIỀU KHIỂN BẢN ĐỒ GÓC PHẢI */
        .map-controls { position: absolute; top: 12px; right: 12px; z-index: 400; flex-direction: column; gap: 4px; padding: 6px; }
        .map-btn { width: 34px; height: 34px; background: transparent; border: none; border-radius: 8px; cursor: pointer; display:flex; align-items:center; justify-content:center; color: #334155; transition: 0.2s;}
        .map-btn:hover { background: rgba(255,255,255,1); transform: scale(1.1); }
        .map-btn ha-icon { --mdc-icon-size: 18px; }
        
        .text-btn { font-size: 10px; font-weight: 800; color: #f59e0b; width: 100%; padding: 0; height: 20px; background: rgba(255,255,255,0.6); border-radius: 4px; margin-top: -2px;}
        .map-divider { height: 1px; background: rgba(0,0,0,0.1); margin: 2px 6px; }

        /* MARKERS BẢN ĐỒ */
        .marker-start { background: #10b981; border: 2px solid white; border-radius: 50%; box-shadow: 0 3px 6px rgba(0,0,0,0.3); width: 14px !important; height: 14px !important; margin-top:-7px; margin-left:-7px;}
        .marker-park { background: #ef4444; border: 2px solid white; border-radius: 50%; color: white; display: flex; justify-content: center; align-items: center; font-size: 10px; font-weight: bold; width: 18px !important; height: 18px !important; margin-top:-9px; margin-left:-9px; box-shadow: 0 3px 6px rgba(0,0,0,0.3);}
        .marker-pause { background: #f59e0b; border: 2px solid white; border-radius: 50%; color: white; display: flex; justify-content: center; align-items: center; font-size: 10px; font-weight: bold; width: 18px !important; height: 18px !important; margin-top:-9px; margin-left:-9px; box-shadow: 0 3px 6px rgba(0,0,0,0.3);}
        .marker-end-flag { font-size: 20px; line-height: 1; filter: drop-shadow(0 3px 3px rgba(0,0,0,0.3)); margin-top:-20px; margin-left:-10px;}
        .marker-continue { background: #3b82f6; border: 2px solid white; border-radius: 50%; color: white; display: flex; justify-content: center; align-items: center; font-size: 10px; font-weight: bold; width: 18px !important; height: 18px !important; margin-top:-9px; margin-left:-9px; box-shadow: 0 3px 6px rgba(0,0,0,0.3);}
      `;
      this.appendChild(style);

      const toggleBtn = this.querySelector('#btn-toggle-cal');
      const dropdown = this.querySelector('#cal-dropdown');
      if (toggleBtn && dropdown) {
          toggleBtn.onclick = () => { dropdown.style.display = dropdown.style.display === 'flex' ? 'none' : 'flex'; };
      }
      const mapCanvas = this.querySelector('#vf-map-canvas');
      if (mapCanvas) {
          mapCanvas.onclick = () => { if (dropdown) dropdown.style.display = 'none'; };
      }
      
      const btnLiveMode = this.querySelector('#btn-live-mode');
      if (btnLiveMode) {
          btnLiveMode.onclick = () => {
              this._selectedDateStr = 'LIVE';
              this.renderCalendar();
              this.switchMode();
              dropdown.style.display = 'none';
          }
      }

      this.querySelector('#btn-prev-month').addEventListener('click', () => this.changeMonth(-1));
      this.querySelector('#btn-next-month').addEventListener('click', () => this.changeMonth(1));

      this.toggleExpand = (boxId, detailId, containerId) => {
          const box = this.querySelector(boxId); const detail = this.querySelector(detailId); const container = this.querySelector(containerId);
          if (!box || !detail || !container) return;
          const isExpanded = box.classList.contains('active-box');
          this.querySelectorAll('.stat-box').forEach(el => el.classList.remove('active-box'));
          this.querySelectorAll('.stat-detail-container').forEach(el => el.style.display = 'none');
          this.querySelectorAll('.stat-detail-content').forEach(el => el.style.display = 'none');
          
          if (!isExpanded) {
              box.classList.add('active-box'); container.style.display = 'block'; detail.style.display = 'block';
              if (boxId === '#box-charge') this.renderChargeHistory();
              if (boxId === '#box-trip') this.renderTodayTrips();
              if (boxId === '#box-daily') this.renderDailyConsumption();
              // Mở thẻ sức khỏe: nạp lại lịch sử sạc rồi vẽ lại (API "lần sạc gần nhất" của
              // VinFast đứng yên từ 14/09, lịch sử sạc mới hơn nên phải lấy bản tươi).
              if (boxId === '#box-health') { this.renderHealthPanel(); this.fetchChargeHistory(vinStr).then(() => this.renderHealthPanel()); }
          }
      };

      const aiHeader = this.querySelector('#vf-ai-header');
      const aiContent = this.querySelector('#vf-ai-content');
      const aiChevron = this.querySelector('#vf-ai-chevron');

      if (aiHeader) {
          aiHeader.onclick = () => {
              const isCollapsed = aiContent.style.maxHeight === '0px';
              if (isCollapsed) {
                  aiContent.style.maxHeight = '200px'; aiContent.style.marginTop = '8px'; aiChevron.style.transform = 'rotate(0deg)';
              } else {
                  aiContent.style.maxHeight = '0px'; aiContent.style.marginTop = '0px'; aiChevron.style.transform = 'rotate(180deg)';
              }
          };
      }

      this.renderChargeHistory = () => {
          const listEl = this.querySelector('#vf-inline-charge-list');
          if (!listEl) return;
          let html = '';
          if (this._chargeHistoryData && this._chargeHistoryData.length > 0) {
              this._chargeHistoryData.forEach(c => {
                  html += `<div style="padding:8px 0; border-bottom:1px solid var(--divider-color, #e5e7eb);">
                      <div style="font-weight:bold; font-size:11px; color:var(--primary-text-color, #1e3a8a); margin-bottom:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${c.address}</div>
                      <div style="display:flex; justify-content:space-between; font-size:10px; color:var(--secondary-text-color, #475569);"><span>${c.date}</span><span style="color:#d97706; font-weight:bold;">${c.kwh} kWh</span><span>${c.duration}p</span></div>
                  </div>`;
              });
          } else { html = `<div style="padding:10px; text-align:center; color:var(--secondary-text-color, #6b7280); font-size:11px;">Chưa có dữ liệu sạc trạm.</div>`; }
          
          const pSessions = this.querySelector('#inline-pub-sessions'); const hSessions = this.querySelector('#inline-home-sessions'); const hKwh = this.querySelector('#inline-home-kwh');
          if(pSessions) pSessions.innerText = getValidState('so_lan_sac_tai_tram') || 0;
          if(hSessions) hSessions.innerText = getValidState('so_lan_sac_tai_nha') || 0;
          if(hKwh) hKwh.innerText = getValidState('dien_nang_sac_tai_nha') || 0;
          listEl.innerHTML = html;
      };

      // ---------------------------------------------------------------
      // KHỐI "TÌNH TRẠNG & BẢO DƯỠNG" (dữ liệu từ extended_api.py)
      // ---------------------------------------------------------------
      const fmtEpoch = (v) => {
          if (v === null || v === undefined || v === '') return null;
          const n = Number(v);
          // sensor device_class=timestamp trả chuỗi ISO; epoch ms cũng chấp nhận
          const d = (!isNaN(n) && n > 0) ? new Date(n < 1e12 ? n * 1000 : n) : new Date(v);
          if (isNaN(d.getTime())) return null;
          try { return d.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
          catch (e) { return d.toISOString(); }
      };
      const isOn = (v) => v === true || v === 'on' || v === 'true' || v === 'True' || v === '1';

      this.renderHealthPanel = () => {
          // Hàm này chỉ được tạo 1 lần lúc init nên biến `hass` bên ngoài bị đóng băng ở
          // lần gán đầu tiên -> luôn đọc lại từ this._hass (được làm mới mỗi lần hass đổi).
          const hass = this._hass || {};
          const pfx = this._entityPrefix;
          const getValidState = (suffix) => {
              const s = hass.states[`sensor.${pfx}_${suffix}`];
              return (s && s.state !== 'unavailable' && s.state !== 'unknown' && s.state !== '') ? s.state : null;
          };
          const alerts = Number(getValidState('so_canh_bao_tren_xe') || 0);
          const thiefAlert = isOn(getValidState('co_su_kien_bao_trom'));
          const thiefArmed = isOn(getValidState('chuong_bao_trom_dang_bat'));
          const fwOn = isOn(getValidState('co_ban_cap_nhat_firmware'));
          const score = getValidState('diem_lai_xe_an_toan');

          // Nguồn "lần sạc gần nhất": API vf-safety-driving của VinFast đứng ở 14/09/2026 (đã đối
          // chiếu 20/09 vẫn trả 14/09) trong khi lịch sử sạc (ccarcharging) đã có phiên 19/09 20:47.
          // Vì vậy lấy phiên mới nhất trong lịch sử sạc khi nó mới hơn API.
          // ponytail: chỉ so 1 mốc thời gian; nâng cấp khi VinFast sửa lại endpoint last-charge.
          const histList = Array.isArray(this._chargeHistoryData) ? this._chargeHistoryData : [];
          const newest = histList.reduce((a, b) =>
              (Number(b && b.session_time || 0) > Number(a && a.session_time || 0) ? b : a), null);
          const apiChargeMs = Date.parse(getValidState('thoi_diem_sac_gan_nhat') || '');
          const histChargeMs = newest ? Number(newest.session_time || 0) * 1000 : NaN;
          const useHist = !!(newest && isFinite(histChargeMs) && (!isFinite(apiChargeMs) || histChargeMs > apiChargeMs));

          const summaryEl = this.querySelector('#vf-stat-health');
          if (summaryEl) {
              if (thiefAlert) { summaryEl.innerText = 'CÓ CẢNH BÁO TRỘM'; summaryEl.style.color = '#dc2626'; }
              else if (alerts > 0) { summaryEl.innerText = `${alerts} cảnh báo`; summaryEl.style.color = '#f59e0b'; }
              else if (fwOn) { summaryEl.innerText = 'Có bản cập nhật'; summaryEl.style.color = '#2563eb'; }
              else if (score) { summaryEl.innerText = `${score} điểm`; summaryEl.style.color = '#10b981'; }
              else { summaryEl.innerText = 'Bình thường'; summaryEl.style.color = '#10b981'; }
          }

          const host = this.querySelector('#vf-health-body');
          const box = this.querySelector('#box-health');
          if (!host || !box || !box.classList.contains('active-box')) return;

          // ---- Định dạng giá trị: số kiểu Việt Nam, bỏ ".0" thừa, ẩn giá trị rỗng ----
          const num = (v, unit, dec) => {
              if (v === null || v === undefined || v === '') return null;
              const n = Number(v);
              if (!isFinite(n)) return null;
              const opts = (dec === undefined)
                  ? { maximumFractionDigits: 1 }
                  : { minimumFractionDigits: dec, maximumFractionDigits: dec };
              let s;
              try { s = n.toLocaleString('vi-VN', opts); } catch (e) { s = String(n); }
              return unit ? `${s}\u00a0${unit}` : s;
          };
          const money = (v) => { const s = num(v); return s === null ? null : `${s}\u00a0đ`; };
          const fmtMinutes = (v) => {
              if (v === null || v === undefined || v === '') return null;
              const n = Number(v);
              if (!isFinite(n) || n <= 0) return null;
              if (n < 60) return num(n, 'phút');
              const h = Math.floor(n / 60), m = Math.round(n % 60);
              return m ? `${h} giờ ${m} phút` : `${h} giờ`;
          };
          const phone = (v) => {
              if (v === null || v === undefined || v === '') return null;
              const s = String(v).trim();
              const m = s.match(/^(?:\+?84|0)(\d{9})$/);
              return m ? `+84 ${m[1].slice(0, 3)} ${m[1].slice(3, 6)} ${m[1].slice(6)}` : s;
          };
          // ISO "YYYY-MM-DD" -> "DD/MM/YYYY" (bảo hành, kỳ tính điểm)
          const fmtDay = (v) => {
              if (v === null || v === undefined || v === '') return null;
              const s = String(v).trim();
              const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
              return m ? `${m[3]}/${m[2]}/${m[1]}` : s;
          };
          const fmtDayRange = (v) => {
              if (v === null || v === undefined || v === '') return null;
              const parts = String(v).trim().split(':');
              if (parts.length === 2) {
                  const a = fmtDay(parts[0]), b = fmtDay(parts[1]);
                  if (a && b) return `${a} – ${b}`;
              }
              return fmtDay(v);
          };
          const ENUM_VI = {
              BALANCE: 'Cân bằng tốt', BALANCED: 'Cân bằng tốt', IMBALANCE: 'Lệch cell', UNBALANCED: 'Lệch cell',
              NORMAL: 'Bình thường', GOOD: 'Tốt', WARNING: 'Cảnh báo', LOW: 'Yếu', BAD: 'Kém',
              SUCCESS: 'Thành công', SUCCEEDED: 'Thành công', FAILED: 'Thất bại', FAIL: 'Thất bại',
              DC: 'DC (sạc nhanh)', AC: 'AC (sạc thường)',
          };
          // Chuỗi trạng thái -> tiếng Việt; coi unknown/none/null là "không có dữ liệu"
          const tr = (v) => {
              if (v === null || v === undefined || v === '') return null;
              const s = String(v).trim();
              const low = s.toLowerCase();
              if (!s || low === 'unknown' || low === 'none' || low === 'null' || low === 'nan') return null;
              return ENUM_VI[s.toUpperCase()] || s;
          };
          const onOff = (v) => (v === null || v === undefined || v === '') ? null : (isOn(v) ? 'Đang bật' : 'Đang tắt');
          const yesNo = (v) => (v === null || v === undefined || v === '') ? null : (isOn(v) ? 'Có' : 'Không');

          const BORDER = 'border-bottom:1px dashed var(--divider-color, #e2e8f0);';
          // Hàng nhãn trái – giá trị phải (giá trị ngắn)
          const row = (label, value, color) => {
              if (value === null || value === undefined || value === '') return '';
              return `<div style="${BORDER} display:flex; justify-content:space-between; align-items:baseline; gap:12px; padding:6px 0;">
                  <span style="color:var(--secondary-text-color, #64748b); font-size:11px; white-space:nowrap;">${label}</span>
                  <b style="color:${color || 'var(--primary-text-color, #1e293b)'}; text-align:right; font-size:12px;">${value}</b></div>`;
          };
          // Hàng nhãn trên – giá trị xuống dòng (văn bản dài: thói quen, nội dung cảnh báo)
          const block = (label, value, color) => {
              if (value === null || value === undefined || value === '') return '';
              return `<div style="${BORDER} padding:6px 0;">
                  <div style="color:var(--secondary-text-color, #64748b); font-size:11px;">${label}</div>
                  <div style="color:${color || 'var(--primary-text-color, #1e293b)'}; font-weight:600; font-size:12px; line-height:1.45; margin-top:2px;">${value}</div></div>`;
          };
          const group = (title, icon, rows, color) => {
              const body = rows.filter(Boolean).join('');
              if (!body) return '';
              return `<div style="margin-top:12px; border-left:3px solid ${color}; padding-left:9px;">
                  <div style="display:flex; align-items:center; gap:5px; font-size:10px; font-weight:900; letter-spacing:.5px; color:${color}; text-transform:uppercase;">
                      <ha-icon icon="${icon}" style="--mdc-icon-size:14px;"></ha-icon>${title}</div>
                  ${body}</div>`;
          };

          // ---- Dữ liệu đã chuẩn hoá ----
          const armedState = getValidState('chuong_bao_trom_dang_bat');
          const alertState = getValidState('co_su_kien_bao_trom');
          const alertCountState = getValidState('so_canh_bao_tren_xe');
          const fwState = getValidState('co_ban_cap_nhat_firmware');
          const peakTempRaw = getValidState('nhiet_do_pin_cao_nhat');
          const thrTempRaw = getValidState('nguong_nhiet_do_pin');
          const peakTempHot = (peakTempRaw !== null && thrTempRaw !== null
              && Number(peakTempRaw) >= Number(thrTempRaw) - 5);

          const html = [
              group('An ninh', 'mdi:shield-lock-outline', [
                  row('Chuông báo trộm', onOff(armedState), isOn(armedState) ? '#10b981' : '#64748b'),
                  row('Sự kiện trộm', alertState === null ? null : (isOn(alertState) ? 'CÓ SỰ KIỆN' : 'Không có'), isOn(alertState) ? '#dc2626' : '#10b981'),
                  block('Nội dung', getValidState('noi_dung_canh_bao_trom'), '#dc2626'),
                  row('Thời điểm', fmtEpoch(getValidState('thoi_diem_canh_bao_trom'))),
                  row('Thông báo chưa đọc', yesNo(getValidState('co_thong_bao_chua_doc')), '#2563eb'),
              ], '#ef4444'),
              group('Cảnh báo trên xe', 'mdi:alert-outline', [
                  row('Số cảnh báo', alertCountState === null ? null : (alerts > 0 ? num(alerts) : '0'), alerts > 0 ? '#f59e0b' : '#10b981'),
                  block('Nội dung', getValidState('noi_dung_canh_bao'), '#f59e0b'),
              ], '#f59e0b'),
              group('Sức khỏe pin', 'mdi:battery-heart-variant', [
                  row('Hãng pin', getValidState('hang_pin')),
                  row('Cân bằng cell', tr(getValidState('can_bang_cell_pin'))),
                  row('Ắc quy 12V', tr(getValidState('ac_quy_12v'))),
                  row('Nhiệt độ pin cao nhất', num(peakTempRaw, '°C'), peakTempHot ? '#dc2626' : '#10b981'),
                  row('Ngưỡng cảnh báo', num(thrTempRaw, '°C')),
                  block('Thói quen sạc', tr(getValidState('thoi_quen_sac_pin'))),
                  block('Thói quen lái', tr(getValidState('thoi_quen_lai_xe'))),
                  block('Thói quen đỗ xe', tr(getValidState('thoi_quen_do_xe'))),
              ], '#10b981'),
              group('Lần sạc gần nhất', 'mdi:ev-station', useHist ? [
                  row('Thời điểm', newest.date, '#0ea5e9'),
                  block('Trạm', newest.address),
                  row('Sạc vào', num(newest.kwh, 'kWh')),
                  row('Thời lượng', fmtMinutes(newest.duration)),
                  block('Nguồn', 'Lịch sử sạc VinFast (API "lần sạc gần nhất" đứng từ 14/09)'),
              ] : [
                  row('Thời điểm', fmtEpoch(getValidState('thoi_diem_sac_gan_nhat'))),
                  row('Kiểu sạc', tr(getValidState('kieu_sac_gan_nhat'))),
                  row('Kết quả', tr(getValidState('ket_qua_lan_sac_gan_nhat'))),
                  row('Thời lượng', fmtMinutes(getValidState('thoi_luong_sac_gan_nhat'))),
                  row('Công suất cao nhất', num(getValidState('cong_suat_sac_cao_nhat'), 'kW')),
              ], '#0ea5e9'),
              // Chỉ hiện khối lái xe an toàn khi API thực sự có điểm (API trả -1 khi chưa đủ dữ liệu)
              (score === null || score === undefined || Number(score) < 0) ? '' : group('Lái xe an toàn', 'mdi:steering', [
                  row('Điểm', num(score, 'điểm'), '#8b5cf6'),
                  row('Xếp hạng', tr(getValidState('xep_hang_lai_xe'))),
                  row('Kỳ tính', fmtDayRange(getValidState('ky_tinh_diem_lai_xe'))),
              ], '#8b5cf6'),
              group('Bảo hành & tài khoản', 'mdi:card-account-details-outline', [
                  row('Chủ xe', getValidState('chu_xe')),
                  row('SĐT', phone(getValidState('sdt_chu_xe'))),
                  row('Bảo hành từ', fmtDay(getValidState('bao_hanh_tu'))),
                  row('Bảo hành đến', fmtDay(getValidState('bao_hanh_den')), '#2563eb'),
                  row('Số năm', num(getValidState('so_nam_bao_hanh'), 'năm')),
                  row('Giới hạn km', num(getValidState('gioi_han_km_bao_hanh'), 'km')),
                  row('Số người lái', num(getValidState('so_nguoi_lai_duoc_cap_quyen'))),
              ], '#64748b'),
              group('Phần mềm & thuê pin', 'mdi:cellphone-cog', [
                  row('Bản T-Box', getValidState('phien_ban_t_box_sota')),
                  block('Gói phần mềm', getValidState('goi_phan_mem_hien_tai')),
                  row('Có bản cập nhật', fwState === null ? null : (fwOn ? 'Có' : 'Không'), fwOn ? '#2563eb' : '#10b981'),
                  row('Đang cập nhật', getValidState('firmware_dang_cap_nhat'), '#2563eb'),
                  row('Phí thuê pin', money(getValidState('phi_thue_pin_thang_nay'))),
                  row('Km trong kỳ', num(getValidState('km_di_trong_ky_thue_pin'), 'km')),
                  row('ODO đầu kỳ', num(getValidState('odo_dau_ky_thue_pin'), 'km')),
                  row('ODO cuối kỳ', num(getValidState('odo_cuoi_ky_thue_pin'), 'km')),
                  row('Kỳ thuê pin', getValidState('ky_thue_pin')),
              ], '#0f766e'),
          ].filter(Boolean).join('');

          // Bỏ đường kẻ ở hàng cuối cùng cho gọn
          const lastBorder = html.lastIndexOf(BORDER);
          const htmlClean = lastBorder < 0 ? html : html.slice(0, lastBorder) + html.slice(lastBorder + BORDER.length);

          host.innerHTML = htmlClean || `<div style="padding:12px; text-align:center; color:var(--secondary-text-color, #94a3b8); font-size:11px;">Chưa có dữ liệu mở rộng. Bấm "Làm mới dữ liệu mở rộng".</div>`;
      };

      const healthRefreshBtn = this.querySelector('#vf-health-refresh');
      if (healthRefreshBtn) {
          healthRefreshBtn.onclick = () => {
              const entityId = `button.${p}_lam_moi_mo_rong`;
              if (this._hass && this._hass.states[entityId]) {
                  this._hass.callService('button', 'press', { entity_id: entityId });
              } else {
                  alert(`Không tìm thấy nút làm mới (${entityId}). Khởi động lại Home Assistant nếu vừa nâng cấp component.`);
              }
          };
      }
      this.renderHealthPanel();

      const attachClick = (boxId, detailId, containerId) => {
          const el = this.querySelector(boxId);
          if (el) el.onclick = () => this.toggleExpand(boxId, detailId, containerId);
      };
      
      attachClick('#box-batt-range', '#detail-batt-range', '#detail-container-1');
      attachClick('#box-sensors', '#detail-sensors', '#detail-container-1');
      attachClick('#box-eff', '#detail-eff', '#detail-container-2');
      attachClick('#box-speed', '#detail-speed', '#detail-container-2'); 
      attachClick('#box-trip', '#detail-trip', '#detail-container-3');
      attachClick('#box-health', '#detail-health', '#detail-container-5');
      attachClick('#box-charge', '#detail-charge', '#detail-container-3'); 
      attachClick('#box-daily', '#detail-daily', '#detail-container-4');
      attachClick('#box-stats', '#detail-stats', '#detail-container-4');

      // Tự thu gọn thẻ: bấm ra ngoài thẻ đang mở (kể cả chỗ khác trong card) là đóng lại
      if (this._outsideClick) document.removeEventListener('click', this._outsideClick, true);
      this._outsideClick = (ev) => {
          const path = ev.composedPath ? ev.composedPath() : [ev.target];
          const inside = path.some(n => n && n.classList && (n.classList.contains('stat-box') || n.classList.contains('stat-detail-container')));
          if (inside) return;
          this.querySelectorAll('.stat-box').forEach(el => el.classList.remove('active-box'));
          this.querySelectorAll('.stat-detail-container').forEach(el => el.style.display = 'none');
          this.querySelectorAll('.stat-detail-content').forEach(el => el.style.display = 'none');
      };
      document.addEventListener('click', this._outsideClick, true);
      
      const periodBtns = this.querySelectorAll('.stats-period-btn');
      periodBtns.forEach(btn => {
          btn.onclick = (e) => {
              periodBtns.forEach(b => b.classList.remove('active'));
              e.target.classList.add('active');
              if (typeof this.renderStatsChart === 'function') this.renderStatsChart(e.target.dataset.period);
          };
      });

      const btnLocate = this.querySelector('#btn-locate');
      if (btnLocate) btnLocate.onclick = () => { 
        if(this._map && this._lastLat) this._map.setView([this._lastLat, this._lastLon], 15, {animate: true});
      };

      const btnStations = this.querySelector('#btn-stations');
      const btnFilter = this.querySelector('#btn-filter-station');

      if (btnFilter) {
          btnFilter.innerText = this._stationFilter;
          if (this._stationFilter === 'DC') btnFilter.style.color = '#dc2626';
          else if (this._stationFilter === 'AC') btnFilter.style.color = '#16a34a';
          else btnFilter.style.color = '#f59e0b';
          btnFilter.style.display = this._showStations ? 'flex' : 'none';
      }

      if (btnStations) {
          btnStations.onclick = () => {
              if (this._selectedDateStr !== 'LIVE') return;
              this._showStations = !this._showStations;
              localStorage.setItem('vf_show_stations', this._showStations);
              
              if(btnFilter) btnFilter.style.display = this._showStations ? 'flex' : 'none';
              
              if (this._showStations) {
                  this.renderStations();
                  if (this._map && this._currentStations && this._currentStations.length > 0) {
                      const lats = this._currentStations.map(s => s.lat);
                      const lngs = this._currentStations.map(s => s.lng);
                      if (this._lastLat && this._lastLon) { lats.push(this._lastLat); lngs.push(this._lastLon); }
                      const bounds = [[Math.min(...lats), Math.min(...lngs)], [Math.max(...lats), Math.max(...lngs)]];
                      this._map.fitBounds(bounds, {padding: [40, 40], maxZoom: 15});
                  }
              } else {
                  this._stationLayer.clearLayers();
              }
          };
      }
      
      if(btnFilter) {
          btnFilter.onclick = () => {
              if (this._selectedDateStr !== 'LIVE' || !this._showStations) return;
              if (this._stationFilter === 'ALL') { this._stationFilter = 'DC'; btnFilter.style.color = '#dc2626'; }
              else if (this._stationFilter === 'DC') { this._stationFilter = 'AC'; btnFilter.style.color = '#16a34a'; }
              else { this._stationFilter = 'ALL'; btnFilter.style.color = '#f59e0b'; }
              
              btnFilter.innerText = this._stationFilter;
              localStorage.setItem('vf_station_filter', this._stationFilter);
              this.renderStations();
          };
      }

      this._initRoutePlannerUI();

      const callServiceBtn = (btnId, domain, service, entityId) => {
          const btn = this.querySelector(btnId);
          if(btn) btn.onclick = () => { if(this._hass.states[entityId]) this._hass.callService(domain, service, { entity_id: entityId }); };
      };
      callServiceBtn('#btn-rc-lock', 'button', 'press', `button.${p}_khoa_cua`);
      callServiceBtn('#btn-rc-unlock', 'button', 'press', `button.${p}_mo_cua`);
      callServiceBtn('#btn-rc-horn', 'button', 'press', `button.${p}_bam_coi`);
      callServiceBtn('#btn-rc-lights', 'button', 'press', `button.${p}_nhay_den`);
      const remoteBar = this.querySelector('#vf-remote-controls');
      if (remoteBar) {
          const remoteEntities = [`button.${p}_khoa_cua`, `button.${p}_mo_cua`, `button.${p}_bam_coi`, `button.${p}_nhay_den`];
          remoteBar.style.display = remoteEntities.some(entityId => Boolean(this._hass.states[entityId])) ? 'flex' : 'none';
      }

      const btnReplay = this.querySelector('#btn-replay');
      const iconReplay = this.querySelector('#icon-replay');

      if(btnReplay && iconReplay) {
          btnReplay.onclick = () => {
              if (!this._map || !this._marker || !this._polyline) return;
              const segments = (this._replaySegments || []).filter(segment => Array.isArray(segment) && segment.length >= 2);
              if (!segments.length) return alert("Lộ trình hiện tại quá ngắn để phát lại!");
              this._replaySegmentsActive = segments;

              if (this._isReplaying && !this._isPaused) {
                  this._isPaused = true; cancelAnimationFrame(this._animationFrameId); iconReplay.setAttribute('icon', 'mdi:play-circle');
              } else if (this._isReplaying && this._isPaused) {
                  this._isPaused = false; iconReplay.setAttribute('icon', 'mdi:pause-circle');
                  this._lastReplayTime = performance.now(); this._animationFrameId = requestAnimationFrame(this._runAnimation);
              } else {
                  this._isReplaying = true; this._isPaused = false; this._currentReplaySegment = 0; this._currentReplayIdx = 0; this._replayElapsedMs = 0;
                  iconReplay.setAttribute('icon', 'mdi:pause-circle');
                  this._marker.setOpacity(1);
                  const firstPoint = segments[0][0];
                  this._map.setView([firstPoint[0], firstPoint[1]], 15);
                  this._lastReplayTime = performance.now(); this._animationFrameId = requestAnimationFrame(this._runAnimation);
              }
          };
      }

      const btnRouteMode = this.querySelector('#btn-route-mode');
      if (btnRouteMode) {
          btnRouteMode.onclick = null;
          btnRouteMode.disabled = true;
      }

      this._runAnimation = (timestamp) => {
          if (!this._isReplaying || this._isPaused) return;
          const segments = this._replaySegmentsActive;
          let segmentIndex = this._currentReplaySegment || 0;
          let coords = segments?.[segmentIndex];
          if (!coords || coords.length < 2) { this._isReplaying = false; return; }

          const frameMs = Math.min(250, Math.max(0, timestamp - (this._lastReplayTime || timestamp)));
          this._lastReplayTime = timestamp;
          this._replayElapsedMs = (this._replayElapsedMs || 0) + frameMs * 15.0;
          let idx = this._currentReplayIdx || 0;
          while (idx < coords.length - 2) {
              const currentTs = Number(coords[idx][3] || 0);
              const nextTs = Number(coords[idx + 1][3] || 0);
              const segmentMs = nextTs > currentTs ? nextTs - currentTs : 1000;
              if (this._replayElapsedMs < segmentMs) break;
              this._replayElapsedMs -= segmentMs;
              idx++;
          }
          this._currentReplayIdx = idx;
          const ptA = coords[idx];
          const ptB = coords[Math.min(idx + 1, coords.length - 1)];
          const tsA = Number(ptA[3] || 0);
          const tsB = Number(ptB[3] || 0);
          const segmentMs = tsB > tsA ? tsB - tsA : 1000;
          const progress = Math.max(0, Math.min(1, this._replayElapsedMs / segmentMs));
          const lat = ptA[0] + (ptB[0] - ptA[0]) * progress;
          const lon = ptA[1] + (ptB[1] - ptA[1]) * progress;
          const speedA = Number(ptA[2] || 0);
          const speed = speedA + (Number(ptB[2] || speedA) - speedA) * progress;
          const angle = this._smoothRotation(this.getBearing(ptA[0], ptA[1], ptB[0], ptB[1]));
          if (speedA > 0) this._marker.setIcon(this.getCarIcon(angle, speed));
          this._marker.setLatLng([lat, lon]);
          this._map.panTo([lat, lon], { animate: false });

          if (idx >= coords.length - 2 && progress >= 1) {
              if (segmentIndex < segments.length - 1) {
                  segmentIndex++;
                  coords = segments[segmentIndex];
                  this._currentReplaySegment = segmentIndex;
                  this._currentReplayIdx = 0;
                  this._replayElapsedMs = 0;
                  const nextStart = coords[0];
                  this._marker.setLatLng([nextStart[0], nextStart[1]]);
                  this._map.panTo([nextStart[0], nextStart[1]], { animate: false });
              } else {
                  this._isReplaying = false; this._isPaused = false;
                  iconReplay.setAttribute('icon', 'mdi:play-circle');
                  if (this._selectedDateStr !== 'LIVE') setTimeout(() => this._marker.setOpacity(0), 2000);
                  return;
              }
          }
          this._animationFrameId = requestAnimationFrame(this._runAnimation);
      };
      
      this.loadLeaflet();
      this.fetchTripHistory(vinStr);
      this.fetchChargeHistory(vinStr); 
    }

    const tracker = hass.states[`device_tracker.${p}_vi_tri_gps`];
    const lat = parseFloat(tracker?.attributes?.latitude ?? getValidState('vi_do_latitude') ?? 0);
    const lon = parseFloat(tracker?.attributes?.longitude ?? getValidState('kinh_do_longitude') ?? 0);
    let name = getValidState('bien_so_ten_xe_phu');
    if (!name || name === "0" || name === "1" || name.toLowerCase() === "unknown" || name === "none" || name.toLowerCase() === "vinfast") name = getValidState('ten_dinh_danh_xe');
    if (!name || name === "0" || name === "1" || name.toLowerCase() === "unknown" || name === "none" || name.toLowerCase() === "vinfast") name = getValidState('ten_dinh_danh_xe_mqtt');
    if (!name || name === "0" || name === "1" || name.toLowerCase() === "unknown" || name === "none" || name.toLowerCase() === "vinfast") name = getValidState('ten_dong_xe');
    if (!name || name === "0" || name === "1" || name.toLowerCase() === "unknown" || name === "none" || name.toLowerCase() === "vinfast") name = 'Xe VinFast';

    const statusObj = hass.states[`sensor.${p}_trang_thai_hoat_dong`];
    let statusTextRaw = statusObj ? statusObj.state : 'N/A'; let statusText = statusTextRaw;
    if (statusObj && statusObj.last_changed) statusText += ` ${formatTimeSince(statusObj.last_changed)}`;
    
    const gearState = getValidState('vi_tri_can_so') || 'P';
    let gear = 'P';
    if (gearState) {
        const gStr = String(gearState).toUpperCase();
        if (gStr.includes('P') || gStr === '1' || gStr.includes('ĐỖ')) gear = 'P';
        else if (gStr.includes('R') || gStr === '2' || gStr.includes('LÙI')) gear = 'R';
        else if (gStr.includes('N') || gStr === '3' || gStr.includes('MO')) gear = 'N';
        else if (gStr.includes('D') || gStr === '4' || gStr.includes('ĐI')) gear = 'D';
        else gear = gStr;
    }
    // VF3 không tạo entity "Tốc độ hiện tại" (sensor..._toc_do_hien_tai) nên cảm biến luôn rỗng,
    // lấy tốc độ của điểm cuối vệt GPS làm nguồn dự phòng.
    const speed = getValidState('toc_do_hien_tai') || '0';
    const trackPts = Array.isArray(this._rawRouteCoords) ? this._rawRouteCoords : [];
    const gpsSpeed = trackPts.length ? Math.round(Number(trackPts[trackPts.length - 1][2]) || 0) : 0;
    const speedNum = Math.round(Number(speed)) || gpsSpeed;
    const carModel = getValidState('ten_dong_xe') || "";
    
    const nameEl = this.querySelector('#vf-name');
    const weatherEl = this.querySelector('#vf-weather-text');
    const vehicleStatusEl = this.querySelector('#vf-vehicle-status');
    const weatherCondition = getValidState('thoi_tiet_hien_tai');
    const outsideTemp = getValidState('nhiet_do_ngoai_troi_gps');
    const readyRaw = (getValidState('trang_thai_lai_ready') || '').toLowerCase();
    let vehicleStatus = 'Đang đỗ';
    if (speedNum > 0 && (gear.includes('D') || gear.includes('R'))) vehicleStatus = 'Đang đi';
    else if ((gear.includes('D') || gear.includes('R') || gear.includes('N')) && speedNum === 0) vehicleStatus = 'Đang dừng';
    else if (readyRaw.includes('ready') || readyRaw.includes('sẵn sàng')) vehicleStatus = 'Sẵn sàng';

    if (nameEl) nameEl.textContent = name;
    if (weatherEl) weatherEl.textContent = outsideTemp && outsideTemp !== '--'
        ? `${outsideTemp}°C${weatherCondition ? ` · ${weatherCondition}` : ''}`
        : (weatherCondition || '--');
    if (vehicleStatusEl) vehicleStatusEl.textContent = vehicleStatus;

    const statBadgeEl = this.querySelector('#vf-status-badge');
    if(statBadgeEl) statBadgeEl.innerText = statusText;
    // [dsh] Badge biển báo: cấm dừng / cấm đỗ + giới hạn tốc độ (VietMap + OSM)
    const signItemEl = this.querySelector('#vf-sign-item');
    if (signItemEl) {
        const signStatus = getValidState('bien_bao_cam_dung_do');
        const signDetail = getValidState('chi_tiet_bien_bao');
        const speedLimit = getValidState('gioi_han_toc_do_tham_khao');
        const bad = signStatus && !/^Chưa|^Lỗi|^Không/.test(String(signStatus));
        if (bad) {
            const noStop = String(signStatus).indexOf('Cấm dừng') === 0;
            const iconEl = this.querySelector('#vf-sign-icon');
            const txtEl = this.querySelector('#vf-sign-text');
            if (iconEl) iconEl.setAttribute('icon', noStop ? 'mdi:parking-off' : 'mdi:parking');
            let txt = (noStop ? '🚫 ' : '🅿️ ') + signStatus;
            if (signDetail && String(signDetail).indexOf('Trái:') === 0) txt += ' (' + signDetail + ')';
            if (speedLimit && /^\d+$/.test(String(speedLimit))) txt += ' · GH ' + speedLimit + ' km/h';
            if (txtEl) txtEl.textContent = txt;
            signItemEl.style.display = 'flex';
            signItemEl.style.color = noStop ? '#dc2626' : '#f59e0b';
        } else {
            signItemEl.style.display = 'none';
        }
    }

    // [dsh] Cảnh báo đoạn cấm PHÍA TRƯỚC + vẽ lên bản đồ
    const nextM = getValidState('khoang_cach_bien_bao_toi');
    const aheadRaw = getAttr('bien_bao_phia_truoc', 'blocks_json');
    let aheadPts = [];
    try {
        const b = (typeof aheadRaw === 'string') ? JSON.parse(aheadRaw) : aheadRaw;
        aheadPts = (b && b.points) || [];
    } catch (e) { aheadPts = []; }
    if (nextM && /^[0-9]+(\.[0-9]+)?$/.test(String(nextM)) && signItemEl) {
        let worstAhead = 0;
        aheadPts.forEach(p => { const t = Math.max(p.left || 0, p.right || 0); if (t > worstAhead) worstAhead = t; });
        const txtEl2 = this.querySelector('#vf-sign-text');
        const iconEl2 = this.querySelector('#vf-sign-icon');
        if (iconEl2) iconEl2.setAttribute('icon', worstAhead === 2 ? 'mdi:parking-off' : 'mdi:parking');
        if (txtEl2) txtEl2.textContent = (worstAhead === 2 ? '🚫 Cấm dừng & cấm đỗ' : '🅿️ Cấm đỗ') + ' cách ' + Math.round(nextM) + ' m';
        signItemEl.style.display = 'flex';
        signItemEl.style.color = '#dc2626';
    }
    if (this._signLayer && typeof L !== 'undefined') {
        this._signLayer.clearLayers();
        if (aheadPts.length) {
            const linePts = [];
            aheadPts.forEach(p => {
                const t = Math.max(p.left || 0, p.right || 0);
                const color = (t === 2) ? '#dc2626' : (t === 1 ? '#f59e0b' : '#94a3b8');
                linePts.push([p.lat, p.lon]);
                const cm = L.circleMarker([p.lat, p.lon], {
                    radius: t > 0 ? 8 : 4, color: color, weight: 3,
                    fillColor: color, fillOpacity: t > 0 ? 0.55 : 0.15, opacity: t > 0 ? 1 : 0.5
                }).addTo(this._signLayer);
                const label = (t === 2) ? '🚫 Cấm dừng & cấm đỗ' : (t === 1 ? '🅿️ Cấm đỗ' : 'Không hạn chế');
                cm.bindPopup(label + ' · cách xe ' + p.dist + ' m' + (p.entry ? '<br>⛔ Đường cấm vào' : ''));
            });
            if (linePts.length > 1) {
                L.polyline(linePts, { color: '#dc2626', weight: 3, opacity: 0.4, dashArray: '6 6' }).addTo(this._signLayer);
            }
        }
    }
    
    const odoRaw = getValidState('tong_odo_mqtt') || getValidState('tong_odo');
    const odoEl = this.querySelector('#vf-odo-int');
    if(odoEl) odoEl.innerText = (odoRaw && !isNaN(odoRaw)) ? Math.floor(parseFloat(odoRaw)).toString() : '--';

    let rawImage = getValidState('hinh_anh_xe_url');
    if (rawImage && rawImage.includes('public.s3.connected-car.vinfast.vn')) {
        rawImage = rawImage.replace('http://', 'https://');
    }
    const imgEl = this.querySelector('#vf-car-img');
    if (imgEl) {
        if (rawImage && rawImage !== 'unknown' && !rawImage.includes('/user/user/')) {
            imgEl.src = rawImage;
        } else {
            imgEl.src = 'https://public.s3.connected-car.vinfast.vn/content/carimage/EI13_2024_CE18.png';
        }
    }

    const updateTire = (id, val) => {
      const el = this.querySelector(id);
      if(el) { if (val !== null && val !== 'unknown' && val !== '') { el.style.display = 'block'; el.querySelector('span').innerText = val; } else el.style.display = 'none'; }
    };
    updateTire('#tire-fl', getValidState('ap_suat_lop_truoc_trai')); updateTire('#tire-fr', getValidState('ap_suat_lop_truoc_phai')); 
    updateTire('#tire-rl', getValidState('ap_suat_lop_sau_trai')); updateTire('#tire-rr', getValidState('ap_suat_lop_sau_phai'));

    ['P','R','N','D'].forEach(g => {
      const el = this.querySelector(`#gear-${g}`);
      if(el) { if (gear.includes(g)) el.classList.add('active'); else el.classList.remove('active'); }
    });
    
    const speedEl = this.querySelector('#vf-speed-container');
    if (!this._isReplaying && speedEl) {
        const speedDisplayEl = this.querySelector('#vf-speed');
        if (gear.includes('P') || speedNum === 0) speedEl.style.display = 'none';
        else { speedEl.style.display = 'flex'; if (speedDisplayEl) speedDisplayEl.innerText = speedNum; }
    }

    const checkSensorState = (slugs, targetState) => {
        for (let s of slugs) { const state = getValidState(s); if (state && state.toLowerCase() === targetState.toLowerCase()) return true; }
        return false;
    };

    const doorsConfig = [
        { slugs: ['cua_tai_xe'], name: 'Cửa lái', icon: 'mdi:car-door' }, { slugs: ['cua_phu'], name: 'Cửa phụ', icon: 'mdi:car-door' },
        { slugs: ['cua_sau_tai_xe', 'cua_sau_trai'], name: 'Cửa sau T', icon: 'mdi:car-door' }, { slugs: ['cua_sau_phu', 'cua_sau_phai'], name: 'Cửa sau P', icon: 'mdi:car-door' },
        { slugs: ['cop_sau'], name: 'Cốp sau', icon: 'mdi:car-back' }, { slugs: ['nap_capo'], name: 'Capo', icon: 'mdi:car' },
        { slugs: ['kinh_tai_xe', 'cua_so_tai_xe'], name: 'Kính lái', icon: 'mdi:window-open' }
    ];

    const isParked = statusTextRaw.toLowerCase().includes('đỗ') || gear.includes('P');
    const isUnlocked = checkSensorState(['khoa_tong'], 'mở khóa') || checkSensorState(['khoa_tong'], 'chưa khóa');
    const openDoors = (!isParked || isUnlocked) ? doorsConfig.filter(d => checkSensorState(d.slugs, 'mở') || checkSensorState(d.slugs, 'đang mở')) : [];
    const doorsEl = this.querySelector('#vf-doors-container');
    if (doorsEl) {
        let securityHtml = '';
        if (openDoors.length === 0 && (!isParked || !isUnlocked)) securityHtml = `<div class="door-badge" style="color: #10b981; border-color: rgba(16, 185, 129, 0.3); background: rgba(255,255,255,0.7);"><ha-icon icon="mdi:shield-check-outline"></ha-icon> An toàn</div>`;
        else {
            if (openDoors.length > 0) securityHtml += openDoors.map(d => `<div class="door-badge open"><ha-icon icon="${d.icon}"></ha-icon> ${d.name}</div>`).join('');
            if (isParked && isUnlocked) securityHtml += `<div class="door-badge open warning"><ha-icon icon="mdi:lock-open-alert"></ha-icon> Chưa khóa xe</div>`;
        }
        doorsEl.innerHTML = securityHtml;
    }

    const chargingBanner = this.querySelector('#vf-charging-banner');
    const isCharging = statusTextRaw && (statusTextRaw.toLowerCase().includes('sạc') || statusTextRaw.toLowerCase().includes('hoàn tất'));
    
    if (isCharging && chargingBanner && !statusTextRaw.toLowerCase().includes('không')) {
        chargingBanner.style.display = 'flex';
        let chargeLimit = getValidState('muc_tieu_sac_target') || '--'; 
        const chargeTimeRemain = getValidState('thoi_gian_sac_con_lai');
        
        const chargeLimitEl = this.querySelector('#vf-charge-limit'); 
        const chargeTimeEl = this.querySelector('#vf-charge-time'); 
        const chargeStatusTextEl = this.querySelector('#vf-charge-status-text'); 
        const powerEl = this.querySelector('#vf-charge-power');
        
        if (chargeLimitEl) chargeLimitEl.innerText = chargeLimit !== '--' ? `${chargeLimit}%` : '--';
        if (chargeTimeEl) chargeTimeEl.innerText = (chargeTimeRemain && chargeTimeRemain !== 'unknown') ? `${chargeTimeRemain}` : '--';
        if (chargeStatusTextEl) chargeStatusTextEl.innerText = statusTextRaw.toLowerCase().includes('đầy') || statusTextRaw.toLowerCase().includes('hoàn tất') ? "Đã sạc đầy" : "Hệ thống đang sạc";
        
        let pwr = getValidState('cong_suat_sac_hien_tai') || getValidState('cong_suat_sac_trung_binh_lan_cuoi') || getValidState('cong_suat_sac_tram') || getValidState('cong_suat_sac');
        if (powerEl) powerEl.innerText = pwr ? `${pwr} kW` : 'Đang tính...';
    } else if (chargingBanner) {
        chargingBanner.style.display = 'none';
    }

    const batt = getValidState('phan_tram_pin');
    let range = getValidState('quang_duong_du_kien');
    if (!range || range === '0' || range === '0.0' || range === '--' || range === 'unknown') {
        range = getValidState('quang_duong_con_lai_theo_hieu_suat');
        if (!range || range === '0' || range === '0.0' || range === '--' || range === 'unknown') range = getValidState('quang_duong_cong_bo_max');
    }
    const trip = getValidState('quang_duong_chuyen_di_trip');
    const tripEnergy = getValidState('dien_nang_tieu_thu_trip');
    const effKwh = getValidState('hieu_suat_tieu_thu_trung_binh_xe') || '--';
    this._lifetimeEfficiency = effKwh;
    const effRangePerPercent = getValidState('quang_duong_di_duoc_moi_1_pin') || '--';

    if (!this._effToggleTimer) {
        this._effToggleTimer = setInterval(() => {
            this._effToggleState = !this._effToggleState;
            const elements = [
                { el: this.querySelector('#vf-stat-eff'), lbl: this.querySelector('#lbl-eff') },
                { el: this.querySelector('#vf-stat-batt-range'), lbl: this.querySelector('#lbl-batt-range'), icon: this.querySelector('#icon-batt-range') }
            ];
            elements.forEach(item => {
                if (item.el) {
                    item.el.style.opacity = '0'; 
                    setTimeout(() => {
                        if (item.lbl && item.lbl.id === 'lbl-eff') {
                            if (this._effToggleState) { item.el.innerHTML = `${effRangePerPercent}<span class="stat-unit">km/1%</span>`; item.lbl.innerText = "Mỗi 1% Pin"; item.lbl.style.color = "#3b82f6"; } 
                            else { item.el.innerHTML = `${effKwh}<span class="stat-unit">kWh/100km</span>`; item.lbl.innerText = "Hiệu suất TB"; item.lbl.style.color = "#6b7280"; }
                        } else if (item.lbl) {
                            if (this._effToggleState) { item.el.innerHTML = `${range && range!=='--' ? range : '--'}<span class="stat-unit">km</span>`; item.lbl.innerText = "PHẠM VI"; item.lbl.style.color = "#3b82f6"; if(item.icon) { item.icon.setAttribute('icon', 'mdi:map-marker-distance'); item.icon.style.color = "#3b82f6"; } } 
                            else { item.el.innerHTML = `${batt && batt!=='--' ? batt : '--'}<span class="stat-unit">%</span>`; item.lbl.innerText = "MỨC PIN"; item.lbl.style.color = "#10b981"; if(item.icon) { item.icon.setAttribute('icon', 'mdi:battery-charging-60'); item.icon.style.color = "#10b981"; } }
                        }
                        item.el.style.opacity = '1';
                    }, 300);
                }
            });
        }, 5000);
    }

    const renderStat = (id, val, unit) => { const el = this.querySelector(id); if(el) { if (val && val !== 'unknown' && val !== '--') el.innerHTML = `${val}<span class="stat-unit">${unit}</span>`; else el.innerHTML = '--'; } };
    renderStat('#vf-stat-batt-range', batt, '%');    renderStat('#vf-stat-trip', getValidState('quang_duong_chuyen_di_trip'), 'km');
    renderStat('#vf-stat-daily-dist', getValidState('api_daily_energy') || getValidState('nang_luong_tieu_thu_trong_ngay'), 'kWh');
    const dtDailyEnergyEl = this.querySelector('#dt-daily-energy'); 
    if (dtDailyEnergyEl) {
        let val = getValidState('nang_luong_tieu_thu_trong_ngay');
        dtDailyEnergyEl.innerText = (val !== null && val !== '') ? `${val} kWh` : '--';
    }
    
    let phanhTay = getValidState('phanh_tay') || getValidState('phanh_tay_dien_tu');
    if (carModel.toUpperCase().includes('VF3') || carModel.toUpperCase().includes('VF 3')) {
        if (gear.includes('P')) phanhTay = 'Kéo phanh tay'; else if (gear.includes('D') || gear.includes('R') || gear.includes('N')) phanhTay = 'Nhả phanh tay';
    }

    const sensorsToWatch = [
        { name: "Pin 12V", state: getValidState('pin_12v_ac_quy'), icon: "mdi:car-battery", unit: "%" }, { name: "Khóa tổng", state: getValidState('khoa_tong'), icon: "mdi:lock" },
        { name: "An ninh", state: getValidState('trang_thai_an_ninh'), icon: "mdi:shield-car" }, { name: "Phanh tay", state: phanhTay, icon: "mdi:car-brake-parking" },
        { name: "Cảnh báo", state: getValidState('den_nhay_canh_bao'), icon: "mdi:car-light-alert" }, { name: "Đèn pha", state: getValidState('trang_thai_den_pha'), icon: "mdi:car-light-high" }, { name: "Điều hòa", state: getValidState('trang_thai_dieu_hoa'), icon: "mdi:air-conditioner" },
        { name: "Cắm trại", state: getValidState('che_do_cam_trai_camp'), icon: "mdi:tent" }, { name: "Thú cưng", state: getValidState('che_do_thu_cung_pet'), icon: "mdi:paw" },
        { name: "Giao xe (Valet)", state: getValidState('che_do_giao_xe_valet'), icon: "mdi:account-tie-hat" }
    ];

    let sensorHtml = ''; let warningCount = 0;
    sensorsToWatch.forEach(s => {
        if (s.state && s.state !== '--' && s.state !== 'unknown') {
            let color = '#475569'; const stLower = s.state.toLowerCase();
            if (stLower.includes('mở khóa') || stLower.includes('tắt an ninh') || stLower.includes('nhả phanh tay') || (stLower.includes('đang nháy') && s.name==='Cảnh báo') || (s.name==='Pin 12V' && parseFloat(s.state) < 40)) { color = '#ef4444'; if (s.name !== 'Điều hòa') warningCount++; } 
            else if (stLower.includes('khóa') || stLower.includes('bật an ninh') || stLower.includes('kéo phanh tay') || (stLower.includes('đang bật') && s.name !== 'Đèn pha')) { color = '#10b981'; }
            else if (stLower.includes('bật') && s.name === 'Đèn pha') { color = '#f59e0b'; }
            sensorHtml += `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--primary-background-color, white); padding:8px 12px; border-radius:8px; border:1px solid var(--divider-color, #e2e8f0);"><div style="display:flex; align-items:center; gap:8px; color:var(--secondary-text-color, #475569);"><ha-icon icon="${s.icon}" style="color:${color}; --mdc-icon-size:18px;"></ha-icon><span style="font-size:12px; font-weight:600;">${s.name}</span></div><b style="font-size:12px; color:${color};">${s.state} ${s.unit||''}</b></div>`;
        }
    });

    const sensorListEl = this.querySelector('#sensor-list-container');
    if (sensorListEl) sensorListEl.innerHTML = sensorHtml || `<div style="text-align:center; padding:10px; color:#94a3b8; font-size:12px;">Không có cảm biến khả dụng</div>`;
    const sensorSummaryEl = this.querySelector('#vf-stat-sensors');
    if (sensorSummaryEl) sensorSummaryEl.innerHTML = warningCount > 0 ? `<span style="color:#ef4444; font-size:14px;">${warningCount} Cảnh báo</span>` : `<span style="color:#10b981; font-size:14px;">Bình thường</span>`;

    const tripEff = parseFloat(getValidState('hieu_suat_tieu_thu_trip')) || 0;
    const capacity = parseFloat(getValidState('dung_luong_pin_thiet_ke')) || 0;
    const maxRange = parseFloat(getValidState('quang_duong_cong_bo_max')) || 0;
    const isTripActive = parseFloat(trip) > 0.5;

    let tripDegradationHtml = '--';
    if (isTripActive && tripEff > 0 && capacity > 0 && maxRange > 0) {
        const tripMaxRange = capacity / (tripEff / 100); let dropPct = ((maxRange - tripMaxRange) / maxRange) * 100; if (dropPct < 0) dropPct = 0; 
        tripDegradationHtml = `${dropPct.toFixed(1)}% <span style="font-size:10px; color:#94a3b8; font-weight:normal;">(Theo Trip)</span>`;
    } else {
        tripDegradationHtml = `${getValidState('kha_nang_chai_pin_theo_range_tham_khao') || '--'}% <span style="font-size:10px; color:#94a3b8; font-weight:normal;">(Vòng đời)</span>`;
    }

    const dtRangeDropTripEl = this.querySelector('#dt-range-drop-trip'); if (dtRangeDropTripEl) dtRangeDropTripEl.innerHTML = tripDegradationHtml;
    
    const pubSessions = parseInt(getValidState('so_lan_sac_tai_tram')) || 0; 
    const homeSessions = parseInt(getValidState('so_lan_sac_tai_nha')) || 0; 
    const totalSessions = parseInt(getValidState('tong_so_lan_sac')) || (pubSessions + homeSessions);
    
    const chargeCountEl = this.querySelector('#vf-stat-charge-count'); 
    if(chargeCountEl) chargeCountEl.innerHTML = `${totalSessions}<span class="stat-unit">lần</span>`;
    
    if (this._lastTotalSessions !== undefined && this._lastTotalSessions !== totalSessions) {
        this.fetchChargeHistory(vinStr);
    }
    this._lastTotalSessions = totalSessions;

    const dtSohEl = this.querySelector('#dt-soh'); if (dtSohEl) dtSohEl.innerText = getValidState('suc_khoe_pin_soh_tinh_toan') ? `${getValidState('suc_khoe_pin_soh_tinh_toan')}%` : '--';
    const dtChargeEffEl = this.querySelector('#dt-charge-eff'); if (dtChargeEffEl) dtChargeEffEl.innerText = getValidState('hieu_suat_sac_thuc_te_lan_cuoi') ? `${getValidState('hieu_suat_sac_thuc_te_lan_cuoi')}%` : '--';
    const dtChargeSocStartEl = this.querySelector('#dt-charge-soc-start'); if (dtChargeSocStartEl) dtChargeSocStartEl.innerText = `${getValidState('pin_luc_cam_sac_lan_cuoi') || '--'}%`;
    
    const dtChargeSocEndEl = this.querySelector('#dt-charge-soc-end');
    if (dtChargeSocEndEl) { 
        let endSoc = getValidState('pin_luc_rut_sac_lan_cuoi'); 
        if (isCharging) endSoc = batt; 
        dtChargeSocEndEl.innerText = `${endSoc || '--'}%`; 
    }
    
    const dtRangeMaxEl = this.querySelector('#dt-range-max'); if (dtRangeMaxEl) dtRangeMaxEl.innerText = `${getValidState('quang_duong_cong_bo_max') || '--'} km`;
    const dtRangeAiEl = this.querySelector('#dt-range-ai'); if (dtRangeAiEl) dtRangeAiEl.innerText = `${getValidState('quang_duong_thuc_te_day_100_pin') || '--'} km`;
    const dtTotalKwhEl = this.querySelector('#dt-total-kwh'); if (dtTotalKwhEl) dtTotalKwhEl.innerText = `${getValidState('tong_dien_nang_da_sac') || '--'} kWh`;
    const dtTotalCostEl = this.querySelector('#dt-total-cost'); if (dtTotalCostEl) dtTotalCostEl.innerText = `${getValidState('tong_chi_phi_sac_quy_doi') || '--'} VNĐ`;
    const dtTripAvgSpeedEl = this.querySelector('#dt-trip-avg-speed'); if (dtTripAvgSpeedEl) dtTripAvgSpeedEl.innerText = `${getValidState('toc_do_tb_chuyen_di') || '--'} km/h`;
    const dtTripEnergyEl = this.querySelector('#dt-trip-energy'); if (dtTripEnergyEl) dtTripEnergyEl.innerText = `${getValidState('dien_nang_tieu_thu_trip') || '--'} kWh`;

    const aiAdvisor = getValidState('co_van_xe_dien_ai');
    const aiContainer = this.querySelector('#vf-ai-advisor-container');
    const aiTextEl = this.querySelector('#vf-ai-text');
    const aiContentEl = this.querySelector('#vf-ai-content');
    const aiChevron = this.querySelector('#vf-ai-chevron');
    
    if (aiContainer && aiTextEl) {
        if (!aiAdvisor || aiAdvisor === 'DISABLED' || aiAdvisor === 'unavailable') aiContainer.style.display = 'none'; 
        else if (!aiAdvisor.includes('Hệ thống AI đang chờ') && !aiAdvisor.includes('Vui lòng nhập Google') && !aiAdvisor.includes('waiting')) {
            aiTextEl.innerText = aiAdvisor; aiContainer.style.display = 'block'; 
            if (this._lastAiMessage !== aiAdvisor) {
                this._lastAiMessage = aiAdvisor;
                if (aiContentEl) { aiContentEl.style.maxHeight = '500px'; aiContentEl.style.marginTop = '8px'; if (aiChevron) aiChevron.style.transform = 'rotate(0deg)'; }
            }
        } else aiContainer.style.display = 'none'; 
    }

    const addressEl = this.querySelector('#vf-current-address');
    if (addressEl) {
        let sensorAddress = getValidState('vi_tri_xe_dia_chi');
        if (sensorAddress && sensorAddress !== 'unknown') addressEl.innerText = sensorAddress;
        else if (Number.isFinite(lat) && Number.isFinite(lon) && (lat !== 0 || lon !== 0)) addressEl.innerText = `Tọa độ: ${lat.toFixed(5)}, ${lon.toFixed(5)}`;
        else addressEl.innerText = "Đang tìm vị trí...";
    }

    if (batt && !isNaN(batt)) {
        const battNum = parseFloat(batt); 
        const stageEl = this.querySelector('#vf-car-stage');
        const boxBatt = this.querySelector('#box-batt-range');
        
        if (battNum < 20) { 
            if (stageEl) stageEl.classList.add('low-battery'); 
            if (boxBatt) {
                boxBatt.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                boxBatt.style.borderColor = 'rgba(239, 68, 68, 0.4)';
            }
        } else { 
            if (stageEl) stageEl.classList.remove('low-battery'); 
            if (boxBatt) {
                boxBatt.style.removeProperty('background-color');
                boxBatt.style.removeProperty('border-color');
            }
        }
        
        if (this._smoothedRouteCoords && this._smoothedRouteCoords.length >= 2 && this._selectedDateStr === 'LIVE') {
            const lastPt = this._smoothedRouteCoords[this._smoothedRouteCoords.length - 1]; const prevPt = this._smoothedRouteCoords[this._smoothedRouteCoords.length - 2];
            const currentHeading = this.getBearing(prevPt[0], prevPt[1], lastPt[0], lastPt[1]);
            this.checkAndShowSmartSuggestion(battNum, currentHeading);
        } else this.checkAndShowSmartSuggestion(battNum, null);
    }

    if (this._map && lat && lon && typeof L !== 'undefined') {
      if (!this._isReplaying && this._selectedDateStr === 'LIVE') {
          // Mũi tên chỉ hướng xe đi: lấy hướng của đoạn cuối vệt GPS (2 điểm cách nhau >8m để bỏ rung GPS,
          // xe đỗ thì giữ nguyên hướng cũ). Hướng này là hướng di chuyển thật nên không cần đảo cho số R.
          // ponytail: chưa dùng heading trong tệp trip; đổi sang heading nếu route_json trả thêm cột đó.
          const livePts = Array.isArray(this._rawRouteCoords) ? this._rawRouteCoords : [];
          let targetAngle = this._currentAngle || 0;
          if (livePts.length >= 2) {
              const ptA = livePts[livePts.length - 2], ptB = livePts[livePts.length - 1];
              if (this._map.distance([ptA[0], ptA[1]], [ptB[0], ptB[1]]) > 8) {
                  targetAngle = this.getBearing(ptA[0], ptA[1], ptB[0], ptB[1]);
                  this._currentAngle = targetAngle;
              }
          }

          if (this._marker) {
              this._marker.setOpacity(1); 
              this._marker.setLatLng([lat, lon]);
              const iconEl = this._marker.getElement();
              if (iconEl) {
                  const smoothedAngle = this._smoothRotation(targetAngle);
                  const svg = iconEl.querySelector('.car-dir-svg'); if (svg) svg.style.transform = `rotate(${smoothedAngle}deg)`;
                  const badge = iconEl.querySelector('.car-speed-badge');
                  if (badge) { badge.style.display = (!gear.includes('P') && speedNum > 0) ? 'block' : 'none'; badge.innerText = `${speedNum} km/h`; }
              }
          }

          if (this._lastLat === null) this._map.setView([lat, lon], 15);
          this._lastLat = lat; this._lastLon = lon;
          
          const routeJsonStr = getAttr('lo_trinh_gps', 'route_json');
          if (routeJsonStr && this._polyline) {
              if (this._currentPolylineString !== routeJsonStr) {
                  this._currentPolylineString = routeJsonStr;
                  let parsedData = this.safeParseJSON(routeJsonStr);
                  this._rawRouteCoords = this.cleanRouteData(parsedData);
                  const gapSegments = this._splitRouteByGap(this._rawRouteCoords);
                  this._polyline.setLatLngs(gapSegments.map(seg => seg.map(p => [p[0], p[1]])));
              }
          }
      }

      if (this._selectedDateStr === 'LIVE') {
          const stationsStr = getAttr('tram_sac_lan_can', 'stations');
          if (stationsStr && stationsStr !== this._prevStationStr) {
              this._prevStationStr = stationsStr;
              let newStations = this.safeParseJSON(stationsStr);
              if (Array.isArray(newStations)) { this._currentStations = newStations; this.renderStations(); }
          }
          
          const liveIndicator = this.querySelector('#icon-live-indicator');
          const calIcon = this.querySelector('#icon-cal-mode');
          if(liveIndicator) liveIndicator.style.display = 'block';
          if(calIcon) calIcon.style.color = '#334155';
      } else {
          if (this._stationLayer) this._stationLayer.clearLayers();
          
          const liveIndicator = this.querySelector('#icon-live-indicator');
          const calIcon = this.querySelector('#icon-cal-mode');
          if(liveIndicator) liveIndicator.style.display = 'none';
          if(calIcon) calIcon.style.color = '#2563eb';
      }
    }

    // Thẻ "Tình trạng & bảo dưỡng": dữ liệu mở rộng về muộn / đổi sau khi card đã dựng,
    // trước đây panel chỉ vẽ 1 lần lúc init nên luôn hiển thị số liệu cũ.
    // ponytail: chỉ theo dõi các khoá hay đổi; thêm khoá mới vào đây nếu cần vẽ lại.
    if (this.renderHealthPanel) {
        const healthSig = ['so_canh_bao_tren_xe', 'co_su_kien_bao_trom', 'chuong_bao_trom_dang_bat', 'co_ban_cap_nhat_firmware',
            'diem_lai_xe_an_toan', 'thoi_diem_sac_gan_nhat', 'nhiet_do_pin_cao_nhat', 'phi_thue_pin_thang_nay',
            'odo_cuoi_ky_thue_pin', 'km_di_trong_ky_thue_pin', 'phien_ban_t_box_sota', 'co_thong_bao_chua_doc'].map(getValidState).join('|');
        if (healthSig !== this._healthSig) { this._healthSig = healthSig; this.renderHealthPanel(); }
    }

    this.updateDynamicTripStats();
  }
  renderTodayTrips() {
      const container = this.querySelector('#dt-trip-list');
      if (!container) return;
      const trips = [...(this._tripsData[this._todayStr] || [])];
      const state = (suffix) => this._hass?.states?.[`sensor.${this._entityPrefix}_${suffix}`]?.state;
      const activeDistance = Number(state('quang_duong_chuyen_di_trip') || 0);
      const activeEnergy = Number(state('dien_nang_tieu_thu_trip') || 0);
      if (activeDistance > 0.05) trips.unshift({ current: true, start_time_str: 'Đang chạy', distance: activeDistance, energy_used: activeEnergy });
      trips.sort((a, b) => Number(Boolean(b.current)) - Number(Boolean(a.current)) || String(a.start_time_str).localeCompare(String(b.start_time_str)));
      container.innerHTML = trips.length ? trips.map((trip, index) => {
          const distance = Number(trip.distance || 0);
          const energy = Number(trip.energy_used || 0);
          const efficiency = distance > 0 && energy > 0 ? `${(energy / distance * 100).toFixed(1)} kWh/100km` : '--';
          return `<div style="padding:8px 0;border-top:1px solid var(--divider-color,#e2e8f0);font-size:11px;">
              <div style="display:flex;justify-content:space-between;font-weight:800;"><span>${trip.current ? 'Chuyến hiện tại' : `Chuyến ${index + (activeDistance > 0.05 ? 0 : 1)}`}</span><span>${trip.start_time_str || '--:--'}${trip.end_time_str ? ` - ${trip.end_time_str}` : ''}</span></div>
              <div style="display:flex;justify-content:space-between;color:var(--secondary-text-color,#64748b);margin-top:3px;"><span>${distance.toFixed(2)} km</span><span>${energy.toFixed(2)} kWh</span><span>${efficiency}</span></div>
          </div>`;
      }).join('') : '<div style="padding:10px 0;text-align:center;color:#94a3b8;font-size:11px;">Chưa có trip hôm nay.</div>';
  }

  renderDailyConsumption() {
      const container = this.querySelector('#dt-daily-list');
      if (!container) return;
      const state = (suffix) => this._hass?.states?.[`sensor.${this._entityPrefix}_${suffix}`]?.state;
      const activeDistance = Number(state('quang_duong_chuyen_di_trip') || 0);
      const activeEnergy = Number(state('dien_nang_tieu_thu_trip') || 0);
      const rows = [];
      for (let offset = 0; offset < 30; offset++) {
          const date = new Date();
          date.setHours(0, 0, 0, 0);
          date.setDate(date.getDate() - offset);
          const dateStr = this.formatDate(date);
          const totals = (this._tripsData[dateStr] || []).reduce((sum, trip) => {
              sum.distance += Number(trip.distance || 0);
              sum.energy += Number(trip.energy_used || 0);
              return sum;
          }, { distance: 0, energy: 0 });
          if (offset === 0) {
              totals.distance += activeDistance;
              totals.energy += activeEnergy;
          }
          const efficiency = totals.distance > 0 && totals.energy > 0 ? `${(totals.energy / totals.distance * 100).toFixed(1)} kWh/100km` : '--';
          rows.push(`<div style="display:flex;justify-content:space-between;gap:6px;padding:7px 0;border-top:1px solid var(--divider-color,#e2e8f0);font-size:11px;"><span style="width:72px;font-weight:800;">${offset === 0 ? 'Hôm nay' : dateStr.slice(8) + '/' + dateStr.slice(5, 7)}</span><span>${totals.distance.toFixed(1)} km</span><span>${totals.energy.toFixed(2)} kWh</span><span>${efficiency}</span></div>`);
      }
      container.innerHTML = rows.join('');
  }

  renderStatsChart(days) {
      // 'all' = Toàn thời gian (không lọc ngày, gom theo tháng trên toàn bộ lịch sử)
      const isAll = String(days) === 'all';
      const selectedDays = isAll ? null : (Number(days) > 0 ? Number(days) : 7);
      const container = this.querySelector('#stats-chart-container');
      if (!container) return;

      const now = new Date();
      now.setHours(0,0,0,0);
      const past = new Date(now);
      if (!isAll) past.setDate(past.getDate() - selectedDays + 1);

      let totalDist = 0;
      let totalEnergy = 0;
      let dailyData = {};
      let tripCount = 0;

      const trendStateObj = this._hass && this._entityPrefix ? this._hass.states[`sensor.${this._entityPrefix}_du_lieu_xu_huong_lai_xe`] : null;
      let apiTrendData = null;
      if (trendStateObj && trendStateObj.attributes && trendStateObj.attributes.trend_json) {
          try {
              apiTrendData = typeof trendStateObj.attributes.trend_json === 'string' ? JSON.parse(trendStateObj.attributes.trend_json) : trendStateObj.attributes.trend_json;
          } catch(e) {}
      }

      // API chỉ có sẵn bucket 7/30/365 ngày -> 'Toàn thời gian' luôn tính từ lịch sử chuyến đi
      if (!isAll && apiTrendData && apiTrendData[String(selectedDays)]) {
          let periodData = apiTrendData[String(selectedDays)];
          totalDist = parseFloat(periodData.distance_km || 0);
          totalEnergy = parseFloat(periodData.energy_kwh || 0);
          let rawDays = periodData.raw && periodData.raw.days ? periodData.raw.days : [];

          rawDays.forEach(d => {
              let tDist = parseFloat(d.distance || d.totalDistance || d.km || 0);
              let tFuel = parseFloat(d.fuel || d.totalEnergy || d.energyConsumed || 0);
              let dTime = d.time;
              if (dTime) {
                  let dt = new Date(dTime * 1000);
                  let y = dt.getFullYear(), m = String(dt.getMonth()+1).padStart(2,'0'), day = String(dt.getDate()).padStart(2,'0');
                  let dateStr = `${y}-${m}-${day}`;
                  dailyData[dateStr] = { dist: tDist, energy: tFuel };
              }
          });
      } else {
          Object.keys(this._tripsData).forEach(dateStr => {
              const tripDate = new Date(dateStr);
              if (isAll || (tripDate >= past && tripDate <= now)) {
                  if (!dailyData[dateStr]) dailyData[dateStr] = { dist: 0, energy: 0 };
                  this._tripsData[dateStr].forEach(trip => {
                      let tDist = parseFloat(trip.distance || 0);
                      let tEnergy = parseFloat(trip.energy_used || 0);
                      // Tự động nội suy cho các chuyến đi cũ bị thiếu dữ liệu energy_used (fallback)
                      if (tEnergy === 0 && tDist > 0) {
                          // Dùng hiệu suất thực từ biến lưu sẵn thay vì hardcode 15 kWh/100km
                          const lifeEff = parseFloat(this._lifetimeEfficiency || 0);
                          if (lifeEff > 0 && lifeEff !== 15.0) {
                              tEnergy = (tDist / 100.0) * lifeEff; // Ước tính từ hiệu suất thực
                          }
                          // Nếu không có lifetime efficiency thực → để 0 (sẽ không tính hiệu suất)
                      }
                      dailyData[dateStr].dist += tDist;
                      dailyData[dateStr].energy += tEnergy;
                      totalDist += tDist;
                      totalEnergy += tEnergy;
                      tripCount++;
                  });
              }
          });
      }
      
      const lblDist = this.querySelector('#dt-stats-dist');
      const lblEnergy = this.querySelector('#dt-stats-energy');
      const lblEff = this.querySelector('#dt-stats-eff');
      const boxTotalDist = this.querySelector('#vf-stat-total-dist');
      const fmtKm = (v) => Number(v).toLocaleString('vi-VN', { maximumFractionDigits: 1 });
      const periodLabel = isAll ? 'toàn thời gian' : `${selectedDays} ngày qua`;

      if (lblDist) lblDist.innerText = `${fmtKm(totalDist)} km`;
      if (lblEnergy) lblEnergy.innerText = `${totalEnergy.toFixed(1)} kWh`;
      if (lblEff) lblEff.innerText = totalDist > 0 ? `${((totalEnergy / totalDist)*100).toFixed(1)} kWh/100km` : '--';
      if (boxTotalDist) boxTotalDist.innerHTML = `${fmtKm(totalDist)}<span class="stat-unit">km</span>`;
      
      let chartData = [];
      if (isAll) {
          // Gom theo tháng trên toàn bộ khoảng dữ liệu có thật (không giới hạn 12 tháng)
          let monthlyData = {};
          Object.keys(dailyData).forEach(dateStr => {
              let monthStr = dateStr.substring(0, 7);
              if (!monthlyData[monthStr]) monthlyData[monthStr] = { dist: 0, energy: 0 };
              monthlyData[monthStr].dist += dailyData[dateStr].dist;
              monthlyData[monthStr].energy += dailyData[dateStr].energy;
          });
          const months = Object.keys(monthlyData).sort();
          if (months.length) {
              let [y, m] = months[0].split('-').map(Number);
              const [ly, lm] = months[months.length - 1].split('-').map(Number);
              let guard = 0;
              while ((y < ly || (y === ly && m <= lm)) && guard++ < 240) {
                  const monthStr = `${y}-${String(m).padStart(2,'0')}`;
                  chartData.push({
                      label: `${m}/${String(y).slice(2)}`,
                      dist: monthlyData[monthStr] ? monthlyData[monthStr].dist : 0,
                      energy: monthlyData[monthStr] ? monthlyData[monthStr].energy : 0
                  });
                  m++; if (m > 12) { m = 1; y++; }
              }
          }
      } else if (selectedDays <= 30) {
          for (let i = 0; i < selectedDays; i++) {
              let d = new Date(past);
              d.setDate(d.getDate() + i);
              let y = d.getFullYear(), m = String(d.getMonth()+1).padStart(2,'0'), day = String(d.getDate()).padStart(2,'0');
              let dateStr = `${y}-${m}-${day}`;
              let displayLabel = `${day}/${m}`;
              chartData.push({
                  label: displayLabel,
                  dist: dailyData[dateStr] ? dailyData[dateStr].dist : 0,
                  energy: dailyData[dateStr] ? dailyData[dateStr].energy : 0
              });
          }
      } else {
          let monthlyData = {};
          Object.keys(dailyData).forEach(dateStr => {
              let monthStr = dateStr.substring(0, 7);
              if (!monthlyData[monthStr]) monthlyData[monthStr] = { dist: 0, energy: 0 };
              monthlyData[monthStr].dist += dailyData[dateStr].dist;
              monthlyData[monthStr].energy += dailyData[dateStr].energy;
          });
          for (let i = 0; i < 12; i++) {
              let d = new Date(now.getFullYear(), now.getMonth() - 11 + i, 1);
              let y = d.getFullYear(), m = String(d.getMonth()+1).padStart(2,'0');
              let monthStr = `${y}-${m}`;
              chartData.push({
                  label: `T${m}`,
                  dist: monthlyData[monthStr] ? monthlyData[monthStr].dist : 0,
                  energy: monthlyData[monthStr] ? monthlyData[monthStr].energy : 0
              });
          }
      }
      
      if (chartData.length === 0 || (totalDist === 0 && totalEnergy === 0)) {
          container.innerHTML = `<div style="text-align:center; width:100%; color:#94a3b8; font-size:11px;">Không có chuyến đi nào trong ${periodLabel}.</div>`;
          return;
      }
      
      let maxDist = Math.max(...chartData.map(d => d.dist));
      if (maxDist === 0) maxDist = 1;
      
      let html = '';
      chartData.forEach(d => {
          let heightPct = (d.dist / maxDist) * 100;
          if (d.dist > 0 && heightPct < 5) heightPct = 5;
          // Nhãn trên cột: >=100 km làm tròn, nhỏ hơn giữ 1 số lẻ; luôn có dấu phân cách nghìn
          let valLabel = d.dist > 0 ? fmtKm(d.dist >= 100 ? Math.round(d.dist) : d.dist) : '';
          html += `
              <div class="stats-bar-wrapper" title="${d.label}: ${fmtKm(d.dist)} km · ${d.energy.toFixed(1)} kWh">
                  <div class="stats-bar-val">${valLabel}</div>
                  <div class="stats-bar" style="height: ${heightPct}%"></div>
                  <div class="stats-bar-label">${d.label}</div>
              </div>
          `;
      });
      if (isAll) {
          html += `<div style="flex:0 0 auto; align-self:center; padding-left:10px; font-size:10px; color:var(--secondary-text-color,#64748b); white-space:nowrap;">${tripCount} chuyến<br>${chartData.length} tháng</div>`;
      }
      container.innerHTML = html;
  }

// Chú thích cho khối: Thống kê Dải Tốc Độ Tối Ưu (Đồng bộ cảm biến và sửa lỗi chiều dài chuỗi)
  updateDynamicTripStats() {
    const speedElTarget = this.querySelector('#vf-stat-speed');
    const dtSpeedChart = this.querySelector('#dt-speed-chart');
    const speedLbl = this.querySelector('#lbl-speed-title');
    
    const p = this._entityPrefix;
    if (!p || !this._hass) return;

    const globalSpeedSensor = this._hass.states[`sensor.${p}_hieu_suat_toc_do_toan_cuc`];
    let hasSensorData = false;
    let maxVal = 0;
    let bars = [];
    let speedBandStr = '--';

    if (globalSpeedSensor && globalSpeedSensor.state && globalSpeedSensor.state.startsWith('{')) {
        try {
            let effObj = JSON.parse(globalSpeedSensor.state);
            let minEff = 999;
            let bestBand = "--";
            
            for (let k of ["0-30", "30-50", "50-70", "70-90", ">90"]) {
                let val = parseFloat(effObj[k]) || 0;
                if (val > maxVal) maxVal = val;
                if (val > 0 && val < minEff) { minEff = val; bestBand = k; }
                bars.push({label: k, val: val, rawStr: val > 0 ? `${val} kWh/100km` : `0 kWh`});
            }
            
            if (speedElTarget) { 
                speedElTarget.innerHTML = `${bestBand}<span class="stat-unit">km/h</span>`; 
            }
            if (speedLbl) speedLbl.innerText = "DẢI TỐC ĐỘ TỐI ƯU TOÀN CỤC";
            hasSensorData = true;
        } catch(e) {}
    }
    
    if (!hasSensorData) {
        const speedSensor = this._hass.states[`sensor.${p}_dai_toc_do_toi_uu_nhat`] || this._hass.states[`sensor.${p}_toc_do_toi_uu_nhat`];
        speedBandStr = speedSensor ? speedSensor.state : '--';
        if (speedBandStr === 'unknown' || speedBandStr === 'unavailable') speedBandStr = '--';

        const sObj = speedSensor || this._hass.states[`sensor.${p}_co_van_xe_dien_ai`];
        if (sObj && sObj.attributes) {
            for (let key in sObj.attributes) {
                let lowerKey = key.toLowerCase();
                if ((lowerKey.includes('dải') || lowerKey.includes('dai_') || lowerKey.includes('km/h') || lowerKey.match(/^[0-9]+(-|_)[0-9]+/)) && !lowerKey.includes('quãng') && !lowerKey.includes('tiêu') && !lowerKey.includes('distance') && !lowerKey.includes('drop')) { 
                    let valStr = String(sObj.attributes[key]); 
                    let num = parseFloat(valStr.split(' ')[0]); 
                    if (!isNaN(num)) {
                        if (num > maxVal) maxVal = num; 
                        let label = key.replace(/Dải|dải|km\/h|_/ig, ' ').trim();
                        if(label.includes('-') || label.includes('>')) {
                             bars.push({label: label, val: num, rawStr: valStr}); 
                             hasSensorData = true;
                        }
                    }
                }
            }
        }

        if (hasSensorData) {
            if (speedElTarget && speedBandStr !== '--') { 
                let spd = String(speedBandStr).split(' km/h')[0]; 
                speedElTarget.innerHTML = `${spd}<span class="stat-unit">km/h</span>`; 
            } else if (speedElTarget) {
                speedElTarget.innerHTML = '--';
            }
            if (speedLbl) speedLbl.innerText = "DẢI TỐC ĐỘ TỐI ƯU";
        }
    }

    
    if (hasSensorData && bars.length > 0) {
        bars.sort((a,b) => {
           let aNum = parseInt(a.label.split('-')[0].replace('>', '')) || 0;
           let bNum = parseInt(b.label.split('-')[0].replace('>', '')) || 0;
           return aNum - bNum;
        });
        let htmlChart = '';
        bars.forEach(b => {
            let pct = maxVal > 0 ? Math.round((b.val / maxVal) * 100) : 0;
            let displayVal = b.unit ? `${b.val} km` : (b.rawStr ? b.rawStr : b.val);
            htmlChart += `<div style="display:flex; align-items:center; gap:8px;"><div style="width:35px; font-size:10px; text-align:right; font-weight:bold; color:var(--secondary-text-color, #475569);">${b.label}</div><div style="flex:1; background:var(--divider-color, #e2e8f0); height:8px; border-radius:4px; overflow:hidden;"><div style="width:${pct}%; height:100%; background:${pct === 100 ? '#eab308' : '#3b82f6'}; transition: width 0.5s;"></div></div><div style="width:65px; font-size:10px; font-weight:bold; color:var(--primary-text-color, #1e3a8a); text-align:left;">${displayVal}</div></div>`;
        });
        if (dtSpeedChart) dtSpeedChart.innerHTML = htmlChart;
    } else {
        if (dtSpeedChart) dtSpeedChart.innerHTML = `<div style="text-align:center; padding:10px; color:#94a3b8; font-size:11px;">Chưa đủ dữ liệu phân tích</div>`;
    }
  }
// Kết thúc khối.

  // =====================================================================
  // KHỐI: LỘ TRÌNH - DẪN ĐƯỜNG - TRẠM SẠC TRÊN TUYẾN - QUÃNG ĐƯỜNG CÒN LẠI
  // =====================================================================
  _sensorVal(suffix) {
      const p = this._entityPrefix;
      if (!p || !this._hass) return null;
      const s = this._hass.states[`sensor.${p}_${suffix}`];
      if (!s) return null;
      const v = s.state;
      if (v === undefined || v === null || v === '' || v === 'unknown' || v === 'unavailable' || v === '--') return null;
      return v;
  }

  _sensorNum(suffix) {
      const n = parseFloat(this._sensorVal(suffix));
      return Number.isFinite(n) ? n : null;
  }

  // Thông tin pin/phạm vi dùng cho bài toán lộ trình
  _rangeInfo() {
      const soc = this._sensorNum('phan_tram_pin');
      const cap = this._sensorNum('dung_luong_pin_thiet_ke') || 0;
      let range = this._sensorNum('quang_duong_du_kien');
      if (range === null || range <= 0) range = this._sensorNum('quang_duong_con_lai_thich_ung');
      if (range === null || range <= 0) {
          const full = this._sensorNum('quang_duong_thuc_te_day_100_pin') || this._sensorNum('quang_duong_cong_bo_max');
          if (full && soc) range = full * soc / 100;
      }
      const kmPerPct = (range && soc) ? range / soc : null;
      return { soc, cap, range: (range === null || range <= 0) ? null : range, kmPerPct };
  }

  _carLatLng() {
      if (this._lastLat && this._lastLon) return [this._lastLat, this._lastLon];
      const t = (this._hass && this._entityPrefix) ? this._hass.states[`device_tracker.${this._entityPrefix}_vi_tri_gps`] : null;
      const lat = parseFloat(t?.attributes?.latitude ?? this._sensorVal('vi_do_latitude'));
      const lon = parseFloat(t?.attributes?.longitude ?? this._sensorVal('kinh_do_longitude'));
      return (Number.isFinite(lat) && Number.isFinite(lon) && lat && lon) ? [lat, lon] : null;
  }

  _initRoutePlannerUI() {
      const btnPlan = this.querySelector('#btn-route-plan');
      const panel = this.querySelector('#vf-route-panel');
      if (!btnPlan || !panel) return;
      const input = this.querySelector('#vf-route-input');
      const statusEl = this.querySelector('#vf-route-status');

      this._setRouteStatus = (msg, color) => {
          if (!statusEl) return;
          if (!msg) { statusEl.style.display = 'none'; return; }
          statusEl.style.display = 'block';
          statusEl.style.color = color || '#64748b';
          statusEl.innerHTML = msg;
      };

      this._toggleRoutePanel = (open) => {
          const isOpen = (open === undefined) ? panel.style.display !== 'block' : !!open;
          panel.style.display = isOpen ? 'block' : 'none';
          btnPlan.style.color = isOpen ? '#2563eb' : '';
          if (!isOpen) this._setPickMode(false);
      };

      this._onMapPick = async (e) => {
          if (!this._pickDestMode) return;
          this._setPickMode(false);
          const lat = e.latlng.lat, lng = e.latlng.lng;
          if (input) input.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
          this._setRouteStatus('Đang lấy địa chỉ điểm đến...');
          const addr = await this.getAddressFromCoords(lat, lng);
          this._routeDest = { lat, lng, name: addr };
          this._setRouteStatus(`Điểm đến: ${addr}`);
          this.calculateRoutePlan();
      };

      btnPlan.onclick = () => {
          if (this._selectedDateStr !== 'LIVE') return;
          this._toggleRoutePanel();
      };
      const btnClose = this.querySelector('#btn-route-close');
      if (btnClose) btnClose.onclick = () => this._toggleRoutePanel(false);
      const btnPick = this.querySelector('#btn-route-pick');
      if (btnPick) btnPick.onclick = () => this._setPickMode(!this._pickDestMode);
      const btnGo = this.querySelector('#btn-route-go');
      if (btnGo) btnGo.onclick = () => this.calculateRoutePlan();
      if (input) input.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.calculateRoutePlan(); } };
  }

  _setPickMode(on) {
      this._pickDestMode = !!on;
      const btnPick = this.querySelector('#btn-route-pick');
      const mapEl = this.querySelector('#vf-map-canvas');
      if (btnPick) {
          btnPick.style.background = this._pickDestMode ? '#2563eb' : '#f1f5f9';
          btnPick.style.color = this._pickDestMode ? 'white' : '#334155';
          btnPick.innerText = this._pickDestMode ? 'Chạm lên bản đồ...' : 'Chọn trên bản đồ';
      }
      if (mapEl) mapEl.style.cursor = this._pickDestMode ? 'crosshair' : '';
      if (this._map) {
          if (this._pickDestMode && !this._mapClickBound) { this._map.on('click', this._onMapPick); this._mapClickBound = true; }
          else if (!this._pickDestMode && this._mapClickBound) { this._map.off('click', this._onMapPick); this._mapClickBound = false; }
      }
  }

  _parseCoord(s) {
      const m = String(s || '').trim().match(/^(-?\d{1,3}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)$/);
      if (!m) return null;
      const lat = parseFloat(m[1]), lng = parseFloat(m[2]);
      return (Math.abs(lat) <= 90 && Math.abs(lng) <= 180) ? [lat, lng] : null;
  }

  // Nhận diện: toạ độ thô / địa chỉ / link Google Maps (kể cả link có waypoints)
  // Trả về { origin, dest, waypoints, query }: origin có khi link tự chứa điểm xuất phát (link lộ trình /dir/)
  _parseGmapsText(text) {
      const t = String(text || '').trim();
      if (!t) return null;
      if (!/^https?:\/\//i.test(t)) {
          const c = this._parseCoord(t);
          return { origin: null, dest: c ? { lat: c[0], lng: c[1], name: null } : null, waypoints: [], query: c ? null : t };
      }
      const out = { origin: null, dest: null, waypoints: [], query: null };
      const d3 = t.match(/!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)/);
      if (d3) out.dest = { lat: parseFloat(d3[1]), lng: parseFloat(d3[2]), name: null };

      const dir = t.match(/\/dir\/([^?]+)/);
      if (dir) {
          const pts = decodeURIComponent(dir[1]).split('/').filter(Boolean).map(s => this._parseCoord(s)).filter(Boolean);
          if (pts.length >= 2) {
              out.origin = { lat: pts[0][0], lng: pts[0][1], name: null };
              if (!out.dest) out.dest = { lat: pts[pts.length - 1][0], lng: pts[pts.length - 1][1], name: null };
              out.waypoints = pts.slice(1, -1).map(p => ({ lat: p[0], lng: p[1], name: null }));
          } else if (pts.length === 1 && !out.dest) {
              out.dest = { lat: pts[0][0], lng: pts[0][1], name: null };
          }
      }
      const org = t.match(/[?&]origin=([^&]+)/);
      if (org) {
          const c = this._parseCoord(decodeURIComponent(org[1].replace(/\+/g, ' ')));
          if (c) out.origin = { lat: c[0], lng: c[1], name: null };
      }
      const wp = t.match(/[?&]waypoints=([^&]+)/);
      if (wp) {
          const list = decodeURIComponent(wp[1]).split('|').map(s => this._parseCoord(s)).filter(Boolean);
          if (list.length) out.waypoints = list.map(p => ({ lat: p[0], lng: p[1], name: null }));
      }
      if (!out.dest) {
          const qs = t.match(/[?&](?:destination|daddr|q|query|ll)=([^&]+)/);
          if (qs) {
              const v = decodeURIComponent(qs[1].replace(/\+/g, ' '));
              const c = this._parseCoord(v);
              if (c) out.dest = { lat: c[0], lng: c[1], name: null };
              else out.query = v;
          }
      }
      if (!out.dest) {
          const at = t.match(/@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/);
          if (at) out.dest = { lat: parseFloat(at[1]), lng: parseFloat(at[2]), name: null };
      }
      if (!out.dest && !out.query) out.query = t;
      return out;
  }

  // Link chia sẻ dạng rút gọn (maps.app.goo.gl) -> mở qua backend để lấy URL đầy đủ
  async _resolveShortLink(url) {
      if (!/(maps\.app\.goo\.gl|goo\.gl\/maps)/i.test(url)) return url;
      if (!this._hass) return url;
      try {
          const res = await this._hass.callApi('GET', `vinfast/resolve_url?u=${encodeURIComponent(url)}`);
          return (res && res.url) ? res.url : url;
      } catch (e) { return url; }
  }

  async _geocodeText(q) {
      const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&accept-language=vi&q=${encodeURIComponent(q)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Geocode HTTP ${res.status}`);
      const data = await res.json();
      if (!Array.isArray(data) || !data.length) throw new Error('Không tìm thấy địa điểm');
      return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon), name: data[0].display_name || q };
  }

  _cumulativeKm(coords) {
      const cum = [0];
      for (let i = 1; i < coords.length; i++) {
          cum.push(cum[i - 1] + this.getDistanceFromLatLonInM(coords[i - 1][0], coords[i - 1][1], coords[i][0], coords[i][1]) / 1000);
      }
      return cum;
  }

  async _fetchOsrmRoute(points) {
      // Nhiều máy chủ định tuyến OSRM (cùng API) để tự chuyển khi máy chủ demo bị chặn/timeout
      const endpoints = [
          'https://routing.openstreetmap.de/routed-car/route/v1/driving',
          'https://router.project-osrm.org/route/v1/driving'
      ];
      const path = points.map(p => `${p.lng},${p.lat}`).join(';');
      let lastErr = null;
      for (const base of endpoints) {
          try {
              const ctrl = new AbortController();
              const timer = setTimeout(() => ctrl.abort(), 15000);
              const res = await fetch(`${base}/${path}?overview=full&geometries=geojson&steps=false&alternatives=false`, { signal: ctrl.signal });
              clearTimeout(timer);
              if (!res.ok) throw new Error(`HTTP ${res.status}`);
              const data = await res.json();
              const r = data && data.routes && data.routes[0];
              if (!r || !r.geometry || !Array.isArray(r.geometry.coordinates)) throw new Error('Không có dữ liệu tuyến');
              const coords = r.geometry.coordinates.map(c => [c[1], c[0]]);
              return { km: r.distance / 1000, mins: r.duration / 60, coords, cum: this._cumulativeKm(coords) };
          } catch (e) {
              lastErr = e;
          }
      }
      throw new Error(`Không lấy được lộ trình (${lastErr && lastErr.message ? lastErr.message : lastErr})`);
  }

  // Lấy trạm sạc dọc tuyến: lấy mẫu điểm trên tuyến rồi hỏi backend
  async _fetchStationsAlong(coords, cum) {
      const total = cum[cum.length - 1];
      const maxPts = 32;
      // Mỗi điểm mẫu chỉ trả về ~20 trạm gần nhất: lấy mẫu dày (>=10 km) nhưng phải trải đều hết tuyến,
      // nếu không tuyến dài sẽ chỉ dò được đoạn đầu (lỗi cũ: kẹp 17 km -> hết trạm sau ~540 km)
      const stepKm = Math.max(10, total / (maxPts - 1));
      const pts = [];
      let i = 0;
      for (let d = 0; d <= total && pts.length < maxPts; d += stepKm) {
          while (i < cum.length - 1 && cum[i] < d) i++;
          pts.push(coords[i]);
      }
      if (!pts.length) pts.push(coords[0]);
      const q = pts.map(p => `${p[0].toFixed(4)},${p[1].toFixed(4)}`).join(';');
      const res = await this._hass.callApi('GET', `vinfast/stations_along?points=${encodeURIComponent(q)}`);
      return (Array.isArray(res) ? res : []).filter(s => s && Number.isFinite(Number(s.lat)) && Number.isFinite(Number(s.lng)));
  }

  // Tìm vị trí gần nhất trên tuyến: trả về km dọc tuyến và độ lệch so với tuyến
  _nearestRoute(lat, lng, coords, cum) {
      let best = Infinity, km = 0;
      for (let i = 0; i < coords.length; i++) {
          const d = this.getDistanceFromLatLonInM(lat, lng, coords[i][0], coords[i][1]) / 1000;
          if (d < best) { best = d; km = cum[i]; }
      }
      return { detour: best, km };
  }

  // Gắn "km dọc tuyến" + độ lệch tuyến cho từng trạm
  _annotateStations(stations, coords, cum) {
      const out = [];
      for (const s of stations) {
          const lat = Number(s.lat), lng = Number(s.lng);
          const near = this._nearestRoute(lat, lng, coords, cum);
          if (near.detour <= 6) out.push(Object.assign({}, s, { lat, lng, detour: near.detour, km: near.km }));
      }
      return out.sort((a, b) => a.km - b.km);
  }

  // Bài toán chọn điểm dừng sạc cho lộ trình dài:
  //  - Chia nhỏ lộ trình: mỗi chặng chỉ dùng ~75% quãng đường dự kiến (70-80%)
  //  - Tới trạm dự kiến còn ~20% pin
  //  - Mỗi lần sạc lên 85% (trong khoảng 80-90%), riêng chặng cuối sạc vừa đủ tới đích
  //  - Hết mỗi chặng lại tự tính trạm kế tiếp cho tới khi phủ hết lộ trình
  _solveChargingStops(totalKm, info, stations) {
      const soc0 = info.soc, kmPerPct = info.kmPerPct, cap = info.cap;
      const LEG_FRAC = 0.75;      // dùng 75% quãng đường dự kiến cho mỗi chặng
      const ARRIVE_SOC = 20;      // tới trạm còn ~20% pin
      const CHARGE_TARGET = 85;   // sạc mỗi lần tới 85%
      const CHARGE_MAX = 90;      // trần sạc cho phép
      // Quãng đường đi được của một chặng, tính theo % pin hiện có
      const legPctAt = (soc) => (soc > ARRIVE_SOC + 7 ? Math.min(soc * LEG_FRAC, soc - ARRIVE_SOC) : soc * LEG_FRAC);
      const reachAt = (soc) => Math.max(0, legPctAt(soc)) * kmPerPct;
      const stops = [];
      let pos = 0, socNow = soc0, guard = 0;
      // Số điểm dừng tối đa suy ra từ độ dài tuyến (lỗi cũ: kẹp cứng 10 -> tuyến >1400 km không phủ hết)
      const maxStops = Math.ceil(totalKm / Math.max(20, reachAt(CHARGE_TARGET) * 0.5)) + 3;

      while ((totalKm - pos) > reachAt(socNow) && guard++ < maxStops) {
          const reach = reachAt(socNow);
          const lo = pos + reach * 0.3;
          const hi = pos + reach;
          // Ưu tiên trạm ở cuối chặng; nếu không có thì nhận trạm gần hơn, cuối cùng nới tới giới hạn pin
          let cand = stations.filter(s => s.km > lo && s.km <= hi);
          if (!cand.length) cand = stations.filter(s => s.km > pos && s.km <= hi);
          if (!cand.length) cand = stations.filter(s => s.km > pos && s.km <= pos + socNow * kmPerPct * 0.98);
          if (!cand.length) break;
          const pick = cand.map(s => ({
              s,
              score: (s.km - pos) / Math.max(reach, 1) * 40
                   - s.detour * 6
                   + (s.power >= 20 ? 10 : 0)
                   + (s.power >= 60 ? 5 : 0)
                   + (s.avail > 0 ? 8 : -15)
          })).sort((a, b) => b.score - a.score)[0].s;

          const arriveSoc = Math.max(0, socNow - (pick.km - pos) / kmPerPct);
          const remain = totalKm - pick.km;
          let chargeTo = CHARGE_TARGET;
          if (remain <= reachAt(CHARGE_MAX)) {
              const need = ARRIVE_SOC + remain / kmPerPct;   // vừa đủ tới đích với ~20% pin
              chargeTo = Math.min(CHARGE_MAX, Math.max(Math.ceil(arriveSoc) + 5, Math.ceil(need)));
              // Đảm bảo chặng cuối thực sự phủ được quãng đường còn lại
              if (reachAt(chargeTo) < remain) chargeTo = Math.min(CHARGE_MAX, Math.ceil(remain / (LEG_FRAC * kmPerPct)));
          }
          const kwh = Math.max(0, (chargeTo - arriveSoc) / 100 * cap);
          const effKw = Math.min(pick.power || 11, 60) * 0.85;
          stops.push(Object.assign({}, pick, {
              arriveSoc, chargeTo, kwh, legKm: pick.km - pos,
              minutes: effKw > 0 ? Math.round(kwh / effKw * 60) : null
          }));
          pos = pick.km;
          socNow = chargeTo;
      }
      const reachLeft = reachAt(socNow);
      const covered = (totalKm - pos) <= reachLeft + 0.5;
      const socArrival = Math.max(0, socNow - (totalKm - pos) / kmPerPct);
      return { stops, covered, socArrival, reachLeft };
  }

  // Điểm có nằm trong Việt Nam không (ray casting trên bảng biên giới)
  _inVietnam(lat, lng) {
      let hit = false;
      for (let i = 0, j = VN_BORDER.length - 1; i < VN_BORDER.length; j = i++) {
          const yi = VN_BORDER[i][0], xi = VN_BORDER[i][1], yj = VN_BORDER[j][0], xj = VN_BORDER[j][1];
          if ((xi > lng) !== (xj > lng) && lat < (yj - yi) * (lng - xi) / (xj - xi) + yi) hit = !hit;
      }
      return hit;
  }

  // Lộ trình có đoạn nào ra ngoài Việt Nam không (lấy mẫu mỗi ~25 km)
  _routeLeavesVN(coords, cum) {
      if (!coords || !coords.length) return false;
      let next = 0;
      for (let i = 0; i < coords.length; i++) {
          if (cum[i] >= next || i === coords.length - 1) {
              if (!this._inVietnam(coords[i][0], coords[i][1])) return true;
              next = cum[i] + 25;
          }
      }
      return false;
  }

  // Vị trí tương đối của điểm P trên đoạn thẳng A->B (0 = A, 1 = B) và khoảng cách lệch khỏi đoạn
  _progressT(a, b, p) {
      const straight = this.getDistanceFromLatLonInM(a.lat, a.lng, b.lat, b.lng) / 1000;
      if (!straight) return 0;
      const dA = this.getDistanceFromLatLonInM(a.lat, a.lng, p.lat, p.lng) / 1000;
      const dB = this.getDistanceFromLatLonInM(p.lat, p.lng, b.lat, b.lng) / 1000;
      const t = (dA * dA + straight * straight - dB * dB) / (2 * straight * straight);
      const s = t * straight;
      return { t, perp: Math.sqrt(Math.max(0, dA * dA - s * s)) };
  }

  // Thành phố mốc trên quốc lộ chính: dùng để neo lộ trình trong Việt Nam
  _vnAnchors(a, b) {
      const cities = [
          ['Điện Biên', 21.39, 103.02], ['Sơn La', 21.33, 103.91], ['Lào Cai', 22.48, 103.97], ['Hà Giang', 22.82, 104.98],
          ['Hà Nội', 21.03, 105.85], ['Ninh Bình', 20.25, 105.97], ['Thanh Hóa', 19.81, 105.78], ['Vinh', 18.68, 105.68],
          ['Hà Tĩnh', 18.34, 105.90], ['Đồng Hới', 17.47, 106.60], ['Đông Hà', 16.82, 107.10], ['Huế', 16.46, 107.60],
          ['Đà Nẵng', 16.05, 108.22], ['Tam Kỳ', 15.57, 108.47], ['Quảng Ngãi', 15.12, 108.80], ['Quy Nhơn', 13.78, 109.22],
          ['Nha Trang', 12.24, 109.19], ['Phan Rang', 11.57, 108.99], ['Phan Thiết', 10.93, 108.10], ['Vũng Tàu', 10.35, 107.08],
          ['Đà Lạt', 11.94, 108.44], ['Buôn Ma Thuột', 12.68, 108.05], ['Pleiku', 13.98, 108.00], ['Kon Tum', 14.35, 108.00],
          ['Đồng Xoài', 11.53, 106.90], ['Tây Ninh', 11.36, 106.13], ['Biên Hòa', 10.95, 106.82], ['TP.HCM', 10.78, 106.70],
          ['Mỹ Tho', 10.36, 106.36], ['Cần Thơ', 10.03, 105.78], ['Rạch Giá', 10.01, 105.08], ['Cà Mau', 9.18, 105.15]
      ];
      const straight = this.getDistanceFromLatLonInM(a.lat, a.lng, b.lat, b.lng) / 1000;
      if (straight < 250) return [];
      const picks = [];
      for (const [name, lat, lng] of cities) {
          const g = this._progressT(a, b, { lat, lng });
          if (g.t < 0.1 || g.t > 0.9 || g.perp > 300) continue;
          picks.push({ name, lat, lng, t: g.t });
      }
      picks.sort((x, y) => x.t - y.t);
      if (picks.length <= 3) return picks;
      const step = picks.length / 3;
      return [picks[Math.floor(step * 0.5)], picks[Math.floor(step * 1.5)], picks[Math.min(picks.length - 1, Math.floor(step * 2.5))]];
  }

  // Lấy lộ trình; nếu tuyến đi qua nước khác thì neo lại qua các thành phố Việt Nam rồi tính lại
  async _fetchRouteInVN(points) {
      const route = await this._fetchOsrmRoute(points);
      if (!this._routeLeavesVN(route.coords, route.cum)) return { route, anchored: false, outside: false };
      const a = points[0], b = points[points.length - 1];
      const anchors = this._vnAnchors(a, b);
      if (!anchors.length) return { route, anchored: false, outside: true };
      // trộn điểm neo với các điểm qua của người dùng theo đúng thứ tự tiến độ
      const middle = anchors.concat(points.slice(1, -1).map(p => Object.assign({ t: this._progressT(a, b, p).t }, p)));
      middle.sort((x, y) => x.t - y.t);
      try {
          const r2 = await this._fetchOsrmRoute([a].concat(middle, [b]));
          if (!this._routeLeavesVN(r2.coords, r2.cum)) return { route: r2, anchored: true, outside: false, anchors };
      } catch (e) { /* giữ tuyến ban đầu */ }
      return { route, anchored: false, outside: true, anchors };
  }

  // Chặng nhỏ còn lại: từ vị trí xe hiện tại tới trạm sạc kế tiếp (hoặc tới đích)
  _nextLeg() {
      const plan = this._routePlan;
      const geo = this._routeGeo;
      const pos = this._carLatLng();
      if (!plan || !geo || !pos) return null;
      const near = this._nearestRoute(pos[0], pos[1], geo.coords, geo.cum);
      if (near.detour > 25) return null;                                   // xe không còn trên tuyến đã tính
      if (near.km > plan.km - 0.5) return null;                            // đã tới đích
      const stop = plan.stops.find(s => s.km > near.km + 0.5) || null;
      const target = stop || plan.dest;
      const kmLeft = (stop ? stop.km : plan.km) - near.km;
      const info = this._rangeInfo();
      const socNow = info.soc !== null ? info.soc : plan.info.soc;
      const socAt = info.kmPerPct ? Math.max(0, socNow - kmLeft / info.kmPerPct) : null;
      const label = stop ? `${stop.name} (⚡ ${stop.power} kW, trống ${stop.avail}/${stop.total})` : (plan.dest.name || 'Điểm đến');
      return {
          stop, kmLeft, socAt, label,
          url: this._gmapsUrl({ lat: pos[0], lng: pos[1] }, target, [])
      };
  }

  // Cập nhật dòng "chặng kế tiếp" khi xe chạy/sạc (chỉ vẽ lại khi vị trí hoặc pin đổi đủ nhiều)
  _refreshNextLeg() {
      const el = this.querySelector('#vf-route-next');
      if (!el || !this._routePlan) return;
      const pos = this._carLatLng();
      const posKey = pos ? `${pos[0].toFixed(4)},${pos[1].toFixed(4)},${this._rangeInfo().soc}` : 'none';
      if (posKey === this._lastLegPosKey) return;         // xe chưa đổi vị trí/pin: khỏi quét lại toàn tuyến
      this._lastLegPosKey = posKey;
      const leg = this._nextLeg();
      if (!leg) { el.innerHTML = ''; return; }
      const key = `${leg.kmLeft.toFixed(0)}|${leg.socAt === null ? '-' : Math.round(leg.socAt)}|${leg.stop ? leg.stop.name : 'dest'}`;
      if (key === this._lastLegKey) return;
      this._lastLegKey = key;
      const f1 = (v) => Number.isFinite(v) ? v.toFixed(1) : '--';
      const warn = leg.socAt !== null && leg.socAt < 10;
      el.innerHTML = `
          <div style="margin-top:8px; border:1px solid ${warn ? '#fca5a5' : '#bfdbfe'}; background:${warn ? '#fef2f2' : '#eff6ff'}; border-radius:8px; padding:8px;">
              <div style="font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:.5px;">Chặng kế tiếp</div>
              <div style="font-size:11px; font-weight:bold; color:#1e3a8a; margin-top:2px;">${leg.stop ? 'Trạm sạc: ' : 'Tới đích: '}${leg.label}</div>
              <div style="font-size:10px; color:#475569; margin-top:2px;">Còn ${f1(leg.kmLeft)} km${leg.socAt !== null ? ` • dự kiến tới nơi còn ~${Math.round(leg.socAt)}% pin` : ''}</div>
              <a href="${leg.url}" target="_blank" style="display:flex; align-items:center; justify-content:center; gap:4px; margin-top:6px; background:${warn ? '#dc2626' : '#0ea5e9'}; color:white; padding:6px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:11px;">
                  <ha-icon icon="mdi:navigation-variant" style="--mdc-icon-size:13px;"></ha-icon> ${leg.stop ? 'Dẫn tới trạm kế tiếp' : 'Dẫn tới điểm đến'}
              </a>
          </div>`;
  }

  async calculateRoutePlan() {
      if (this._routeBusy) return;
      const input = this.querySelector('#vf-route-input');
      const info = this._rangeInfo();
      if (info.range === null || info.soc === null) { this._setRouteStatus('Chưa có dữ liệu pin/phạm vi của xe.', '#dc2626'); return; }
      const text = input ? input.value.trim() : '';
      if (!text) { this._setRouteStatus('Nhập điểm đến hoặc chạm lên bản đồ để chọn.', '#dc2626'); return; }

      this._routeBusy = true;
      const btnGo = this.querySelector('#btn-route-go');
      if (btnGo) { btnGo.disabled = true; btnGo.innerText = 'Đang tính...'; }
      let origin = this._carLatLng();
      try {
          this._setRouteStatus('Đang phân tích điểm đến...');
          let parsed = this._parseGmapsText(text);
          if (parsed && parsed.query && /^https?:\/\//i.test(parsed.query)) {
              this._setRouteStatus('Đang mở link chia sẻ Google Maps...');
              parsed = this._parseGmapsText(await this._resolveShortLink(parsed.query));
          }
          if (parsed && parsed.query && !parsed.dest) {
              this._setRouteStatus('Đang tìm địa chỉ...');
              parsed.dest = await this._geocodeText(parsed.query);
          }
          if (!parsed || !parsed.dest) { this._setRouteStatus('Không xác định được điểm đến. Kiểm tra lại link/địa chỉ.', '#dc2626'); return; }
          this._routeDest = parsed.dest;

          // Link lộ trình /dir/ có sẵn điểm xuất phát -> đi đúng theo lộ trình Google đã chia sẻ
          let originLabel = 'vị trí xe';
          if (parsed.origin) {
              origin = [parsed.origin.lat, parsed.origin.lng];
              originLabel = 'điểm đầu của link';
          }
          if (!origin) { this._setRouteStatus('Chưa xác định được vị trí xe và link không có điểm xuất phát.', '#dc2626'); return; }

          const via = (parsed.waypoints || []).slice(0, 8);
          const points = [{ lat: origin[0], lng: origin[1] }].concat(via, [parsed.dest]);
          this._setRouteStatus('Đang lấy lộ trình...');
          const got = await this._fetchRouteInVN(points);
          const route = got.route;
          this._routeGeo = route;
          const anchors = (got.anchors || []).map(a => Object.assign({ anchor: true }, a));
          const viaKm = via.concat(anchors).map(v => Object.assign({}, v, this._nearestRoute(v.lat, v.lng, route.coords, route.cum)));

          let stations = [];
          this._setRouteStatus('Đang dò trạm sạc trên tuyến...');
          try {
              stations = this._annotateStations(await this._fetchStationsAlong(route.coords, route.cum), route.coords, route.cum);
          } catch (e) { stations = []; }

          const solved = this._solveChargingStops(route.km, info, stations);
          this._routePlan = {
              km: route.km, mins: route.mins, dest: parsed.dest, via: viaKm, originLabel,
              anchored: got.anchored, outside: got.outside,
              stops: solved.stops, covered: solved.covered, socArrival: solved.socArrival,
              info, origin, stationCount: stations.length
          };
          this._drawRoutePlan();
          this._renderRoutePlan();
          this._setRouteStatus(null);
      } catch (e) {
          this._setRouteStatus(`Lỗi tính lộ trình: ${e && e.message ? e.message : e}`, '#dc2626');
      } finally {
          this._routeBusy = false;
          if (btnGo) { btnGo.disabled = false; btnGo.innerText = 'Tính lộ trình'; }
      }
  }

  _gmapsUrl(origin, dest, viaPoints) {
      const fmt = (p) => `${Number(p.lat).toFixed(6)},${Number(p.lng).toFixed(6)}`;
      let url = `https://www.google.com/maps/dir/?api=1&origin=${fmt(origin)}&destination=${fmt(dest)}&travelmode=driving`;
      const seen = new Set();
      const wps = (viaPoints || []).filter(p => {
          if (!p) return false;
          const k = fmt(p);
          if (seen.has(k)) return false;
          seen.add(k);
          return true;
      });
      if (wps.length) url += `&waypoints=${wps.map(fmt).join('%7C')}`;
      return url;
  }

  _drawRoutePlan() {
      if (!this._map || typeof L === 'undefined' || !this._routeLayer) return;
      this._routeLayer.clearLayers();
      const plan = this._routePlan;
      if (!plan || !this._routeGeo) return;
      const line = this._routeGeo.coords;
      L.polyline(line, { color: '#7c3aed', weight: 5, opacity: 0.85, lineCap: 'round', lineJoin: 'round' }).addTo(this._routeLayer);
      L.marker([plan.dest.lat, plan.dest.lng], {
          icon: L.divIcon({
              className: '', iconSize: [26, 26], iconAnchor: [13, 13],
              html: `<div style="background:#dc2626; color:white; border:2px solid white; border-radius:50%; width:26px; height:26px; display:flex; align-items:center; justify-content:center; box-shadow:0 3px 6px rgba(0,0,0,0.3);"><ha-icon icon="mdi:flag-checkered" style="--mdc-icon-size:16px;"></ha-icon></div>`
          })
      }).bindPopup(`<b>Điểm đến</b><br>${plan.dest.name || `${plan.dest.lat.toFixed(5)}, ${plan.dest.lng.toFixed(5)}`}`).addTo(this._routeLayer);

      (plan.via || []).forEach((v, i) => {
          L.circleMarker([v.lat, v.lng], { radius: 5, color: '#2563eb', fillColor: '#ffffff', fillOpacity: 1, weight: 2 })
              .bindPopup(`Điểm qua ${i + 1} (theo link Google Maps)`).addTo(this._routeLayer);
      });

      plan.stops.forEach((s, i) => {
          L.marker([s.lat, s.lng], {
              icon: L.divIcon({
                  className: '', iconSize: [24, 24], iconAnchor: [12, 12],
                  html: `<div style="background:#f59e0b; color:white; border:2px solid white; border-radius:50%; width:24px; height:24px; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:bold; box-shadow:0 3px 6px rgba(0,0,0,0.3);">${i + 1}</div>`
              })
          }).bindPopup(`<b>${i + 1}. ${s.name}</b><br>⚡ ${s.power} kW • Trống ${s.avail}/${s.total}<br>🔋 Tới trạm ~${Math.round(s.arriveSoc)}% → sạc lên ${s.chargeTo}%<br><a href="${this._gmapsUrl({ lat: s.lat, lng: s.lng }, plan.dest, [])}" target="_blank">Chỉ đường tới trạm</a>`).addTo(this._routeLayer);
      });
      try { this._map.fitBounds(L.latLngBounds(line), { padding: [30, 30] }); } catch (e) { /* bỏ qua */ }
  }

  _renderRoutePlan() {
      const el = this.querySelector('#vf-route-result');
      const plan = this._routePlan;
      if (!el || !plan) return;
      const f1 = (v) => Number.isFinite(v) ? v.toFixed(1) : '--';
      const socArrival = plan.socArrival !== undefined ? plan.socArrival : (plan.info.kmPerPct
          ? plan.info.soc - plan.km / plan.info.kmPerPct
          : null);
      const enough = plan.covered !== false && plan.stops.length === 0;
      const verdictColor = enough ? '#16a34a' : (plan.covered === false ? '#dc2626' : '#f59e0b');
      const verdictText = enough
          ? `Đủ pin để tới nơi — dự kiến còn ~${Math.max(0, Math.round(socArrival))}% (~${f1(Math.max(0, plan.info.range - plan.km))} km)`
          : (plan.covered === false
              ? `Không đủ pin và chưa tìm được trạm sạc phù hợp trên tuyến — cần chia chặng hoặc sạc đầy trước khi đi`
              : `Không đủ pin — chia lộ trình thành ${plan.stops.length} chặng, tới trạm dự kiến còn ~20% pin`);

      const stopRows = plan.stops.map((s, i) => `
          <div style="border-top:1px dashed var(--divider-color, #e2e8f0); padding:6px 0;">
            <div style="display:flex; justify-content:space-between; gap:6px;">
              <b style="font-size:11px; color:var(--primary-text-color, #1e3a8a);">${i + 1}. ${s.name}</b>
              <span style="font-size:10px; color:#64748b; white-space:nowrap;">${f1(s.km)} km (chặng ${f1(s.legKm)} km)</span>
            </div>
            <div style="font-size:10px; color:var(--secondary-text-color, #475569); margin-top:2px; line-height:1.5;">
              ⚡ ${s.power} kW (${s.details || '--'}) • Trống ${s.avail}/${s.total} • Lệch tuyến ${f1(s.detour)} km<br>
              🔋 Tới trạm ~${Math.round(s.arriveSoc)}% → sạc lên ${s.chargeTo}%${s.minutes !== null ? ` (~${s.minutes} phút, ${f1(s.kwh)} kWh)` : ''}
            </div>
          </div>`).join('');

      const wps = (plan.via || []).concat(plan.stops).sort((a, b) => a.km - b.km);
      const btnUrl = this._gmapsUrl({ lat: plan.origin[0], lng: plan.origin[1] }, plan.dest, wps);
      const routeNote = plan.anchored
          ? `<div style="font-size:10px; color:#0369a1; margin-top:2px;">Đã neo lộ trình qua ${plan.via.filter(v => v.anchor).map(v => v.name).join(' → ') || 'quốc lộ Việt Nam'} để không đi qua Lào/Campuchia</div>`
          : (plan.outside ? `<div style="font-size:10px; color:#b45309; margin-top:2px;">Lộ trình có đoạn ra ngoài Việt Nam — kiểm tra lại điểm dừng trước khi đi</div>` : '');

      el.style.display = 'block';
      el.innerHTML = `
          <div style="display:flex; gap:8px; font-size:11px; color:var(--secondary-text-color, #475569);">
              <span>🛣️ <b style="color:var(--primary-text-color, #1e293b);">${f1(plan.km)} km</b></span>
              <span>⏱️ <b style="color:var(--primary-text-color, #1e293b);">${this.formatMins(Math.round(plan.mins))}</b></span>
              <span>🔋 <b style="color:var(--primary-text-color, #1e293b);">${Math.round(plan.info.soc)}%</b> (~${f1(plan.info.range)} km)</span>
              <span>📍 ${plan.originLabel || 'vị trí xe'}</span>
          </div>
          <div style="margin-top:6px; font-size:11px; font-weight:bold; color:${verdictColor};">
              ${verdictText}
          </div>
          ${(enough || plan.covered === false) ? '' : `<div style="font-size:10px; color:var(--secondary-text-color, #64748b); margin-top:2px;">Dự kiến tới đích còn ~${Math.max(0, Math.round(socArrival))}% • Mỗi chặng dùng ~75% quãng đường dự kiến • Chặng cuối ~${f1(plan.km - plan.stops[plan.stops.length - 1].km)} km • Đã dò ${plan.stationCount} trạm quanh tuyến</div>`}
          ${routeNote}
          ${stopRows}
          <div id="vf-route-next"></div>
          <a href="${btnUrl}" target="_blank" style="display:flex; align-items:center; justify-content:center; gap:4px; margin-top:8px; background:#2563eb; color:white; padding:8px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:11px;">
              <ha-icon icon="mdi:navigation-variant" style="--mdc-icon-size:14px;"></ha-icon> ${plan.stops.length ? 'Dẫn đường kèm điểm dừng sạc' : 'Dẫn đường bằng Google Maps'}
          </a>
          <button id="btn-route-clear" style="margin-top:6px; width:100%; background:#f1f5f9; color:#334155; border:none; border-radius:8px; padding:6px; font-weight:bold; font-size:11px; cursor:pointer;">Xoá lộ trình</button>
      `;
      const btnClear = el.querySelector('#btn-route-clear');
      if (btnClear) btnClear.onclick = () => this._clearRoutePlan(true);
      this._lastLegKey = null;
      this._lastLegPosKey = null;
      this._refreshNextLeg();
  }

  _clearRoutePlan(resetInput) {
      this._routePlan = null;
      this._routeGeo = null;
      this._routeDest = null;
      this._lastLegKey = null;
      this._lastLegPosKey = null;
      if (this._routeLayer) this._routeLayer.clearLayers();
      const el = this.querySelector('#vf-route-result');
      if (el) { el.style.display = 'none'; el.innerHTML = ''; }
      if (resetInput) {
          const input = this.querySelector('#vf-route-input');
          if (input) input.value = '';
      }
      if (this._setRouteStatus) this._setRouteStatus(null);
      this._setPickMode(false);
  }
  // Kết thúc khối.

  disconnectedCallback() {
      if (this._outsideClick) document.removeEventListener('click', this._outsideClick, true);
  }

  getCardSize() { return 8; }
}

if (!customElements.get('vinfast-digital-twin')) {
    customElements.define('vinfast-digital-twin', VinFastDigitalTwin);
}

// Chú thích cho khối: Thẻ Debug Log / Report JSON
class VinFastDebugCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error('Bạn cần khai báo entity của cảm biến System Debug Raw Data');
    }
    this.config = config;
    this.activeTab = 'log'; 
    this.filterText = '';
    this._logData = [];
    this._rawJsonData = {};
    
    this._aliases = JSON.parse(localStorage.getItem('vf_debug_aliases') || '{}');

    this._dictionary = {
        "34183_00001_00009": { name: "Mức Pin (SOC %)", parse: v => `${v}%` },
        "34180_00001_00011": { name: "Mức Pin BMS (SOC %)", parse: v => `${v}%` },
        "34199_00000_00000": { name: "ODO (km)", parse: v => `${v} km` },
        "34183_00001_00003": { name: "ODO (km)", parse: v => `${v} km` },
        "34180_00001_00021": { name: "Điện áp 12V", parse: v => `${v} V` },
        "34180_00001_00014": { name: "Nhiệt độ Pin HV", parse: v => `${v} °C` },
        "34220_00001_00001": { name: "Độ chai Pin (SOH %)", parse: v => `${v}%` },
        "34193_00001_00009": { name: "Quãng đường dự kiến", parse: v => `${v} km` },
        "34193_00001_00005": { name: "Trạng thái Sạc", parse: v => v == 1 ? "Đang sạc" : (v == 2 ? "Ngắt sạc" : "Lỗi/Rút súng") },

        "34183_00000_00001": { name: "Cửa Tổng", parse: v => v == 1 ? "Mở" : "Đóng" },
        "34206_00001_00001": { name: "Khóa cửa (Lock)", parse: v => v == 1 ? "Đã khóa" : "Chưa khóa" },
        "34234_00001_00003": { name: "Cốp sau (Trunk)", parse: v => v == 1 ? "Mở" : "Đóng" },
        "34234_00001_00002": { name: "Nắp Capo (Frunk)", parse: v => v == 1 ? "Mở" : "Đóng" },
        
        "34213_00002_00003": { name: "Kính Lái (Trước Trái)", parse: v => v == 1 ? "Mở" : "Đóng" },
        "34213_00002_00004": { name: "Kính Phụ (Trước Phải)", parse: v => v == 1 ? "Mở" : "Đóng" },
        "34213_00002_00005": { name: "Kính Sau Trái", parse: v => v == 1 ? "Mở" : "Đóng" },
        "34213_00002_00006": { name: "Kính Sau Phải", parse: v => v == 1 ? "Mở" : "Đóng" },

        "34196_00001_00003": { name: "Áp suất Lốp Trước Trái", parse: v => `${(v/10).toFixed(1)} Bar` },
        "34196_00001_00005": { name: "Áp suất Lốp Trước Phải", parse: v => `${(v/10).toFixed(1)} Bar` },
        "34196_00001_00007": { name: "Áp suất Lốp Sau Trái", parse: v => `${(v/10).toFixed(1)} Bar` },
        "34196_00001_00009": { name: "Áp suất Lốp Sau Phải", parse: v => `${(v/10).toFixed(1)} Bar` },

        "10351_00006_00050": { name: "Điều hòa (AC)", parse: v => v == 1 ? "Bật" : "Tắt" },
        "10351_00006_00052": { name: "Nhiệt độ Điều hòa", parse: v => `${v} °C` },
        "10351_00006_00015": { name: "Nhiệt độ Môi trường", parse: v => `${v} °C` },
        
        "56789_00001_00005": { name: "Đèn Pha", parse: v => v == 1 ? "Bật" : "Tắt" },
        "34185_00001_00001": { name: "GPS Lat", parse: v => v },
        "34185_00001_00002": { name: "GPS Lon", parse: v => v },
        "34185_00001_00003": { name: "Tốc độ (Speed)", parse: v => `${v} km/h` },
        "34185_00001_00004": { name: "Hướng di chuyển", parse: v => `${v}°` }
    };
  }

  set hass(hass) {
    this._hass = hass;
    const entityId = this.config.entity;
    const stateObj = hass.states[entityId];

    if (!stateObj) {
      this.innerHTML = `<ha-card><div style="padding: 20px; color: red;">Không tìm thấy thực thể: ${entityId}</div></ha-card>`;
      return;
    }

    if (!this.content) {
      this.initUI();
      this.content = true;
    }

    if (stateObj.attributes) {
        let tempRaw = {};
        for (let key in stateObj.attributes) {
            if (key !== "friendly_name" && key !== "icon" && key !== "Chi tiết") {
                tempRaw[key] = stateObj.attributes[key];
            }
        }
        this._rawJsonData = tempRaw;

        let newLogData = [];
        let nowStr = new Date().toLocaleTimeString('vi-VN', { hour12: false });
        
        for (let [code, val] of Object.entries(this._rawJsonData)) {
            let isExists = this._logData.find(item => item.code === code);
            if (!isExists || isExists.new_value !== val) {
                newLogData.push({
                    time: nowStr,
                    code: code,
                    old_value: isExists ? isExists.new_value : "NEW",
                    new_value: val,
                    status: (this._aliases[code] || this._dictionary[code]) ? "KNOWN" : "UNKNOWN"
                });
            }
        }
        
        if (newLogData.length > 0) {
            this._logData = [...newLogData, ...this._logData].slice(0, 100);
            this.renderBody();
        }
    }
    if (this._routePlan) this._refreshNextLeg();
  }

  initUI() {
    this.innerHTML = `
      <ha-card class="debug-card">
        <div class="debug-header">
          <div>
            <ha-icon icon="mdi:console-network" style="color:#10b981; margin-right:8px;"></ha-icon>
            VINFAST REVERSE ENGINEER
          </div>
          <div id="debug-status-text" class="debug-status">Đang tải dữ liệu...</div>
        </div>
        
        <div class="debug-toolbar">
          <input type="text" id="debug-search" class="debug-search" placeholder="🔍 Nhập mã (VD: 34213) hoặc tên để lọc...">
          <div class="debug-tabs">
            <button id="btn-tab-log" class="debug-tab active" data-target="log">Sự kiện Live</button>
            <button id="btn-tab-raw" class="debug-tab" data-target="raw">Raw JSON</button>
            <button id="btn-tab-report" class="debug-tab" data-target="report" style="color: #f59e0b;"><ha-icon icon="mdi:github" style="width:14px;height:14px;"></ha-icon> Báo cáo</button>
          </div>
        </div>

        <div class="debug-body">
          <div id="view-log" class="debug-view"></div>
          <pre id="view-raw" class="debug-view" style="display: none;"></pre>
          <div id="view-report" class="debug-view" style="display: none;"></div>
        </div>
      </ha-card>
    `;

    const style = document.createElement('style');
    style.textContent = `
      .debug-card { background: #0f172a; color: #e2e8f0; font-family: monospace; border-radius: 12px; overflow: hidden; box-shadow: inset 0 0 20px rgba(0,0,0,0.5); border: 1px solid #1e293b;}
      .debug-header { background: #1e293b; padding: 12px 16px; font-size: 14px; font-weight: bold; border-bottom: 1px solid #334155; display:flex; align-items:center; justify-content: space-between; letter-spacing: 1px; color:#10b981;}
      .debug-status { font-size: 11px; font-weight: normal; color: #94a3b8; text-transform: none; letter-spacing: 0;}
      
      .debug-toolbar { padding: 12px; background: #0f172a; border-bottom: 1px solid #1e293b; }
      .debug-search { width: 100%; padding: 10px; background: #1e293b; border: 1px solid #334155; border-radius: 6px; color: #38bdf8; font-family: monospace; font-size: 13px; outline: none; margin-bottom: 10px; transition: border 0.2s; box-sizing: border-box;}
      .debug-search:focus { border-color: #38bdf8; }
      
      .debug-tabs { display: flex; gap: 8px; }
      .debug-tab { background: #1e293b; border: 1px solid #334155; color: #94a3b8; padding: 8px 10px; border-radius: 6px; cursor: pointer; font-family: monospace; font-size: 12px; font-weight: bold; flex: 1; transition: all 0.2s; display: flex; justify-content: center; align-items: center; gap: 4px;}
      .debug-tab:hover { background: #334155; color: white;}
      .debug-tab.active { background: #38bdf8; color: #0f172a; border-color: #38bdf8;}
      .debug-tab.active[data-target="report"] { background: #f59e0b; border-color: #f59e0b; color: #0f172a;}
      
      .debug-body { padding: 12px; height: 500px; overflow-y: auto; }
      .debug-body::-webkit-scrollbar { width: 8px; }
      .debug-body::-webkit-scrollbar-track { background: #0f172a; }
      .debug-body::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
      
      /* Log Tab */
      .log-item { padding: 12px 10px; border-bottom: 1px dashed #1e293b; font-size: 13px; line-height: 1.5; display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;}
      .log-left { display: flex; flex-direction: column; flex: 1;}
      .log-time { color: #64748b; font-size: 11px; margin-bottom: 4px;}
      .log-code { color: #f43f5e; font-weight: bold; letter-spacing: 0.5px;}
      .log-name-input { background: transparent; border: 1px dashed #334155; color: #e2e8f0; font-family: monospace; font-size: 13px; padding: 4px; border-radius: 4px; width: 90%; outline: none;}
      .log-name-input:focus { border-color: #10b981; border-style: solid; background: rgba(16, 185, 129, 0.1); }
      
      .log-right { display: flex; flex-direction: column; align-items: flex-end; gap: 8px;}
      .log-val-box { background: #1e293b; padding: 4px 10px; border-radius: 20px; border: 1px solid #334155; display: flex; align-items: center;}
      .log-val-old { color: #94a3b8; text-decoration: line-through; margin: 0 4px;}
      .log-arrow { color: #10b981; margin: 0 4px;}
      .log-val-new { color: #10b981; font-weight: bold; font-size: 14px;}
      
      #view-raw { margin: 0; font-size: 13px; color: #38bdf8; white-space: pre-wrap; word-break: break-all;}

      /* Report Tab */
      .report-table { width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }
      .report-table th { background: #1e293b; padding: 8px; text-align: left; position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #334155; color: #94a3b8;}
      .report-table td { padding: 6px 8px; border-bottom: 1px solid #1e293b; vertical-align: middle; word-wrap: break-word;}
      .report-row.unknown { background: rgba(245, 158, 11, 0.05); }
      .report-row:hover { background: rgba(255,255,255,0.05); }
      .rep-input { width: 90%; background: #0f172a; color: #38bdf8; border: 1px solid #334155; padding: 6px; border-radius: 4px; font-family: monospace; outline: none; transition: border 0.2s;}
      .rep-input:focus { border-color: #f59e0b; background: rgba(245, 158, 11, 0.1); color: #fff;}
      
      .guide-box { background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 12px; border-radius: 8px; margin-bottom: 15px; color: #e2e8f0; font-size: 13px; line-height: 1.6; }
      .guide-step { font-weight: bold; color: #10b981;}
      
      #btn-submit-github { width: 100%; padding: 12px; margin-top: 15px; background: #24292e; color: white; border: 1px solid #444; border-radius: 8px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s;}
      #btn-submit-github:hover { background: #2ea043; border-color: #2ea043;}
    `;
    this.appendChild(style);

    const tabs = this.querySelectorAll('.debug-tab');
    const views = this.querySelectorAll('.debug-view');
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            tabs.forEach(t => t.classList.remove('active'));
            const target = e.currentTarget.getAttribute('data-target');
            e.currentTarget.classList.add('active');
            this.activeTab = target;
            
            views.forEach(v => v.style.display = 'none');
            this.querySelector(`#view-${target}`).style.display = 'block';
            this.renderBody();
        });
    });

    this.querySelector('#debug-search').addEventListener('input', (e) => {
      this.filterText = e.target.value.toLowerCase();
      this.renderBody();
    });

    this.querySelector('.debug-body').addEventListener('input', (e) => {
        if (e.target.classList.contains('log-name-input')) {
            const code = e.target.getAttribute('data-code');
            const newName = e.target.value;
            if (newName.trim() === '') delete this._aliases[code];
            else this._aliases[code] = newName;
            localStorage.setItem('vf_debug_aliases', JSON.stringify(this._aliases));
        }
    });

    this.querySelector('.debug-body').addEventListener('click', (e) => {
        const btnSubmit = e.target.closest('#btn-submit-github');
        if (btnSubmit) {
            let markdown = `### Báo cáo Giải mã Lệnh / Cảm biến mới\n\n`;
            markdown += `Tôi phát hiện một số mã lệnh mới từ thẻ Debug Card:\n\n`;
            markdown += `| Device Key | Giá trị RAW | Đề xuất Tên (Name) | Đề xuất Trạng thái |\n`;
            markdown += `| :--- | :--- | :--- | :--- |\n`;
            
            let issueCount = 0;
            const rows = this.querySelectorAll('.report-row');
            rows.forEach(row => {
                let k = row.getAttribute('data-key');
                let rv = row.getAttribute('data-raw');
                let name = row.querySelector('.rep-name').value.trim();
                let state = row.querySelector('.rep-state').value.trim();
                
                if (name !== "" || state !== "") {
                    markdown += `| \`${k}\` | \`${rv}\` | **${name || "_Chưa rõ_"}** | ${state || "_Chưa rõ_"} |\n`;
                    issueCount++;
                }
            });

            if (issueCount === 0) {
                alert("Hãy nhập Đề xuất Tên hoặc Trạng thái vào ít nhất 1 ô trống trước khi gửi báo cáo!");
                return;
            }

            markdown += `\n<details>\n<summary><b>JSON RAW Đính kèm (Dành cho Dev)</b></summary>\n\n`;
            markdown += `\`\`\`json\n${JSON.stringify(this._rawJsonData, null, 2)}\n\`\`\`\n`;
            markdown += `\n</details>\n`;

            let issueTitle = "Bổ sung mã lệnh cảm biến mới (từ Cộng đồng)";
            let githubBaseUrl = "https://github.com/thangnd85/vinfast-connected-car/issues/new";
            let encodedBody = encodeURIComponent(markdown);
            let finalUrl = githubBaseUrl;
            
            if (encodedBody.length < 4000) {
                finalUrl = `${githubBaseUrl}?title=${encodeURIComponent(issueTitle)}&body=${encodedBody}`;
            }

            let newTab = window.open(finalUrl, "_blank");

            navigator.clipboard.writeText(markdown).then(() => {
                btnSubmit.style.background = "#2ea043";
                btnSubmit.innerHTML = `<ha-icon icon="mdi:check-circle"></ha-icon> ĐÃ COPY & ĐÃ MỞ TAB GITHUB!`;

                if (!newTab || newTab.closed || typeof newTab.closed == 'undefined') {
                    alert("Trình duyệt hoặc App Home Assistant đã chặn mở cửa sổ mới! \nDữ liệu đã được lưu vào bộ nhớ tạm. Hãy tự mở link Github và dán báo cáo nhé.");
                }

                setTimeout(() => {
                    btnSubmit.style.background = "#24292e";
                    btnSubmit.innerHTML = `BƯỚC 1: COPY MÃ <ha-icon icon="mdi:arrow-right"></ha-icon> BƯỚC 2: MỞ ISSUE TRÊN GITHUB`;
                }, 3000);
            }).catch(err => {
                alert("Lỗi khi copy vào bộ nhớ tạm: " + err);
            });
        }
    });
  }

  renderBody() {
    const headerTitle = this.querySelector('#debug-status-text');
    if (headerTitle) {
        let totalCodes = Object.keys(this._rawJsonData).length;
        if (totalCodes > 0) headerTitle.innerText = `Phát hiện ${totalCodes} mã Active`;
    }

    if (this.activeTab === 'log') {
        const viewLog = this.querySelector('#view-log');
        if (this._logData.length === 0) {
            viewLog.innerHTML = `<div style="color:#64748b; text-align:center; margin-top:20px;">[ Bật thiết bị trên xe để bắt mã... ]</div>`;
            return;
        }

        let html = '';
        this._logData.forEach((item) => {
            const alias = this._aliases[item.code] || (this._dictionary[item.code] ? this._dictionary[item.code].name : "");
            
            if (this.filterText) {
                const searchStr = `${item.time} ${item.code} ${item.old_value} ${item.new_value} ${alias}`.toLowerCase();
                if (!searchStr.includes(this.filterText)) return;
            }

            html += `
                <div class="log-item">
                    <div class="log-left">
                        <span class="log-time">🕒 ${item.time} • <span class="log-code">${item.code}</span></span>
                        <input type="text" class="log-name-input" data-code="${item.code}" value="${this._aliases[item.code] || ''}" placeholder="${alias || '✍️ Đặt tên tùy chỉnh (Lưu Local)...'}">
                    </div>
                    <div class="log-right">
                        <div class="log-val-box">
                            <span class="log-val-old">${item.old_value}</span> 
                            <span class="log-arrow">➔</span> 
                            <span class="log-val-new">${item.new_value}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        viewLog.innerHTML = html || `<div style="color:#64748b; text-align:center; margin-top:20px;">[ Không tìm thấy ]</div>`;
    }

    if (this.activeTab === 'raw') {
        const viewRaw = this.querySelector('#view-raw');
        let displayJson = {};
        for (let [key, value] of Object.entries(this._rawJsonData)) {
            let dictName = this._dictionary[key] ? this._dictionary[key].name : "";
            let alias = this._aliases[key] || dictName;
            
            if (this.filterText && !key.toLowerCase().includes(this.filterText) && !String(value).toLowerCase().includes(this.filterText) && !alias.toLowerCase().includes(this.filterText)) {
                continue;
            }
            if (alias) displayJson[`${key} (${alias})`] = value;
            else displayJson[key] = value;
        }
        viewRaw.textContent = JSON.stringify(displayJson, null, 2);
    }

    if (this.activeTab === 'report') {
        const viewReport = this.querySelector('#view-report');
        let html = `
            <div class="guide-box">
                <div style="font-weight: bold; margin-bottom: 8px; color: #10b981; font-size: 14px;">
                    <ha-icon icon="mdi:bullhorn-outline" style="width: 18px; height: 18px; margin-bottom: 2px;"></ha-icon> HƯỚNG DẪN CỘNG ĐỒNG:
                </div>
                <div style="margin-bottom: 5px;"><span class="guide-step">BƯỚC 1:</span> Gõ dự đoán của bạn vào các ô trống (ưu tiên các mã <span style="color:#f59e0b; font-weight:bold;">Màu Cam</span> - chưa được giải mã).</div>
                <div style="margin-bottom: 5px;"><span class="guide-step">BƯỚC 2:</span> Bấm nút <b style="color:white;">COPY & MỞ GITHUB</b> ở cuối bảng.</div>
                <div><span class="guide-step">BƯỚC 3:</span> Trình duyệt sẽ mở tab Github Issue mới. Nếu chưa thấy nội dung được điền sẵn, hãy bấm <b style="color:#38bdf8;">Ctrl + V (Dán)</b> vào khung soạn thảo và bấm Submit!</div>
            </div>
            
            <table class="report-table">
                <thead>
                    <tr>
                        <th style="width: 20%">Mã Lệnh</th>
                        <th style="width: 25%">RAW</th>
                        <th style="width: 28%">Tên Đề xuất</th>
                        <th style="width: 27%">Trạng thái</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (let [key, val] of Object.entries(this._rawJsonData)) {
            let dictObj = this._dictionary[key];
            let dictName = dictObj ? dictObj.name : "";
            let dictState = dictObj ? dictObj.parse(val) : "";
            
            let aliasName = this._aliases[key] || "";
            let displayName = aliasName || dictName;
            let isUnknown = !dictObj ? 'unknown' : '';

            if (this.filterText && !key.toLowerCase().includes(this.filterText) && !String(val).toLowerCase().includes(this.filterText) && !displayName.toLowerCase().includes(this.filterText)) {
                continue;
            }

            let displayVal = typeof val === 'object' ? JSON.stringify(val) : val;

            html += `
                <tr class="report-row ${isUnknown}" data-key="${key}" data-raw='${displayVal}'>
                    <td style="color: #f43f5e; font-weight: bold;">${key}</td>
                    <td style="font-weight: bold; color: #e2e8f0;">${displayVal}</td>
                    <td><input type="text" class="rep-input rep-name" value="${displayName}" placeholder="Vd: Sưởi ghế..."></td>
                    <td><input type="text" class="rep-input rep-state" value="${dictState}" placeholder="Vd: Bật"></td>
                </tr>
            `;
        }

        html += `
                </tbody>
            </table>
            <button id="btn-submit-github">
                BƯỚC 1: COPY MÃ <ha-icon icon="mdi:arrow-right" style="margin:0 5px;\"></ha-icon> BƯỚC 2: MỞ ISSUE TRÊN GITHUB
            </button>
        `;
        viewReport.innerHTML = html;
    }
  }

  getCardSize() { return 8; }
}

if (!customElements.get('vinfast-debug-card')) {
    customElements.define('vinfast-debug-card', VinFastDebugCard);
}
// Kết thúc khối.
