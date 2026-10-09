from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.limiter import limiter
from app.schemas.webhook import WebhookResult
from app.services.webhook_service import (
    NETWORKS,
    parse_body,
    process_event,
    verify_signature,
)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{network}", response_model=WebhookResult)
@limiter.limit("30 per minute")
async def receive_webhook(
    network: str,
    request: Request,
    db: Session = Depends(get_db),
    x_signature: str = Header(default="", alias="X-Signature"),
):
    """Recebe callback de conversão de uma rede (HMAC obrigatório)."""
    if network not in NETWORKS:
        raise HTTPException(status_code=404, detail="Rede desconhecida")

    raw_body = await request.body()
    if not verify_signature(network, raw_body, x_signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = parse_body(raw_body)
    if payload is None:
        raise HTTPException(status_code=422, detail="Corpo JSON inválido")

    status, event = process_event(
        db, network, payload, raw_body.decode("utf-8", errors="replace")
    )
    if status == "invalid_payload":
        raise HTTPException(
            status_code=422, detail="external_id ausente"
        )

    return WebhookResult(
        status=status, event_id=event.id if event else None, network=network
    )
