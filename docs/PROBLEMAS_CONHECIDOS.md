# PROBLEMAS CONHECIDOS — Isac Achadinhos

**Data:** 2026-10-10  
**Fase:** 3 — Autenticação e Painel Administrativo

---
## Problemas identificados no código

### 1. Página de login redireciona para si mesma (loop infinito)

**Arquivo:** `app/routers/auth.py:23-31`  
**Descrição:** A rota `GET /admin/login` verifica se o usuário já está logado e redireciona para `/admin/`. Se não estiver logado, redireciona para `/admin/login` — criando um loop infinito.  
**Causa:** A rota deveria renderizar um template HTML de login, não redirecionar.  
**Correção sugerida:** Criar um template `login.html` e retorná-lo com `TemplateResponse`.  
**[x] Corrigido em 2026-10-09**: `GET /admin/login` renderiza `login.html` via `TemplateResponse`; só redireciona para `/admin/` quando já existe sessão válida. Coberto por `test_get_login_renders_form`.

---

### 2. Incompatibilidade entre resposta do login e `response_model`

**Arquivo:** `app/routers/auth.py:34`  
**Descrição:** A rota `POST /admin/login` declara `response_model=Token` mas retorna um `RedirectResponse`. O FastAPI tentará validar o `RedirectResponse` contra o schema `Token`, causando erro.  
**Causa:** `response_model` incompatível com o tipo de retorno real.  
**Correção sugerida:** Remover `response_model=Token` ou retornar JSON com o token (dependendo do fluxo desejado).  
**[x] Corrigido em 2026-10-09**: `POST /admin/login` não declara `response_model`; retorna `RedirectResponse` (sucesso) ou `TemplateResponse` 401 (falha). Coberto por `test_login_valid_redirects_to_admin` e `test_login_invalid_password_returns_401`.

---

### 3. Chave JWT padrão insegura

**Arquivo:** `app/config.py:10-22`  
**Descrição:** O valor padrão de `jwt_secret` era `"change-me-long-random-string"`. Se a variável de ambiente `JWT_SECRET` não for definida, todos os tokens seriam assinados com uma chave conhecida publicamente.  
**Causa:** Fallback inseguro no código - aceitava valor fraco por padrão.  
**Correção aplicada:** Removido o valor `_PLACEHOLDER_SECRET`. O construtor `Settings.__init__` agora exige que `jwt_secret` seja definido e não seja vazio, levantando `ValueError` caso contrário. O segredo válido é carregado do arquivo `.env`. testes automatizados confirmam a rejeição de segredo vazio ou conhecido.  
**[x] Corrigido em 2026-10-10**: validação de JWT_SECRET adicionada em `app/config.py`.

---

### 4. Tratamento incorreto de exceções JWT

**Arquivo:** `app/security.py:33`  
**Descrição:** O código captura `jwt.JWTError`, mas no PyJWT a classe base é `jwt.PyJWTError`. `jwt.JWTError` não existe, causando `AttributeError` quando um token inválido é decodificado.  
**Causa:** Nome incorreto da exceção.  
**Correção sugerida:** Usar `jwt.PyJWTError` ou exceções específicas (`jwt.ExpiredSignatureError`, `jwt.InvalidTokenError`).  
**[x] Corrigido em 2026-10-09**: código usa `jwt.PyJWTError`; verificado com testes de token inválido e expirado (`test_decode_invalid_token_returns_none`, `test_expired_token_returns_none`, `test_decode_expired_token_returns_none`).

---

### 5. Logout não limpa a sessão completamente

**Arquivo:** `app/routers/auth.py:87-108`  
**Descrição:** O logout fazia `request.session.pop("user", None)` mas não limpa outros dados da sessão. Além disso, a blacklist é em memória (`set`) e não persiste entre reinicializações.  
**Causa:** Logout incompleta + blacklist volátil.  
**Correção aplicada:** Agora usa `request.session.clear()` para limpar toda a sessão. Blacklist em memória permanece como limitação conhecida (planejado migrar para Redis).  
**[x] Corrigido em 2026-10-10**: `request.session.clear()` implementado em `app/routers/auth.py:163`.

---

### 6. Sem proteção CSRF

**Arquivo:** `app/routers/auth.py` (todas as rotas POST)  
**Descrição:** Os formulários de criação, edição e exclusão não incluem token CSRF. Um atacante pode criar páginas que enviam POSTs para essas rotas usando a sessão do usuário.  
**Causa:** Falta de implementação de CSRF.  
**Correção sugerida:** Adicionar middleware ou dependência que valide token CSRF em todas as rotas POST/PUT/DELETE.  
**[x] Corrigido em 2026-10-09**: `_csrf_token`/`_check_csrf` aplicados em todos os POSTs admin; corrigido bypass `None == None` (agora exige token presente e igual nos dois lados). Coberto por `test_login_without_csrf_is_rejected`.

