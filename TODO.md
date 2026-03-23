# TODO — Tarugo MVP

## 🎯 Objetivo do MVP

Entregar um sistema funcional com:

- Login de usuários
- Controle de estoque com movimentações
- Base pronta para integração futura

---

# 🧱 FASE 1 — Base do Projeto

## Setup

- [ ] Criar ambiente virtual
- [ ] Instalar dependências (Django, DRF, Pydantic)
- [ ] Criar projeto Django
- [ ] Estruturar pastas (apps, core)

## Configuração

- [ ] Ajustar INSTALLED_APPS
- [ ] Configurar paths (apps/)
- [ ] Subir servidor local

---

# 🔐 FASE 2 — Autenticação

## Usuário

- [ ] Configurar auth padrão do Django
- [ ] Criar superuser
- [ ] Testar login no admin

## API (opcional MVP+)

- [ ] Endpoint de login (token ou session)
- [ ] Proteção de endpoints

---

# 📦 FASE 3 — Estoque (CORE DO MVP)

## Produto

- [ ] Model Produto
- [ ] Migrações
- [ ] CRUD básico via API

## Movimentação (IMPORTANTE)

- [ ] Criar model Movimentacao

  - produto
  - tipo (entrada/saida)
  - quantidade
  - data
- [ ] Criar schema Pydantic
- [ ] Criar service de movimentação
- [ ] Implementar regras:

  - impedir estoque negativo
  - validar tipo
  - validar quantidade
- [ ] Criar endpoint:

  - POST movimentação

## Histórico

- [ ] Listar movimentações por produto
- [ ] Ordenação por data

---

# 📊 FASE 4 — Melhorias no Estoque

- [ ] Alerta de estoque mínimo
- [ ] Campo calculado de status (ok / crítico)
- [ ] Endpoint de listagem com filtros

---

# 🧪 FASE 5 — Testes Básicos

- [ ] Testar criação de produto
- [ ] Testar entrada de estoque
- [ ] Testar saída válida
- [ ] Testar saída inválida (erro)

---

# 🔌 FASE 6 — Integrações (PREPARAÇÃO)

## Estrutura

- [ ] Criar app integracoes
- [ ] Criar pasta services

## Base

- [ ] Criar classe base de integração
- [ ] Implementar logs
- [ ] Estrutura de retry (simples)

## Estudo Dinabox

- [ ] Mapear endpoints da API
- [ ] Entender autenticação
- [ ] Definir primeiros dados a integrar (produtos)

---

# 📚 FASE 7 — Biblioteca de Scripts

- [ ] Criar model Script

  - nome
  - descrição
  - código
  - tipo
- [ ] CRUD de scripts
- [ ] Organização por categoria

---

# 💰 FASE 8 — Orçamentos (PLANEJAMENTO)

- [ ] Definir estrutura de orçamento
- [ ] Modelar itens
- [ ] Relacionar com produtos

---

# 🚀 FASE FINAL — Preparação para Uso

- [ ] Ajustar permissões
- [ ] Validar fluxo completo
- [ ] Criar dados de teste
- [ ] Documentar endpoints

---

# 🔥 FUTURO (PÓS-MVP)

- [ ] Dashboard
- [ ] Celery + tarefas assíncronas
- [ ] Backup automático
- [ ] Multi-empresa (SaaS)
