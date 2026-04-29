"""Unit tests for _get_client_ip in ip_blocker middleware."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.middleware.ip_blocker import _get_client_ip


def _mk_request(client_host=None, headers=None):
    req = MagicMock()
    req.client = MagicMock(host=client_host) if client_host else None
    req.headers = headers or {}
    return req


def test_no_client_returns_unresolved_and_not_real():
    ip, is_real = _get_client_ip(_mk_request())
    assert ip.startswith("unresolved:")
    assert is_real is False


def test_direct_client_when_proxy_disabled():
    ip, is_real = _get_client_ip(_mk_request(client_host="1.2.3.4"))
    assert ip == "1.2.3.4"
    assert is_real is True


def test_trust_proxy_uses_forwarded_header():
    """When trust_proxy=True the left-most X-Forwarded-For value is returned."""
    from app.config import get_settings

    settings = get_settings()
    original_trust = settings.trust_proxy
    settings.__dict__["trust_proxy"] = True
    try:
        req = _mk_request(
            client_host="10.0.0.1",
            headers={"x-forwarded-for": "203.0.113.5, 10.0.0.1"},
        )
        ip, is_real = _get_client_ip(req)
        assert ip == "203.0.113.5"
        assert is_real is True
    finally:
        settings.__dict__["trust_proxy"] = original_trust


def test_trust_proxy_rejects_spoofed_header_when_trusted_ips_set():
    """When trusted_proxy_ips is set and client is not in it, fall back to direct IP."""
    from app.config import get_settings

    settings = get_settings()
    original_trust = settings.trust_proxy
    original_trusted = settings.trusted_proxy_ips
    settings.__dict__["trust_proxy"] = True
    settings.__dict__["trusted_proxy_ips"] = "10.0.0.1"
    try:
        # Client is NOT a known proxy — its X-Forwarded-For should be ignored.
        req = _mk_request(
            client_host="203.0.113.99",
            headers={"x-forwarded-for": "1.2.3.4"},
        )
        ip, is_real = _get_client_ip(req)
        assert ip == "203.0.113.99"
        assert is_real is True
    finally:
        settings.__dict__["trust_proxy"] = original_trust
        settings.__dict__["trusted_proxy_ips"] = original_trusted


def test_unresolved_ips_are_unique():
    """Two requests with no client info must not share the same placeholder."""
    ip1, _ = _get_client_ip(_mk_request())
    ip2, _ = _get_client_ip(_mk_request())
    assert ip1 != ip2
