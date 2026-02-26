# Load config from config.config means /config/config.py
from config.config import DB_CONFIG as BASE_DB_CONFIG

try:
    # Load config from config.config_local means /config/config.py
    from config.config_local import DB_CONFIG as LOCAL_DB_CONFIG
except ImportError:
    LOCAL_DB_CONFIG = {}

# Merge base + local (local overrides base)
DB_CONFIG = {**BASE_DB_CONFIG, **LOCAL_DB_CONFIG}