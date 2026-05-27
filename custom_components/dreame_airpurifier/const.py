"""Constants for Dreame Air Purifier integration."""

DOMAIN = "dreame_airpurifier"
DEFAULT_SCAN_INTERVAL = 15  # Default polling interval in seconds

CONF_COUNTRY = "country"
CONF_SCAN_INTERVAL = "scan_interval"
COUNTRY_OPTIONS = ["us", "cn", "eu", "sg", "kr"]

PLATFORMS = ["fan", "sensor", "select", "switch", "button"]
