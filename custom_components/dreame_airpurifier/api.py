"""Dreame Air Purifier Cloud API Client."""
import hashlib
import logging
import requests
import time

_LOGGER = logging.getLogger(__name__)

DREAME_SALT = "RAylYC%fmSKp7%Tq"
DREAME_USER_AGENT = "Dreame_Smarthome/2.1.9 (iPhone; iOS 18.4.1; Scale/3.00)"
DREAME_AUTH_BASIC = "Basic ZHJlYW1lX2FwcHYxOkFQXmR2QHpAU1FZVnhOODg="
DREAME_TENANT_ID = "000000"
DREAME_RLC = "1c80b3787b2266776bcdc481f37d8fa42ba10a30af81a6df-1"

# === MiOT Property Map for dreame.airp.u2513 (Dreame FP10) ===
# VERIFIED by live API testing

# siid 2: Air Purifier Control
PROP_POWER = {"siid": 2, "piid": 1}         # int: 1=on, 2=standby (read-only)
PROP_MODE = {"siid": 2, "piid": 3}          # int: 0=Auto, 2=Sleep, 3=Custom, 4=Pet
PROP_FAN_SPEED = {"siid": 2, "piid": 4}     # int: 1-10 fan speed level

# siid 3: Environment Sensors
PROP_HUMIDITY = {"siid": 3, "piid": 2}      # int: 0-100%
PROP_TEMPERATURE = {"siid": 3, "piid": 3}   # int: temperature (C or K depending on unit setting)
PROP_AQ_LEVEL = {"siid": 3, "piid": 4}      # int: 1-4 (1=excellent, 4=poor)
PROP_PM25 = {"siid": 3, "piid": 5}          # int: µg/m³
PROP_TVOC = {"siid": 3, "piid": 6}          # int: µg/m³

# siid 4: Filter & Hair Collection
PROP_FILTER_LIFE = {"siid": 4, "piid": 1}   # int: 0-100%
PROP_FILTER_DAYS = {"siid": 4, "piid": 2}   # int: total days
PROP_FILTER_USED = {"siid": 4, "piid": 3}   # int: 0=not used, 1=used (flag)
PROP_HAIR_BOX_LIFE = {"siid": 4, "piid": 5}     # int: 0-100% remaining
PROP_HAIR_BOX_DAYS = {"siid": 4, "piid": 6}     # int: days remaining

# siid 6: Device Settings
PROP_TIMEZONE = {"siid": 6, "piid": 1}      # string
PROP_DEVICE_LOCATION = {"siid": 6, "piid": 3}   # string
PROP_TEMP_UNIT = {"siid": 6, "piid": 4}     # int: 0=C, 1=F
PROP_LIGHT_BRIGHTNESS = {"siid": 6, "piid": 6}  # int: 0=off, 1=on(last), 30=dim, 50=natural, 80=bright
PROP_TIMER = {"siid": 6, "piid": 8}         # int: 0-12 hours
PROP_CHILD_LOCK = {"siid": 6, "piid": 10}   # int: 0=off, 1=on
PROP_WEIGHT_UNIT = {"siid": 6, "piid": 11}  # int: 0=kg, 1=lb
PROP_BREATHING_LIGHT = {"siid": 6, "piid": 12}  # int: 0=off, 1=on
PROP_BUZZER = {"siid": 6, "piid": 17}       # int: 0=off, 1=on

# siid 7: Filter Self-Cleaning
PROP_SELF_CLEANING_STATUS = {"siid": 7, "piid": 1}  # int: 0=off, 1=in progress, 2=finished

# Poll batches (small to avoid timeout)
POLL_BATCHES = [
    [PROP_POWER, PROP_MODE, PROP_FAN_SPEED],
    [PROP_HUMIDITY, PROP_TEMPERATURE, PROP_AQ_LEVEL, PROP_PM25, PROP_TVOC],
    [PROP_FILTER_LIFE, PROP_FILTER_DAYS, PROP_FILTER_USED],
    [PROP_HAIR_BOX_LIFE, PROP_HAIR_BOX_DAYS],
    [PROP_TIMER, PROP_CHILD_LOCK, PROP_BREATHING_LIGHT, PROP_BUZZER],
    [PROP_LIGHT_BRIGHTNESS, PROP_TEMP_UNIT, PROP_WEIGHT_UNIT],
    [PROP_SELF_CLEANING_STATUS],
]

