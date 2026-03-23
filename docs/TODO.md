# TODO — Tarugo MVP

## 🎯 Objetivo do MVP

Entregar um sistema funcional com:

- Login de usuários
- Controle de estoque com movimentações
- Base pronta para integração futura

---

# 🧱 FASE 1 — Base do Projeto ✅

## Setup ✅

- [x] Criar ambiente virtual
- [x] Instalar dependências (Django, DRF, Pydantic)
- [x] Criar projeto Django
- [x] Estruturar pastas (apps, core)

## Configuração ✅

- [x] Ajustar INSTALLED_APPS
- [x] Configurar paths (apps/)
- [x] Subir servidor local

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

# 📦 FASE 3 — Estoque (CORE DO MVP) ✅

## Produto ✅

- [x] Model Produto
- [x] Migrações
- [x] CRUD básico via API (POST /produtos/)

## Movimentação (IMPORTANTE) ✅

- [x] Implementar transaction.atomic
- [x] Implementar select_for_update
- [x] Criar histórico de movimentações
- [x] Garantir consistência de estoque
- [x] Criar model Movimentacao
  - [x] produto
  - [x] tipo (entrada/saida)
  - [x] quantidade
  - [x] criado_em (data de rastreamento)
- [x] Criar schema Pydantic (MovimentacaoSchema)
- [x] Criar service de movimentação (processar_movimentacao)
- [x] Implementar regras:
  - [x] impedir estoque negativo
  - [x] validar tipo
  - [x] validar quantidade
- [x] Criar endpoints:
  - [x] POST /movimentar/

## Histórico ✅

- [x] Listar movimentações por produto (GET /movimentacoes/)
- [x] Ordenação por data (DESC por criado_em)
- [x] Filtros avançados (produto_id, data_inicio, data_fim)
- [x] **NOVO:** Paginação com limit/offset

---

# � FASE 3.5 — Refatoração Estoque por Tipos (EM PLANEJAMENTO)

**Objetivo:** Quebrar o modelo genérico `Produto` em tipos específicos para refletir a realidade do negócio.

## ChapaMDF (novo modelo)

- [ ] Criar model ChapaMDF com campos:
  - [ ] produto (FK)
  - [ ] acabamento (branco_tx, rosa, amarelo, etc)
  - [ ] espessura (15mm, 18mm, 25mm)
  - [ ] comprimento (2750mm padrão)
  - [ ] largura (1830mm padrão)
  - [ ] projeto_id (null = padrão, X = sob demanda)
  - [ ] status (disponivel, separada, em_corte)
  - [ ] quantidade
- [ ] Migrations
- [ ] Service: `chapa_mdf_service.py`
- [ ] Selector: `chapa_mdf_selectors.py`

## SobraChapaMDF (rastreamento de restos)

- [ ] Criar model SobraChapaMDF com:
  - [ ] chapa_original (FK para ChapaMDF)
  - [ ] dimensões_resto (comprimento, largura)
  - [ ] projeto_origem_id (herda de chapa_original)
  - [ ] status (disponivel, bloqueada, utilizada)
  - [ ] projeto_utilizado_em (null até reutilização)
  - [ ] data_utilizacao
  - [ ] autorizado_por_usuario
- [ ] Rule: Bloqueio automático se projeto_origem está ativo
- [ ] Rule: Liberação se projeto_origem é CONCLUÍDO ou admin autoriza
- [ ] Migrations

## PedidoDeCorte (planejamento)

- [ ] Criar model PedidoDeCorte
  - [ ] projeto_id
  - [ ] data_prevista_corte
  - [ ] status (planejado, em_corte, concluído)
  - [ ] data_criacao
- [ ] Migrations

## ChapaMDFPedido (vinculação chapa ↔ pedido)

- [ ] Criar model ChapaMDFPedido
  - [ ] pedido (FK)
  - [ ] chapa_mdf (FK)
  - [ ] quantidade_planejada
  - [ ] data_separacao
  - [ ] status (separada, em_corte, cortada)
- [ ] Migrations

## Services & Selectors

- [ ] `chapa_mdf_service.py` com validações
- [ ] `sobra_mdf_service.py` com regra de bloqueio
- [ ] `pedido_corte_service.py`
- [ ] Selectors para cada modelo

## Endpoints

- [ ] `POST /chapas-mdf/` — registrar chapa
- [ ] `GET /chapas-mdf/` — listar com filtros
- [ ] `POST /sobras-mdf/` — registrar sobra após corte
- [ ] `GET /sobras-mdf/` — listar sobras disponíveis
- [ ] `POST /pedidos-corte/` — criar planejamento
- [ ] `GET /pedidos-corte/` — listar pedidos

## Testes

- [ ] Criar chapa padrão (Branco TX)
- [ ] Criar chapa sob demanda (projeto_id = X)
- [ ] Registrar sobra e validar bloqueio
- [ ] Tentar usar sobra bloqueada (deve falhar)
- [ ] Fechar projeto e tentar reutilizar (deve funcionar)
- [ ] Admin autoriza reutilização (deve funcionar)

---

# 📦 FASE 4 — Modelos Adicionais (após ChapaMDF)

## Ferragem

- [ ] Criar model Ferragem
  - [ ] produto (FK)
  - [ ] especificacao (dobradiça 180°, etc)
  - [ ] codigo_fornecedor
  - [ ] fornecedor_id (FK)
  - [ ] quantidade
- [ ] Service e selector

## Acessorio

- [ ] Criar model Acessorio
  - [ ] produto
  - [ ] tamanho
  - [ ] cor
  - [ ] quantidade
- [ ] Service e selector

## Insumo

- [ ] Criar model Insumo
  - [ ] produto
  - [ ] unidade_medida (litro, kg, unidade)
  - [ ] tamanho_embalagem
  - [ ] quantidade
- [ ] Service e selector

## Endpoints para todos

- [ ] GET com paginação e filtros
- [ ] POST para criar

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
