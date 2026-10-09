"""Agendador — DESLIGADO por padrão (Fase 6).

Sem dependência nova: o APScheduler é importado de forma lazy e só quando
`start_scheduler()` é chamado. Produção liga via `ENABLE_SCHEDULER=1`.
Sem a lib instalada, erro claro em vez de import quebrado.
"""
import logging
import os

logger = logging.getLogger("isac_achadinhos")

_scheduler = None


def enabled() -> bool:
    """Flag explícita que liga o agendador. Padrão: desligado."""
    return os.getenv("ENABLE_SCHEDULER", "0") == "1"


def interval_minutes() -> int:
    """Intervalo do job de sync (padrão: 60 min)."""
    try:
        return max(5, int(os.getenv("SYNC_INTERVAL_MINUTES", "60")))
    except ValueError:
        return 60


def start_scheduler():
    """Inicia o agendador (exige APScheduler instalado + flag ligada)."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    if not enabled():
        raise RuntimeError(
            "Agendador desligado: defina ENABLE_SCHEDULER=1 para ligar"
        )
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        raise RuntimeError(
            "APScheduler não instalado: adicione 'apscheduler' às "
            "dependências para ligar o agendador"
        ) from None

    from app.database import SessionLocal
    from app.jobs.import_products import run_import
    from app.jobs.sync import run_sync_report

    def _sync_job():
        db = SessionLocal()
        try:
            report = run_sync_report(db)
            logger.info("Sync report: %s", report)
        except Exception:
            logger.exception("Falha no job de sincronia")
        finally:
            db.close()

    def _import_job():
        db = SessionLocal()
        try:
            report = run_import(db)
            logger.info("Import report: %s", report)
        except Exception:
            logger.exception("Falha no job de importação")
        finally:
            db.close()

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _sync_job, "interval", minutes=interval_minutes(), id="sync_report"
    )
    _scheduler.add_job(
        _import_job, "interval", minutes=interval_minutes(), id="import_products"
    )
    _scheduler.start()
    return _scheduler


def stop_scheduler() -> None:
    """Para o agendador se estiver rodando."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
