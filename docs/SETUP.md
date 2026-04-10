# Setup e Funcionamento - Tarugo

## Visão geral

O Tarugo é uma aplicação modular em Django. A fase atual assume PostgreSQL como banco principal, com configuração via `.env`.

## Fluxo de camadas

- models -> estrutura de dados
- services -> regra de negócio
- selectors -> consultas
- api -> interface HTTP
- schemas -> validação com Pydantic

## Setup local seguro

1. Copie `.env.example` para `.env`.
2. Preencha `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL` e demais variáveis.
3. Garanta `DEBUG=0` fora de desenvolvimento.
4. Não commite `.env`.

## Rodando com Docker

- O deploy padrão usa `docker compose`.
- O serviço web depende do PostgreSQL definido em `.env`.
- O `deploy.sh` valida a presença do `.env` antes de subir.

## Desenvolvimento

- Use `python manage.py migrate` para aplicar migrations.
- Use `python manage.py runserver` apenas em desenvolvimento local, se necessário.
- Sempre prefira `service + selector + schema` ao adicionar regras novas.

## Referências

- `README.md`
- `docs/AI_CONTEXT.md`
- `docs/ESCOPO.md`
- `skills/tarugo-architecture/SKILL.md`
