# STATUS DO PROJETO — Isac Achadinhos

**Data da última atualização:** 2026-10-09  
**Branch:** master  
**Testes:** 93 passed (+ `test_cli_admin.py`, chave de ouro)  
**Ruff:** 0 erros

---

## Objetivo

Plataforma de ofertas e afiliados com painel administrativo, construída com FastAPI, SQLAlchemy, Alembic, Jinja2 e Python.

---

## Arquitetura

```
projeto_ia/
├── app/
│   ├── main.py              # App FastAPI, middlewares, rotas base
│   ├── config.py            # Settings (Pydantic Settings)
│   ├── database.py          # Engine SQLAlchemy + SessionLocal
│   ├── security.py          # JWT, Argon2, blacklist de tokens
│   ├── db/base.py           # Base declarativa
│   ├── models/              # User, Category, Product
│   ├── schemas/             # Pydantic: User, Category, Product
│   ├── routers/             # auth, products, categories
│   ├── services/            # Lógica de negócio (category, product)
│   └── templates/           # Jinja2 (home.html)
├── alembic/                 # Migrações (initial + users_init)
├── tests/                   # test_basic.py
├── docs/                    # Documentação do projeto
├── isac_achadinhos.html     # Layout original (referência)
├── docs/layout_original.html # Cópia de segurança do layout
├── requirements.txt         # Dependências de produção
├── requirements-dev.txt     # Dependências de desenvolvimento
├── pyproject.toml           # Config Poetry + ruff + mypy
├── .env.example             # Placeholders (sem credenciais)
└── .gitignore
```

**Stack:** FastAPI + Uvicorn, SQLAlchemy 2.0, Alembic, Pydantic v2, Jinja2, Argon2 (argon2-cffi), PyJWT, PostgreSQL (psycopg), Redis (planejado).

---

## Fases

### Fase 0 — Higiene do repositório ✅ CONCLUÍDA

- `.env.example` criado (sem credenciais reais)
- `.gitignore` configurado (venv/, .env, __pycache__, caches)
- `requirements.txt` e `requirements-dev.txt` definidos
- `pyproject.toml` com configurações de ruff e mypy
- Layout original preservado em `isac_achadinhos.html` e `docs/layout_original.html`

### Fase 1 — API base + models + migrations ✅ IMPLEMENTADA (testes mínimos)

**Implementado:**
- Models SQLAlchemy: `User`, `Category`, `Product`
- Schemas Pydantic: `UserCreate`, `UserLogin`, `UserResponse`, `Token`, `CategoryCreate`, `CategoryUpdate`, `CategoryResponse`, `ProductCreate`, `ProductUpdate`, `ProductResponse`
- Migrações Alembic: `initial` (categories + products), `users_init` (users)
- Rotas API REST:
  - `GET /api/products/` — listagem com paginação e filtros
  - `GET /api/products/{id}` — detalhe
  - `POST /api/products/` — criação
  - `PUT /api/products/{id}` — atualização
  - `DELETE /api/products/{id}` — soft delete
  - `GET /api/categories/` — listagem
  - `GET /api/categories/{id}` — detalhe
  - `POST /api/categories/` — criação
  - `PUT /api/categories/{id}` — atualização
  - `DELETE /api/categories/{id}` — soft delete
- Services: `category_service.py`, `product_service.py`
- Health check: `GET /health`
- Página home com Jinja2: `GET /`
- Middlewares: CORS, Session, security headers, request ID
- Testes: `tests/test_basic.py` (2 testes: health + config)

**NÃO testado:**
- Testes de integração das rotas de products/categories
- Testes de autenticação
- Testes de admin panel
- Execução real das migrações em banco PostgreSQL

### Fase 2 — (não documentada separadamente; absorvida pela Fase 1)

Não há documentação de uma Fase 2 distinta. O código atual sugere que a Fase 2 foi mesclada à Fase 1 ou não foi formalizada.

### Fase 3 — Autenticação e Painel Administrativo ✅ CONCLUÍDA (2026-10-09)

Todos os 16 problemas conhecidos corrigidos e cobertos por testes em `tests/test_admin_auth.py` (ver `docs/PROBLEMAS_CONHECIDOS.md`).

### Fase 4 — Rate limiting e Redis ✅ CONCLUÍDA (2026-10-09)

- `SlowAPIMiddleware` ativado em `app/main.py` (limites: 200/dia, 50/min)
- Blacklist JWT com Redis lazy (timeout 1s, 1 tentativa) + fallback em memória
- B008 silenciado no ruff (idioma FastAPI); `class Config` migrado para `ConfigDict`

### Fase 5 — Métricas e Campanhas ✅ CONCLUÍDA (2026-10-09)

