# Contexto do Projeto - Tarugo

## Sobre

Tarugo é uma plataforma web em Django voltada para indústrias moveleiras.

## Stack atual

- Django
- Django REST Framework
- Pydantic
- PostgreSQL
- Docker / Docker Compose
- Proxmox para ambiente local

## Arquitetura

- `core` -> autenticação e base
- `estoque` -> produtos e movimentações
- `integracoes` -> APIs externas
- `pcp` -> legado funcional, em estabilização
- `scripts` e `orcamentos` -> planejados

## Regras importantes

- Não colocar regra de negócio em views
- Sempre usar services
- Validar com Pydantic na camada de domínio
- Segredos apenas em `.env`

## Fluxo

Request -> Serializer -> Service -> Model -> Banco -> Response

## Documento de referência

- `skills/tarugo-architecture/SKILL.md`
- `skills/dinabox-integration.md`
