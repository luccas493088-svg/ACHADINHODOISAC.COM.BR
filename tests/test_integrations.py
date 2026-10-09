"""Testes Fase 6 — contratos + dry-run (unitários puros, sem DB/app)."""
import pytest

from app.integrations import (
    available_networks,
    build_affiliate_url,
    get_network,
)
from app.integrations.base import DryRunError, live_enabled


class TestRegistry:
    def test_unknown_network_raises_value_error(self):
        with pytest.raises(ValueError, match="Rede desconhecida"):
            get_network("nope")

    def test_all_three_registered(self):
        assert get_network("amazon").name == "amazon"
        assert get_network("mercadolivre").name == "mercadolivre"
        assert get_network("monetizze").name == "monetizze"


class TestAmazon:
    def test_build_url_with_tag(self, monkeypatch):
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "isac-20")
        url = build_affiliate_url("amazon", "B0EXAMPLE")
        assert url == "https://www.amazon.com.br/dp/B0EXAMPLE/?tag=isac-20"

    def test_unconfigured_without_tag(self, monkeypatch):
        monkeypatch.delenv("AMAZON_PARTNER_TAG", raising=False)
        assert get_network("amazon").is_configured() is False
        assert "tag" not in build_affiliate_url("amazon", "B0X")

    def test_available_lists_configured(self, monkeypatch):
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "isac-20")
        monkeypatch.delenv("MERCADOLIVRE_APP_ID", raising=False)
        monkeypatch.delenv("MONETIZZE_API_KEY", raising=False)
        assert available_networks() == ["amazon"]


class TestMercadoLivre:
    def test_full_url_passthrough(self):
        url = "https://www.mercadolivre.com.br/itm/MLB123"
        assert build_affiliate_url("mercadolivre", url) == url

    def test_id_builds_item_url(self):
        assert (
            build_affiliate_url("mercadolivre", "MLB123")
            == "https://www.mercadolivre.com.br/itm/MLB123"
        )


class TestMonetizze:
    def test_src_appended(self):
        base = "https://app.monetizze.com.br/r/ABC_123"
        url = build_affiliate_url("monetizze", base, src="isac-site")
        assert url == f"{base}?src=isac-site"

    def test_no_src_returns_base(self):
        base = "https://app.monetizze.com.br/r/ABC_123"
        assert build_affiliate_url("monetizze", base) == base


class TestDryRun:
    def test_live_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("AFFILIATE_LIVE", raising=False)
        assert live_enabled() is False

    def test_fetch_blocked_in_dry_run(self, monkeypatch):
        monkeypatch.delenv("AFFILIATE_LIVE", raising=False)
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "isac-20")
        with pytest.raises(DryRunError):
            get_network("amazon").fetch_offer("B0X")

    def test_fetch_blocked_without_credentials(self, monkeypatch):
        monkeypatch.setenv("AFFILIATE_LIVE", "1")
        monkeypatch.delenv("AMAZON_PARTNER_TAG", raising=False)
        with pytest.raises(DryRunError):
            get_network("amazon").fetch_offer("B0X")

    def test_live_never_touches_network(self, monkeypatch):
        # Mesmo liberado, ainda não há I/O: contrato, não integração real
        monkeypatch.setenv("AFFILIATE_LIVE", "1")
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "isac-20")
        with pytest.raises(NotImplementedError):
            get_network("amazon").fetch_offer("B0X")