- Models `Campaign` + `ClickEvent` (`product.campaign_id`); migration `fase5_campaigns_metrics`
- Redirect rastreado `GET /r/{slug}` → 302 ao `affiliate_url` (fundação do rastreamento; IP só como hash SHA-256, rate-limit 60/min)
- APIs `/api/campaigns` (CRUD) e `/api/metrics/summary` (totais, top produtos, por campanha, por dia)
- Admin: CRUD de campanhas, dashboard `/admin/metrics`, seção Campanhas no painel
- 10 testes em `tests/test_fase5.py` (SQLite em memória + fixture `autouse`)

### Removido do projeto

- Pasta `bellemiststore/` (afiliação Belle Mist) excluída a pedido; zero referências restantes

### Fase 6 — Integrações e automações 🟡 INICIADA (contratos + dry-run)

- `app/integrations/`: contrato `AffiliateNetwork`, builders Amazon/ML/Monetizze, registry; 100% aditivo (nenhum arquivo existente alterado)
- Dry-run por padrão: externas só com `AFFILIATE_LIVE=1` + credenciais; sem I/O implementado ainda
- 13 testes isolados em `tests/test_integrations.py` (sem DB, ~3s)
- Webhooks `POST /api/webhooks/{rede}`: HMAC-SHA256 (`{REDE}_WEBHOOK_SECRET`, `compare_digest`), idempotência `(network, external_id)`, model `ConversionEvent` + migration `fase6_webhook_events`; 9 testes em `tests/test_webhooks.py`

### Fase 7 — Preparação para produção 🟡 INICIADA (2026-10-09)

- `GET /ready` (200 com banco, 503 sem) para orquestradores; `GET /health` mantido
- `requirements.txt` alinhado ao pyproject (faltavam `jinja2`, `redis`, `psycopg` — imagem quebraria sem eles)
- `.dockerignore` (nunca leva `.env`/venvs/git), `HEALTHCHECK` no Dockerfile e no compose
- `scripts/backup_db.sh` (pg_dump via `DATABASE_URL`, sem segredo no repo)
- Removido `app/routers/auth.py.bak`; 6 testes em `tests/test_prod_ready.py`

### Fase 8 — Vitrine com cadastro automático futuro ✅ CONCLUÍDA (2026-10-09)

- Catálogo começa vazio: nada cadastrado; página mostra "Em breve novas ofertas"
- Model `StoreProduct` (loja, nome, preco, imagem, link_afiliado, data_cadastro, ativo) + migration `fase8_store_products`
- Importador com 1 conector por loja (fetch + save com dedupe pelo link); todos dry-run com fictícios; credenciais só via `.env`
- Job manual `POST /api/jobs/import` (admin, agendador Fase 6 segue desligado por padrão)
- APIs `/api/vitrine/produtos` (loja/ordem/limite) e `/api/vitrine/destaque`; frontend lê do banco com fallback JSON
- Meta segue só divulgação (sociais em branco, pixel desligado, sem tokens)
- 14 testes em `tests/test_fase8.py`; Fases 1–7 intactas

### Chave de ouro (2026-10-09) — amarração final

- `.env.example` documenta todas as variáveis novas (webhooks, scheduler, conectores), vazias
- `scripts/criar_admin.py`: cria o primeiro admin (senha via prompt, nunca em arquivo); 4 testes em `tests/test_cli_admin.py`

**Implementado:**
- Router `/admin` com login, logout, painel (`admin_panel.html`), CRUD de categorias e produtos
- Hash de senha com Argon2; JWT (PyJWT) com expiração; sessão via cookie
- Blacklist de tokens (Redis lazy + fallback em memória)
- CSRF em todos os POSTs admin; `require_admin` (roles admin/superuser)

**Testado (29 testes verdes):**
- Fluxo completo de login/logout, expiração e blacklist de JWT
- Proteção de rotas admin, CSRF, autorização por role
- CRUD de campanhas, redirect rastreado e agregações de métricas

---

## Pendências (fora do escopo Fase 3/4 — infra local)

- [ ] Executar migrações em banco real (PostgreSQL)
- [ ] Subir Redis local para blacklist compartilhada (fallback em memória ativo)
- [ ] Commit inicial (aguardando autorização)

---

## Estado do Git

- **Branch:** master
- **Commits:** 0
- **Staged (novos):** `.env.example`, `.gitignore`, `README.md`, `docs/layout_original.html`, `isac_achadinhos.html`, `oppo_a5.jpg`, `requirements.txt`
- **Untracked:** `Dockerfile`, `alembic.ini`, `alembic/`, `app/`, `docker-compose.yml`, `pyproject.toml`, `requirements-dev.txt`, `tests/`
- **Modificados:** nenhum
---

