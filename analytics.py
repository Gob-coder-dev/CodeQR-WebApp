from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

VALID_EVENTS = {"server_visit", "qr_generated"}
TRUTHY_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AnalyticsConfig:
    endpoint: str
    api_key: str


def is_analytics_enabled() -> bool:
    return os.environ.get("ANALYTICS_ENABLED", "").strip().lower() in TRUTHY_VALUES


def get_analytics_config() -> AnalyticsConfig | None:
    if not is_analytics_enabled():
        return None

    supabase_url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    api_key = (
        os.environ.get("SUPABASE_SECRET_KEY", "").strip()
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    if not supabase_url or not api_key:
        return None

    return AnalyticsConfig(
        endpoint=f"{supabase_url}/rest/v1/analytics_events",
        api_key=api_key,
    )


def build_headers(api_key: str) -> dict[str, str]:
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
        "User-Agent": "qr-code-converter-server",
    }

    if not api_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {api_key}"

    return headers


def send_analytics_event(config: AnalyticsConfig, event_name: str) -> None:
    payload = json.dumps({"event_name": event_name}).encode("utf-8")
    request = urlrequest.Request(
        config.endpoint,
        data=payload,
        headers=build_headers(config.api_key),
        method="POST",
    )

    try:
        with urlrequest.urlopen(request, timeout=2):
            pass
    except (HTTPError, URLError, TimeoutError, OSError):
        pass


def track_event(event_name: str) -> None:
    if event_name not in VALID_EVENTS:
        return

    config = get_analytics_config()
    if config is None:
        return

    thread = threading.Thread(
        target=send_analytics_event,
        args=(config, event_name),
        daemon=True,
    )
    thread.start()
