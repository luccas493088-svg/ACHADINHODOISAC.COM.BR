# Isac Achadinhos

Plataforma de ofertas e afiliados (em construção).

## Status

Fase 0 (higiene do repositório) concluída. Nenhum código de aplicação ainda.

## Estrutura

```
projeto_ia/
├── isac_achadinhos.html      # Layout original (referência de UI)
├── oppo_a5.jpg               # Imagem de produto
├── docs/
│   └── layout_original.html  # Cópia de segurança do layout
├── .env.example              # Placeholders de configuração (sem credenciais)
├── requirements.txt          # Dependências planejadas (não instaladas)
├── .gitignore
└── venv/                     # Ambiente local (não versionado, intocado)
```

## Regras

- Credenciais somente em `.env` (gitignored). Nunca no código.
- `venv/` é ambiente local, preservado e não versionado.
- Nenhum `pip install`/`npm install` sem autorização.
