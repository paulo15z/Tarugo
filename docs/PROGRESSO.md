# Progresso do Tarugo

## Status geral

- Base Django organizada
- Estoque funcional como MVP operacional
- Integração Dinabox com schemas especializados
- Deploy migrado para PostgreSQL com `.env`

## Fase atual

1. Harden do deploy e documentação
2. Ajustes finos no estoque e integrações
3. Consolidação do padrão de arquitetura

## Notas de infraestrutura

- `db.sqlite3` não deve mais ser usado no deploy padrão
- `docker compose` e `deploy.sh` assumem PostgreSQL
- `.env.example` serve como base segura para o ambiente local

## Próximos passos

- Revisar permissões e grupos
- Consolidar integrações Dinabox
- Criar testes de regressão para deploy e schemas