# Mode mapping (VERIFIED)
MODE_AUTO = 0
MODE_SLEEP = 2
MODE_CUSTOM = 3
MODE_PET = 4

MODE_NAMES = {MODE_AUTO: "Auto", MODE_SLEEP: "Sleep", MODE_CUSTOM: "Custom", MODE_PET: "Pet"}
MODE_NAME_TO_VALUE = {v: k for k, v in MODE_NAMES.items()}

# Light brightness modes
LIGHT_OFF = 0
LIGHT_ON_LAST = 1
LIGHT_DIM = 30
LIGHT_NATURAL = 50
LIGHT_BRIGHT = 80

LIGHT_MODES = {LIGHT_OFF: "Off", LIGHT_DIM: "Dim", LIGHT_NATURAL: "Natural", LIGHT_BRIGHT: "Bright"}

# Air Quality levels
AQ_LEVEL_EXCELLENT = 1
AQ_LEVEL_GOOD = 2
AQ_LEVEL_MODERATE = 3
AQ_LEVEL_POOR = 4

AQ_LEVEL_NAMES = {AQ_LEVEL_EXCELLENT: "Excellent", AQ_LEVEL_GOOD: "Good", 
                  AQ_LEVEL_MODERATE: "Moderate", AQ_LEVEL_POOR: "Poor"}

# Temperature units
TEMP_UNIT_CELSIUS = 0
TEMP_UNIT_FAHRENHEIT = 1

TEMP_UNIT_NAMES = {TEMP_UNIT_CELSIUS: "C", TEMP_UNIT_FAHRENHEIT: "F"}

# Weight units
WEIGHT_UNIT_KG = 0
WEIGHT_UNIT_LB = 1

WEIGHT_UNIT_NAMES = {WEIGHT_UNIT_KG: "kg", WEIGHT_UNIT_LB: "lb"}

# Power control: use action with siid 2 aiid 1
ACTION_POWER = {"siid": 2, "aiid": 1}       # params: [{"piid": 1, "value": true/false}]

# Filter reset
ACTION_FILTER_RESET = {"siid": 4, "aiid": 1}

# Self-cleaning actions
ACTION_START_SELF_CLEANING = {"siid": 7, "aiid": 1}
ACTION_CONFIRM_SELF_CLEANING = {"siid": 7, "aiid": 2}


