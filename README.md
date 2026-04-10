# Tarugo

Sistema modular em Django para indústrias moveleiras, com foco em operação real, integrações e evolução segura.

## Estado atual

- `estoque` segue como foco principal de uso real
- `pcp` permanece congelado no curto prazo
- `integracoes` evolui com o fluxo Dinabox e validação por schemas
- Deploy atual usa PostgreSQL, `.env` local e `docker compose`

## Princípios

- Models para estrutura
- Services para regra de negócio
- Selectors para consultas
- Schemas Pydantic para validação de domínio
- Não colocar segredos no repositório

## Documentação principal

- [Setup local e deploy seguro](docs/SETUP.md)
- [Escopo atual](docs/ESCOPO.md)
- [Progresso do projeto](docs/PROGRESSO.md)
- [Contexto geral](docs/AI_CONTEXT.md)
- [Fluxo Proxmox com PostgreSQL](Guia%20de%20Configura%C3%A7%C3%A3o%20de%20Ambiente%20no%20Proxmox%20-%20Tarugo%20v1.1.md)

## Skills de referência

- `skills/tarugo-architecture/SKILL.md` para padrões de arquitetura e decisão técnica
- `skills/dinabox-integration.md` para integração e normalização Dinabox

## Deploy

1. Copie `.env.example` para `.env` e preencha os valores reais.
2. Rode `./deploy.sh` no CT da aplicação ou `docker compose up -d` conforme o ambiente.
3. Use `DEBUG=0` fora de desenvolvimento.

## Stack

Django 6, DRF, Pydantic, PostgreSQL, Docker, Proxmox
