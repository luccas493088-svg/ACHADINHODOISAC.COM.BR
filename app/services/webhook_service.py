"""Processamento de webhooks de conversão (Fase 6).

Segurança: HMAC-SHA256 do corpo cru com segredo por rede
(`{REDE}_WEBHOOK_SECRET`, ex: `AMAZON_WEBHOOK_SECRET`) comparado com
`hmac.compare_digest` (tempo constante). Sem segredo configurado, tudo é
rejeitado — nunca aceitar callback sem verificar.
"""
import hashlib
import hmac
import json
import os

from sqlalchemy.orm import Session
from app.models.conversion_event import ConversionEvent
from app.models.product import Product

NETWORKS = ("amazon", "mercadolivre", "monetizze", "tiktok")


def webhook_secret(network: str) -> str:
    """Segredo da rede via ambiente (vazio = não configurada)."""
    return os.getenv(f"{network.upper()}_WEBHOOK_SECRET", "")


def verify_signature(network: str, raw_body: bytes, signature: str) -> bool:
    """Confere `sha256=<hex>` (prefixo opcional) em tempo constante."""
    secret = webhook_secret(network)
    if not secret or not signature:
        return False
    digest = signature.removeprefix("sha256=")
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, digest)


def process_event(
    db: Session, network: str, payload: dict, raw_body: str
) -> tuple[str, ConversionEvent | None]:
    """Valida, deduplica e persiste. Retorna (status, evento)."""
    external_id = payload.get("external_id")
    if not external_id or not isinstance(external_id, str):
        return ("invalid_payload", None)

    existing = (
        db.query(ConversionEvent)
        .filter(
            ConversionEvent.network == network,
            ConversionEvent.external_id == external_id,
        )
        .first()
    )
    if existing:
        return ("duplicate", existing)

    product_id = None
    campaign_id = None
    slug = payload.get("product_slug")
    if slug:
        product = (
            db.query(Product).filter(Product.slug == slug).first()
        )
        if product:
            product_id = product.id
            campaign_id = product.campaign_id

    event = ConversionEvent(
        network=network,
        external_id=external_id,
        product_id=product_id,
        campaign_id=campaign_id,
        amount=payload.get("amount"),
        currency=payload.get("currency") or "BRL",
        status=payload.get("status") or "received",
        payload=raw_body[:4000],
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return ("created", event)


def parse_body(raw_body: bytes) -> dict | None:
    """JSON do corpo cru; None se inválido."""
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None