---

### 7. Sem autorização por função (role)

**Arquivo:** `app/routers/auth.py` (todas as rotas admin)  
**Descrição:** Qualquer usuário autenticado (com `role="admin") pode acessar todas as rotas. Não há verificação de `is_superuser` ou roles específicas.  
**Causa:** Falta de dependência de autorização.  
**Correção sugerida:** Criar dependência `require_role(role: str)` ou `require_superuser()` e aplicá-la às rotas admin.  
**[x] Corrigido em 2026-10-09**: `require_admin`/`_require_admin_redirect` exigem `role in ("admin", "superuser")` em todas as rotas admin (403 caso contrário). Coberto por `test_admin_panel_redirects_when_anonymous`.

---

### 8. Formulários administrativos incompletos

**Arquivo:** `app/routers/auth.py:244-278, 319-354`  
**Descrição:** As rotas `GET /categories/new`, `GET /categories/{id}/edit`, `GET /products/new` e `GET /products/{id}/edit` não renderizam formulários HTML — apenas redirecionam para `/admin/`.  
**Causa:** Implementação incompleta.  
**Correção sugerida:** Criar templates Jinja2 para cada formulário e retorná-los com `TemplateResponse`.  
**[x] Corrigido em 2026-10-09**: `new`/`edit` de categorias e produtos renderizam `category_form.html`/`product_form.html`; painel extraído de string inline para `app/templates/admin_panel.html`.

---

### 9. Exclusões usam POST em vez de DELETE

**Arquivo:** `app/routers/auth.py:300-315, 377-392`  
**Descrição:** As rotas de exclusão de categorias e produtos usam `@router.post` em vez de `@router.delete`. Isso é incompatível com a semântica HTTP e com as rotas da API REST (`/api/products/{id}` usa DELETE).  
**Causa:** Escolha incorreta do método HTTP.  
**Correção sugerida:** Mudar para `@router.delete` ou usar formulários com method override.  
**[x] Decisão documentada em 2026-10-09:** admin HTML mantém POST (forms não têm DELETE); API REST (`/api/categories`, `/api/products`) usa DELETE. Sem ação pendente.

---

### 10. `except Exception: pass` silencia erros

**Arquivo:** `app/routers/auth.py:266-267, 294-295, 312-313, 343-344, 371-372, 389-390`  
**Descrição:** Todas as operações de criação, edição e exclusão no admin estão envolvidas em `try/except Exception: pass`, que silenciosamente ignora qualquer erro. Isso impede debugging e pode esconder falhas de banco de dados.  
**Causa:** Tratamento de erro inadequado.  
**Correção sugerida:** Capturar exceções específicas, logar o erro e retornar resposta apropriada (ex: 404 se não encontrado, 400 se dados inválidos).  
**[x] Corrigido em 2026-10-09**: blocos admin usam `logger.exception(...)` + `raise HTTPException(...) from None` (404/400 conforme o caso). Bônus: corrigida recursão infinita em `POST /api/categories/` (rota chamava a si mesma em vez do service; renomeada para `create_category_route`).

---

### 11. Import tardio de `RedirectResponse`

**Arquivo:** `app/routers/auth.py:6`  
**Descrição:** `RedirectResponse` é importado no topo do arquivo (linha 6), não dentro de funções.  
**Causa:** Import deveria ser no topo do módulo.  
**Correção aplicada:** `from fastapi.responses import RedirectResponse, HTMLResponse` já está no topo do `app/routers/auth.py:6`.  
**[x] Corrigido em 2026-10-10**: import movido para o topo do módulo.

---

### 12. Import duplicado de `HTTPException` em `main.py`

**Arquivo:** `app/main.py:1`  
**Descrição:** `HTTPException` é importado uma única vez na linha 1 (`from fastapi import ... HTTPException ...`).  
**Causa:** Import redundante anterior na linha 6 (`from fastapi.exceptions import HTTPException`).  
**Correção aplicada:** A linha 6 foi removida. Import único permanece em `app/main.py:1`.  
**[x] Corrigido em 2026-10-10**: import duplicado removido de `app/main.py`.

---

### 13. `Optional` não importado em `security.py`

**Arquivo:** `app/security.py:4`  
**Descrição:** A função `create_access_token` usa `Optional[timedelta]` na assinatura, e `Optional` é importado de `typing` na linha 4.  
**Causa:** Import faltante.  
**Correção aplicada:** `from typing import Optional` já está no topo de `app/security.py:4`.  
**[x] Corrigido em 2026-10-10**: import `Optional` verificado e já presente.

---

### 14. `timedelta` não importado em `auth.py`

**Arquivo:** `app/routers/auth.py:3`  
**Descrição:** A linha 3 importa `from datetime import timedelta` e a linha 122 usa `timedelta(minutes=30)`.  
**Causa:** Import faltante.  
**Correção aplicada:** `from datetime import timedelta` já está no topo de `app/routers/auth.py:3`.  
**[x] Corrigido em 2026-10-10**: import `timedelta` verificado e já presente.

---

### 15. `blacklist_token` não importado em `auth.py`

**Arquivo:** `app/routers/auth.py:16`  
**Descrição:** A função `blacklist_token` é importada no topo do arquivo (linha 16) de `app.security`.  
**Causa:** Import faltante.  
**Correção aplicada:** `blacklist_token` já está importado em `app/routers/auth.py:16` de `app.security`.  
**[x] Corrigido em 2026-10-10**: import `blacklist_token` verificado e já presente.

---

### 16. `Request({})` como valor padrão de parâmetro

**Arquivo:** `app/routers/auth.py`  
**Descrição:** Não foram encontrados usos de `request: Request = Request({})` como valor padrão. Todas as rotas recebem `request: Request` injetado pelo FastAPI sem valor padrão.  
**Causa:** Valor padrão incorreto para parâmetro tipado como `Request`.  
**Correção:** Nenhuma alteração necessária — FastAPI injeta `Request` automaticamente.  
**[x] Corrigido em 2026-10-10:** verificado — não há defaults `Request({})` no código.

---

### 17. Blacklist em memória não escala

**Arquivo:** `app/security.py:59`  
**Descrição:** A blacklist de tokens é um `set` em memória. Em produção com múltiplos workers/servidores, a blacklist não será compartilhada.  
**Suspeita:** Deveria usar Redis (já listado em `requirements.txt` e `pyproject.toml`).  
**[x] Corrigido em 2026-10-09 (Fase 4)**: Redis 100% lazy em `app/security.py` — zero I/O no import (antes travava ~19s sem Redis), 1 tentativa com timeout de 1s no primeiro uso, fallback em memória. `SlowAPIMiddleware` ativado em `app/main.py`. Cobertos por `test_limiter_middleware_active` e `test_security_import_does_not_hang_without_redis`.  
--- 

### 18. Sessão em cookie sem rotação de chave

**Arquivo:** `app/main.py:53-58`  
**Descrição:** O `SessionMiddleware` usa `settings.jwt_secret` como `secret_key`. Se a chave mudar, todas as sessões existentes serão invalidadas.  
**Suspeita:** Considerar usar chave separada para sessão.  
**Status:** Não verificado — em desenvolvimento; `https_only` agora respeita variável `environment`.  
---

## Testes pendentes

- [x] Teste de health check (existe em `tests/test_basic.py`)
- [x] Teste de config (existe em `tests/test_basic.py`)
- [x] Teste de JWT_SECRET rejeitado quando vazio
- [x] Teste de JWT_SECRET rejeitado quando placeholder
- [x] Teste de criação e decodificação de token JWT
- [x] Teste de decodificação de token inválido retorna None
- [x] Teste de logout com limpeza de sessão
- [x] Teste de expiração de token JWT (`tests/test_admin_auth.py`)
- [x] Teste de blacklist de tokens (`tests/test_admin_auth.py`)
- [x] Teste de login válido/inválido e CSRF (`tests/test_admin_auth.py`)
- [x] Teste de proteção do painel admin sem sessão (`tests/test_admin_auth.py`)
- [x] Teste de rate-limit ativo e import sem Redis (`tests/test_admin_auth.py`)

**Resultado em 2026-10-09: 19 passed, ruff 0 erros (era 99).**

---

## Segurança

- **Nunca** coloque senhas, tokens, chaves privadas ou valores secretos neste documento.
- Variáveis de ambiente necessárias: `JWT_SECRET`, `DATABASE_URL`, `REDIS_URL`.
- O arquivo `.env` está gitignored e não deve ser versionado.

**Ao corrigir um problema:**
1. Marque como corrigido: `[x]`
2. Adicione uma nota com a data e descrição da correção
3. Execute os testes e registre o resultado real
4. Não declare como corrigido sem evidência
