#!/usr/bin/env bash
# Fase 7 — backup do Postgres via pg_dump (usa DATABASE_URL do .env).
# Uso: ./scripts/backup_db.sh [destino]
# Requer: pg_dump instalado e DATABASE_URL exportada ou em .env
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERRO: DATABASE_URL não definida (nem .env nem ambiente)" >&2
  exit 1
fi

DESTINO="${1:-backups/isac_achadinhos_$(date +%Y%m%d_%H%M%S).sql}"
mkdir -p "$(dirname "$DESTINO")"

pg_dump "$DATABASE_URL" > "$DESTINO"
echo "Backup salvo em $DESTINO"
