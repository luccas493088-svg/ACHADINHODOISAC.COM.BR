# PRÓXIMA SESSÃO — Instruções para Retomada

**Projeto:** Isac Achadinhos  
**Data:** 2026-10-09  
**Fase atual:** Fase 3 (Autenticação e Painel Administrativo) — implementada com problemas pendentes

---

## Contexto

O projeto está em pausa. Nenhum commit foi feito. O código da Fase 3 existe mas possui problemas de segurança e funcionamento que precisam ser corrigidos antes de avançar para a Fase 4.

---

## Instruções para a próxima IA

### 1. Leia os documentos de status

- `docs/STATUS_PROJETO.md` — visão geral do projeto
- `docs/PROBLEMAS_CONHECIDOS.md` — lista detalhada de problemas a corrigir

### 2. Verifique o ambiente

```bash
# Verifique se .venv/ existe e está funcional
ls .venv/

# Se precisar instalar dependências (use .venv/, NÃO venv/)
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Revise o código da Fase 3

Arquivos principais a revisar:
- `app/routers/auth.py` — rotas de login, logout, painel admin, CRUD admin
- `app/security.py` — JWT, Argon2, blacklist
- `app/main.py` — middlewares, imports
- `app/schemas/user.py` — schemas de usuário e token

### 4. Corrija os problemas conhecidos

Siga a lista em `docs/PROBLEMAS_CONHECIDOS.md`. Cada problema tem:
- Descrição
- Causa provável
- Sugestão de correção

**IMPORTANTE:** Não declare um problema como corrigido sem evidência (teste ou verificação no código).

### 5. Execute os testes disponíveis

```bash
# Com .venv/
.venv/bin/pytest tests/ -v

# Ou com pytest global
pytest tests/ -v
```

Se os testes falharem, documente o erro real em `docs/PROBLEMAS_CONHECIDOS.md`.

### 6. Escreva testes para a Fase 3

Após corrigir os problemas, crie testes para:
- Login com credenciais válidas e inválidas
- Logout e invalidação de sessão
- Proteção de rotas admin (redirecionamento quando não autenticado)
- Expiração de token JWT
- Blacklist de tokens

### 7. Não faça

- Não inicie a Fase 4
- Não faça refatorações amplas
- Não altere `isac_achadinhos.html` ou `docs/layout_original.html`
- Não altere a pasta `venv/`
- Não faça commit sem autorização
- Não inicie Docker, PostgreSQL ou Redis
- Não instale pacotes sem necessidade

---

## Resumo do estado atual

| Item | Status |
|------|--------|
| Fase 0 | ✅ Concluída |
| Fase 1 | ✅ Implementada (testes mínimos) |
| Fase 3 | ⚠️ Implementada com problemas |
| Fase 4 | ❌ Não iniciada |
| Commits | 0 |
| Testes passando | Desconhecido (não executados nesta sessão) |

---

## Variáveis de ambiente necessárias

- `DATABASE_URL` — string de conexão PostgreSQL
- `JWT_SECRET` — chave secreta para assinar JWTs
- `REDIS_URL` — string de conexão Redis (para rate limiting/cache)
- `environment` — "development" ou "production"

**Nunca coloque valores reais nos documentos. Use `.env` local (gitignored).**
