# Bootstrap (Deploy / Docker)

Diretório dos scripts de inicialização, ao lado do `manage.py`.

## Scripts

- `bootstrap/01_migrate.sh` -> aplica migrations
- `bootstrap/02_seed_initial_access.sh` -> cria grupos e usuários
- `bootstrap/99_bootstrap_all.sh` -> migração + acesso + seeds opcionais

## Variáveis de ambiente

- `DATABASE_URL` obrigatório no deploy com PostgreSQL
- `SECRET_KEY` obrigatório no ambiente local/produção
- `DEFAULT_PASSWORD` obrigatório para seed inicial
- `RESET_PASSWORDS` (`0` ou `1`)
- `RUN_ESTOQUE_SEEDS` (`0` ou `1`)

## Execução manual

```sh
cp .env.example .env
sh ./bootstrap/99_bootstrap_all.sh
```

## Observações de segurança

- Não versionar `.env`
- Não armazenar senhas reais em `docker-compose.yml`
- Preferir variáveis de ambiente e exemplos sem segredos