class DreameCloudAPI:
    """Client for the Dreame Cloud API."""

    def __init__(self, username: str, password: str, country: str = "us"):
        self._username = username
        self._password = password
        self._country = country
        self._session = requests.Session()
        self._access_token = None
        self._refresh_token = None
        self._uid = None
        self._tenant_id = DREAME_TENANT_ID
        self._token_expire = None

    @property
    def api_url(self) -> str:
        return f"https://{self._country}.iot.dreame.tech:13267"

    @property
    def logged_in(self) -> bool:
        return self._access_token is not None

    def login(self) -> bool:
        url = f"{self.api_url}/dreame-auth/oauth/token"
        pw_hash = hashlib.md5((self._password + DREAME_SALT).encode("utf-8")).hexdigest()
        data = f"platform=IOS&scope=all&grant_type=password&username={self._username}&password={pw_hash}&type=account"
        headers = {
            "User-Agent": DREAME_USER_AGENT, "Authorization": DREAME_AUTH_BASIC,
            "Tenant-Id": DREAME_TENANT_ID, "Content-Type": "application/x-www-form-urlencoded", "Accept": "*/*",
        }
        if self._country == "cn":
            headers["Dreame-Rlc"] = DREAME_RLC
        try:
            response = self._session.post(url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if "access_token" in result:
                    self._access_token = result["access_token"]
                    self._refresh_token = result.get("refresh_token")
                    self._uid = result.get("uid")
                    self._tenant_id = result.get("tenant_id", DREAME_TENANT_ID)
                    self._token_expire = time.time() + result.get("expires_in", 3600) - 120
                    return True
                _LOGGER.error("Login failed: %s", result)
            else:
                _LOGGER.error("Login failed (HTTP %s): %s", response.status_code, response.text)
        except Exception as ex:
            _LOGGER.error("Login error: %s", ex)
        return False

    def _refresh_login(self) -> bool:
        if self._refresh_token and self._token_expire and time.time() > self._token_expire:
            url = f"{self.api_url}/dreame-auth/oauth/token"
            data = f"platform=IOS&scope=all&grant_type=refresh_token&refresh_token={self._refresh_token}"
            headers = {"User-Agent": DREAME_USER_AGENT, "Authorization": DREAME_AUTH_BASIC,
                       "Tenant-Id": self._tenant_id, "Content-Type": "application/x-www-form-urlencoded"}
            try:
                r = self._session.post(url, headers=headers, data=data, timeout=10)
                if r.status_code == 200:
                    result = r.json()
                    if "access_token" in result:
                        self._access_token = result["access_token"]
                        self._refresh_token = result.get("refresh_token", self._refresh_token)
                        self._token_expire = time.time() + result.get("expires_in", 3600) - 120
                        return True
            except Exception as ex:
                _LOGGER.warning("Token refresh failed: %s", ex)
            return self.login()
        return True

    def _auth_headers(self) -> dict:
        return {"User-Agent": DREAME_USER_AGENT, "Authorization": DREAME_AUTH_BASIC,
                "Tenant-Id": self._tenant_id, "Dreame-Auth": self._access_token,
                "Content-Type": "application/json", "Accept": "*/*"}

    def get_devices(self) -> list | None:
        if not self._refresh_login():
            return None
        url = f"{self.api_url}/dreame-user-iot/iotuserbind/device/listV2"
        try:
            r = self._session.post(url, headers=self._auth_headers(), json={}, timeout=10)
            if r.status_code == 200:
                result = r.json()
                if result.get("code") == 0 and "data" in result:
                    return result["data"]["page"]["records"]
        except Exception as ex:
            _LOGGER.error("Failed to get devices: %s", ex)
        return None

    def get_purifiers(self) -> list:
        devices = self.get_devices()
        if not devices:
            return []
        return [d for d in devices if ".airp." in d.get("model", "")]

    def send_command(self, did: str, method: str, params, host: str = None):
        if not self._refresh_login():
            return None
        host_prefix = f"-{host.split('.')[0]}" if host else ""
        url = f"{self.api_url}/dreame-iot-com{host_prefix}/device/sendCommand"
        payload = {"did": str(did), "id": 1, "data": {"did": str(did), "id": 1, "method": method, "params": params}}
        try:
            r = self._session.post(url, headers=self._auth_headers(), json=payload, timeout=10)
            if r.status_code == 200:
                result = r.json()
                if result.get("code") == 0:
                    if result.get("data") and "result" in result["data"]:
                        return result["data"]["result"]
                    if result.get("success"):
                        return {"code": 0}
            elif r.status_code == 401:
                if self.login():
                    return self.send_command(did, method, params, host)
        except Exception as ex:
            _LOGGER.error("Command failed: %s", ex)
        return None

    def get_properties(self, did: str, properties: list, host: str = None) -> dict:
        params = [{"did": str(did), "siid": p["siid"], "piid": p["piid"]} for p in properties]
        result = self.send_command(did, "get_properties", params, host)
        values = {}
        if result and isinstance(result, list):
            for prop in result:
                if prop.get("code", -1) == 0:
                    values[(prop["siid"], prop["piid"])] = prop.get("value")
        return values

    def set_property(self, did: str, siid: int, piid: int, value, host: str = None) -> bool:
        result = self.send_command(did, "set_properties", [{"did": str(did), "siid": siid, "piid": piid, "value": value}], host)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get("code", -1) == 0
        return False

    def call_action(self, did: str, siid: int, aiid: int, params: list = None, host: str = None) -> bool:
        result = self.send_command(did, "action", {"did": str(did), "siid": siid, "aiid": aiid, "in": params or []}, host)
        if result:
            return result.get("code", -1) == 0 if isinstance(result, dict) else True
        return False


class DreameAirPurifier:
    """Represents a single Dreame Air Purifier device (FP10)."""

    def __init__(self, api: DreameCloudAPI, device_info: dict):
        self._api = api
        self._did = str(device_info["did"])
        self._host = device_info.get("bindDomain")
        self._model = device_info.get("model", "unknown")
        self._mac = device_info.get("mac", "")
        self._name = device_info.get("customName") or device_info.get("deviceInfo", {}).get("displayName", "Dreame Air Purifier")
        
        # Power and control
        self._power = False  # 1=on, 2=standby
        self._mode = MODE_AUTO
        self._fan_speed = 0  # 1-10
        
        # Environment sensors
        self._humidity = 0
        self._temperature = 0
        self._pm25 = 0
        self._aq_level = 0
        self._tvoc = 0
        
        # Filter
        self._filter_life = 100
        self._filter_days = 365
        self._filter_used = 0
        
        # Hair collection box
        self._hair_box_life = 100
        self._hair_box_days = 365
        
        # Device settings
        self._timer = 0
        self._child_lock = 0  # 0=off, 1=on
        self._breathing_light = 0  # 0=off, 1=on
        self._buzzer = 0  # 0=off, 1=on
        self._light_brightness = LIGHT_OFF
        self._temp_unit = TEMP_UNIT_CELSIUS
        self._weight_unit = WEIGHT_UNIT_KG
        
        # Self-cleaning
        self._self_cleaning_status = 0  # 0=off, 1=in progress, 2=finished
        
        self._available = True

    @property
    def unique_id(self): return self._mac.replace(":", "").lower()
    @property
    def name(self): return self._name
    @property
    def model(self): return self._model
    @property
    def device_id(self): return self._did
    @property
    def mac(self): return self._mac
    @property
    def available(self): return self._available
    
    @property
    def is_on(self) -> bool:
        """Device is on if power state is 1 (running)."""
        return self._power == 1
    
    @property
    def power_state(self) -> str:
        """Return power state as string."""
        return "On" if self._power == 1 else "Standby"
    
    @property
    def mode(self): return MODE_NAMES.get(self._mode, f"Unknown ({self._mode})")
    @property
    def mode_value(self): return self._mode
    
    @property
    def fan_speed(self): return self._fan_speed
    @property
    def fan_speed_percent(self): return max(0, self._fan_speed * 10) if self._fan_speed > 0 else 0
    
    @property
    def humidity(self): return self._humidity
    @property
    def temperature(self): return self._temperature
    @property
    def pm25(self): return self._pm25
    @property
    def air_quality_level(self): return self._aq_level
    @property
    def air_quality_name(self): return AQ_LEVEL_NAMES.get(self._aq_level, "Unknown")
    @property
    def tvoc(self): return self._tvoc
    
    @property
    def filter_life(self): return self._filter_life
    @property
    def filter_days_total(self): return self._filter_days
    @property
    def filter_used(self): return self._filter_used
    
    @property
    def hair_box_life(self): return self._hair_box_life
    @property
    def hair_box_days_total(self): return self._hair_box_days
    
    @property
    def timer(self): return self._timer
    @property
    def child_lock(self): return self._child_lock
    @property
    def breathing_light(self): return self._breathing_light
    @property
    def buzzer(self): return self._buzzer
    @property
    def light_brightness(self): return self._light_brightness
    @property
    def light_brightness_name(self): return LIGHT_MODES.get(self._light_brightness, "Off")
    @property
    def temp_unit(self): return self._temp_unit
    @property
    def temp_unit_name(self): return TEMP_UNIT_NAMES.get(self._temp_unit, "C")
    @property
    def weight_unit(self): return self._weight_unit
    @property
    def weight_unit_name(self): return WEIGHT_UNIT_NAMES.get(self._weight_unit, "kg")
    
    @property
    def self_cleaning_status(self): return self._self_cleaning_status
    @property
    def self_cleaning_status_name(self):
        if self._self_cleaning_status == 0:
            return "Off"
        elif self._self_cleaning_status == 1:
            return "In Progress"
        elif self._self_cleaning_status == 2:
            return "Finished"
        return "Unknown"

    def update(self) -> bool:
        """Fetch current state from device."""
        all_values = {}
        for batch in POLL_BATCHES:
            values = self._api.get_properties(self._did, batch, self._host)
            if values:
                all_values.update(values)
        
        if not all_values:
            self._available = False
            return False
        
        self._available = True
        
        # Power and control
        self._power = all_values.get((2, 1), 2)  # 1=on, 2=standby
        self._mode = all_values.get((2, 3), MODE_AUTO)
        self._fan_speed = all_values.get((2, 4), 0)
        
        # Environment sensors
        self._humidity = all_values.get((3, 2), 0)
        self._temperature = all_values.get((3, 3), 0)
        self._aq_level = all_values.get((3, 4), 0)
        self._pm25 = all_values.get((3, 5), 0)
        self._tvoc = all_values.get((3, 6), 0)
        
        # Filter
        self._filter_life = all_values.get((4, 1), 100)
        self._filter_days = all_values.get((4, 2), 365)
        self._filter_used = all_values.get((4, 3), 0)
        
        # Hair collection box
        self._hair_box_life = all_values.get((4, 5), 100)
        self._hair_box_days = all_values.get((4, 6), 365)
        
        # Device settings
        self._timer = all_values.get((6, 8), 0)
        self._child_lock = all_values.get((6, 10), 0)  # Keep as 0/1
        self._breathing_light = all_values.get((6, 12), 0)  # Keep as 0/1
        self._buzzer = all_values.get((6, 17), 0)  # Keep as 0/1
        self._light_brightness = all_values.get((6, 6), LIGHT_OFF)
        self._temp_unit = all_values.get((6, 4), TEMP_UNIT_CELSIUS)
        self._weight_unit = all_values.get((6, 11), WEIGHT_UNIT_KG)
        
        # Self-cleaning
        self._self_cleaning_status = all_values.get((7, 1), 0)
        
        return True

    def turn_on(self) -> bool:
        """Turn on device using power action."""
        return self._api.call_action(self._did, ACTION_POWER["siid"], ACTION_POWER["aiid"], 
                                    [{"piid": 1, "value": True}], self._host)

    def turn_off(self) -> bool:
        """Turn off device using power action."""
        return self._api.call_action(self._did, ACTION_POWER["siid"], ACTION_POWER["aiid"], 
                                    [{"piid": 1, "value": False}], self._host)

    def set_mode(self, mode: int) -> bool:
        """Set operation mode."""
        return self._api.set_property(self._did, 2, 3, mode, self._host)

    def set_fan_speed(self, speed: int) -> bool:
        """Set fan speed (1-10)."""
        return self._api.set_property(self._did, 2, 4, max(1, min(10, speed)), self._host)

    def set_fan_speed_percent(self, percent: int) -> bool:
        """Set fan speed by percentage (0-100%)."""
        if percent <= 0:
            return self.turn_off()
        # Map 0-100% to 1-10
        speed = max(1, min(10, round(percent / 10)))
        return self.set_fan_speed(speed)

    def set_light_brightness(self, brightness: int) -> bool:
        """Set light brightness (0=off, 30=dim, 50=natural, 80=bright)."""
        return self._api.set_property(self._did, 6, 6, brightness, self._host)

    def set_timer(self, hours: int) -> bool:
        """Set timer (0-12 hours)."""
        return self._api.set_property(self._did, 6, 8, max(0, min(12, hours)), self._host)

    def set_child_lock(self, enabled: bool) -> bool:
        """Toggle child lock."""
        return self._api.set_property(self._did, 6, 10, 1 if enabled else 0, self._host)

    def set_breathing_light(self, enabled: bool) -> bool:
        """Toggle breathing light."""
        return self._api.set_property(self._did, 6, 12, 1 if enabled else 0, self._host)

    def set_buzzer(self, enabled: bool) -> bool:
        """Toggle buzzer."""
        return self._api.set_property(self._did, 6, 17, 1 if enabled else 0, self._host)

    def set_temp_unit(self, unit: int) -> bool:
        """Set temperature unit (0=C, 1=F)."""
        return self._api.set_property(self._did, 6, 4, unit, self._host)

    def set_weight_unit(self, unit: int) -> bool:
        """Set weight unit (0=kg, 1=lb)."""
        return self._api.set_property(self._did, 6, 11, unit, self._host)

    def start_self_cleaning(self) -> bool:
        """Start self-cleaning procedure."""
        return self._api.call_action(self._did, ACTION_START_SELF_CLEANING["siid"], 
                                    ACTION_START_SELF_CLEANING["aiid"], None, self._host)

    def confirm_self_cleaning_finished(self) -> bool:
        """Confirm self-cleaning finished (after manual hair box cleaning)."""
        return self._api.call_action(self._did, ACTION_CONFIRM_SELF_CLEANING["siid"], 
                                    ACTION_CONFIRM_SELF_CLEANING["aiid"], None, self._host)

    def reset_filter(self) -> bool:
        """Reset filter life counter."""
        return self._api.call_action(self._did, ACTION_FILTER_RESET["siid"], 
                                    ACTION_FILTER_RESET["aiid"], None, self._host)
