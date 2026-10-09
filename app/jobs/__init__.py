"""Jobs de sincronia (Fase 6) — dry-run por padrão, 100% offline."""
from app.jobs.sync import infer_network, run_sync_report

__all__ = ["infer_network", "run_sync_report"]
