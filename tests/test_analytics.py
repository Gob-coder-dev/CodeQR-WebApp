from analytics import (
    AnalyticsConfig,
    build_headers,
    get_analytics_config,
    is_analytics_enabled,
)


def test_analytics_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ANALYTICS_ENABLED", raising=False)

    assert is_analytics_enabled() is False
    assert get_analytics_config() is None


def test_analytics_config_uses_secret_key(monkeypatch):
    monkeypatch.setenv("ANALYTICS_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co/")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_demo")

    assert get_analytics_config() == AnalyticsConfig(
        endpoint="https://example.supabase.co/rest/v1/analytics_events",
        api_key="sb_secret_demo",
    )


def test_secret_key_headers_do_not_use_authorization_header():
    headers = build_headers("sb_secret_demo")

    assert headers["apikey"] == "sb_secret_demo"
    assert "Authorization" not in headers


def test_legacy_service_role_headers_use_authorization_header():
    headers = build_headers("legacy-service-role-key")

    assert headers["apikey"] == "legacy-service-role-key"
    assert headers["Authorization"] == "Bearer legacy-service-role-key"
