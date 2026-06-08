"""
Central settings loader.

Reads your private API keys from `.env` and the editable YAML config files,
and exposes them to the rest of the app through one simple object: `settings`.

Nothing else in the app should read os.environ or open the YAML files directly —
they all go through here. That keeps configuration in one predictable place.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

# --- Paths -----------------------------------------------------------------
# PROJECT_ROOT is the "14. Real Estate" folder (two levels up from this file).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "app" / "assets"

# Load the private keys from .env into the environment (no error if missing).
load_dotenv(PROJECT_ROOT / ".env")


def _read_yaml(filename: str) -> dict:
    """Read one config/*.yaml file into a plain dictionary."""
    path = CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Missing config file: {path}\n"
            f"Make sure you're running from the project folder."
        )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class Settings:
    """One object that holds everything the app needs to be configured."""

    # API keys (empty string if not set yet — the app warns instead of crashing).
    rentcast_api_key: str = ""
    streetview_api_key: str = ""
    gemini_api_key: str = ""

    # Parsed YAML config.
    cities: dict = field(default_factory=dict)
    scoring: dict = field(default_factory=dict)
    financing: dict = field(default_factory=dict)
    cache: dict = field(default_factory=dict)

    # Which user is "active". Becomes the real account id once auth is added;
    # for now everything is attributed to the single local user.
    current_user_id: str = "local"

    # --- Convenience helpers ------------------------------------------------
    @property
    def has_rentcast(self) -> bool:
        return bool(self.rentcast_api_key)

    @property
    def has_streetview(self) -> bool:
        return bool(self.streetview_api_key)

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    def missing_required_keys(self) -> list[str]:
        """Which REQUIRED keys still need to be filled in (for the UI warning)."""
        missing = []
        if not self.has_rentcast:
            missing.append("RENTCAST_API_KEY")
        if not self.has_streetview:
            missing.append("STREETVIEW_API_KEY")
        return missing

    # --- Cache / cost config helpers (with safe defaults) -------------------
    def ttl_seconds(self, key: str, default_seconds: int) -> int:
        """Look up a TTL from cache.yaml. `key` like 'listings_hours' or
        'value_estimate_days'; we read the number and convert to seconds."""
        ttl = self.cache.get("ttl", {})
        if key.endswith("_hours") and key in ttl:
            return int(ttl[key]) * 3600
        if key.endswith("_days") and key in ttl:
            return int(ttl[key]) * 86400
        return default_seconds

    @property
    def streetview_size(self) -> str:
        return self.cache.get("images", {}).get("streetview_size", "640x360")

    @property
    def aerial_size(self) -> str:
        return self.cache.get("images", {}).get("aerial_size", "640x360")

    @property
    def aerial_zoom(self) -> int:
        return int(self.cache.get("images", {}).get("aerial_zoom", 19))

    @property
    def monthly_lookup_cap(self) -> int:
        return int(self.cache.get("limits", {}).get("monthly_lookups_per_user", 300))

    @property
    def lookup_warn_pct(self) -> int:
        return int(self.cache.get("limits", {}).get("warn_at_pct", 80))

    def cost_per_call(self, source: str) -> float:
        return float(self.cache.get("cost_estimates_usd", {}).get(source, 0.0))

    # --- State support (California-only today; built to extend) -------------
    # To add a state later: add its cities to a cities file and its own risk
    # source (e.g. src/data_sources/risk_<state>.py). The app already reads the
    # active state from config rather than hard-coding "CA".
    _STATE_NAMES = {"CA": "California", "OR": "Oregon", "WA": "Washington",
                    "NV": "Nevada", "AZ": "Arizona", "TX": "Texas"}

    @property
    def active_state(self) -> str:
        return self.cities.get("state", "CA")

    @property
    def active_state_name(self) -> str:
        return self._STATE_NAMES.get(self.active_state, self.active_state)

    def city_names(self) -> list[str]:
        return [t["name"] for t in self.cities.get("targets", [])]

    def all_zips(self) -> list[str]:
        zips: list[str] = []
        for t in self.cities.get("targets", []):
            zips.extend(t.get("zips", []) or [])
        return zips


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build the Settings object once and reuse it (cached)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings(
        rentcast_api_key=os.getenv("RENTCAST_API_KEY", "").strip(),
        streetview_api_key=os.getenv("STREETVIEW_API_KEY", "").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        cities=_read_yaml("cities.yaml"),
        scoring=_read_yaml("scoring_weights.yaml"),
        financing=_read_yaml("financing.yaml"),
        cache=_read_yaml("cache.yaml"),
    )


# A ready-to-use instance the rest of the app imports:  from config.settings import settings
settings = get_settings()
