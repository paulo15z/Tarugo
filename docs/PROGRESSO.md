# 📊 PROGRESSO DO TARUGO — Status Desenvolvimento

**Data:** 23 de Março de 2026  
**Status Geral:** MVP Estoque Funcional + Planejamento de Evolução

---

## ✅ O QUE FOI FEITO ATÉ AGORA

### FASE 1 — Base do Projeto ✅

- ✅ Ambiente virtual configurado (venv)
- ✅ Dependências instaladas (Django 6.0.3, DRF, Pydantic)
- ✅ Projeto Django estruturado com apps modular
- ✅ Pastas organizadas: `apps/`, `config/`, `docs/`
- ✅ INSTALLED_APPS configurado
- ✅ Paths do workspace ajustados

### FASE 3 — Estoque (CORE DO MVP) ✅

#### Models ✅
- ✅ `Produto` — genérico (será refatorado)
- ✅ `Movimentacao` — com campo `criado_em` para rastreamento

#### Services ✅
- ✅ `processar_movimentacao()` com:
  - `transaction.atomic` (consistência garantida)
  - `select_for_update` (lock pessimista contra race condition)
  - Validação de estoque insuficiente
- ✅ `criar_produto()`

#### Validação ✅
- ✅ Dupla camada:
  - DRF (serializers na entrada HTTP)
  - Pydantic (regras de negócio no service)
- ✅ Schemas: `MovimentacaoSchema`

#### Endpoints ✅
- ✅ `POST /produtos/` — criar produto
- ✅ `POST /movimentar/` — processar entrada/saída
- ✅ `GET /movimentacoes/` — listar histórico

#### Selectors ✅
- ✅ `listar_movimentacoes(produto_id, data_inicio, data_fim)`

#### Paginação ✅
- ✅ Implementada em `GET /movimentacoes/`
- ✅ Parâmetros: `limit` (padrão 10), `offset`
- ✅ Response com meta data: `total`, `tem_proxima`
- ✅ Validação de parâmetros

#### Migrations ✅
- ✅ Banco sincronizado
- ✅ Tabelas criadas: `estoque_produto`, `estoque_movimentacao`

#### Testes ✅
- ✅ `test_estoque.py` — validação básica de models
- ✅ `test_service.py` — validação de service com transaction.atomic
- ✅ `test_paginacao.py` — validação de paginação (6 testes, todos passando)

---

## 🔄 ESTRUTURA ATUAL DO CÓDIGO

```
apps/estoque/
├── models/
│   ├── produto.py          # Genérico (será quebrado em tipos)
│   ├── movimentacao.py     # Rastreamento de tudo
│   └── __init__.py
├── services/
│   ├── movimentacao_services.py
│   ├── produto_service.py
│   └── schemas.py          # Pydantic schemas
├── selectors/
│   └── movimentacao_selectors.py
├── api/
│   ├── views.py            # APIViews
│   ├── serializers.py      # DRF serializers
│   └── __init__.py
└── migrations/
    └── 0001_initial.py

config/
├── urls.py                 # Rutas registradas
├── settings.py             # INSTALLED_APPS correto
└── ...

docs/
├── AI_CONTEXT.md           # Contexto geral
├── ESCOPO.md               # Visão e objetivos
├── TODO.md                 # Tarefas (será atualizado)
├── PROGRESSO.md            # ← Este arquivo
└── PROCESSOS_ATUAIS.md     # ← Novo (explicar como funciona hoje)
```

---

## 🚀 PRÓXIMOS PASSOS (ROADMAP)

### PRÓXIMA ETAPA: Refatorar Estoque para Tipos Específicos

#### Por que refatorar?
O modelo `Produto` atual é muito genérico e não reflete a realidade do negócio:
- MDFs têm dimensões (comprimento, largura, espessura)
- Ferragens têm especificações diferentes
- Insumos usam unidades variáveis (litro, kg, unidade)
- Produtos sob demanda precisam vínculo com projeto

#### Estrutura Nova (em ordem de implementação):

1. **Produto (base)** — manter genérico
   ```python
   Produto(
       nome,
       sku,
       tipo="chapa_mdf"  # enum: chapa_mdf, ferragem, acessorio, insumo
   )
   ```

2. **ChapaMDF** — específico para MDFs
   ```python
   ChapaMDF(
       produto: FK,
       acabamento: "Branco TX",  # ou "Rosa", "Amarelo", etc
       espessura: 18,             # em mm
       comprimento: 2750,         # em mm
       largura: 1830,             # em mm
       projeto_id: null,          # null=padrão, 123=sob demanda
       quantidade: 5,
       status: "disponivel"
   )
   ```

3. **SobraChapaMDF** — resto após corte
   ```python
   SobraChapaMDF(
       chapa_original: FK(ChapaMDF),
       projeto_origem_id,         # herda de chapa_original
       comprimento: 750,
       largura: 1830,
       espessura: 18,
       status: "disponivel",      # ou "bloqueada" (sob demanda)
       projeto_utilizado_em: null,    # se foi usada em outro projeto
       data_utilizacao: null,
       autorizado_por: null           # quem autorizou
   )
   ```

4. **Ferragem, Acessorio, Insumo** — modelos específicos
   ```python
   Ferragem(produto, especificacao, codigo_fornecedor, quantidade)
   Acessorio(produto, tamanho, cor, quantidade)
   Insumo(produto, unidade_medida, tamanho_embalagem, quantidade)
   ```

5. **PedidoDeCorte** — planejamento
   ```python
   PedidoDeCorte(
       projeto_id,
       data_prevista_corte,
       status: "planejado"  # planejado → em_corte → concluído
   )
   ```

6. **ChapaMDFPedido** — vinculação
   ```python
   ChapaMDFPedido(
       pedido: FK(PedidoDeCorte),
       chapa_mdf: FK(ChapaMDF),
       quantidade_planejada,
       data_separacao,
       status: "separada"  # separada → em_corte → cortada
   )
   ```

#### Regra de Negócio: Bloqueio de Sobras
```
Sobra de Padrão (projeto_id = null):
  ✅ Disponível IMEDIATAMENTE para qualquer projeto
  
Sobra de Sob Demanda (projeto_id = 123):
  ❌ BLOQUEADA enquanto projeto está ATIVO
  ✅ LIBERADA quando:
    - Projeto status = CONCLUÍDO, OU
    - Admin autoriza manualmente
  - Depois liberada: pode ir para outro projeto
  - Rastreamento: qual projeto usou depois (auditoria)
```

---

## 📅 FASES FUTURAS (do TODO.md)

- **FASE 2:** Autenticação (login, usuários, permissões)
- **FASE 4:** Melhorias no Estoque (alertas, status, filtros)
- **FASE 5:** Testes Básicos (testes unitários conforme TODO)
- **FASE 6:** Integrações (preparação para Dinabox, ERPs)
- **FASE 7:** Biblioteca de Scripts (Ruby, Dinabox)
- **FASE 8:** Orçamentos
- **FASE FINAL:** Preparação para uso em produção

---

## 📝 DECISÕES DE DESIGN EXPLICADAS

### 1. Por que `transaction.atomic` + `select_for_update`?
**Problema:** Dois usuários separam a mesma chapa ao mesmo tempo → inconsistência.

**Solução:**
- `select_for_update()` = trava o registro no banco enquanto processa
- `transaction.atomic` = tudo ou nada (não salva se tiver erro)

### 2. Por que separar Models Específicos em vez de JSON genérico?
**Ruim:** `VariacaoProduto(dados={"espessura": "18mm", "cor": "branco"})`
- Sem tipagem
- Impossível validar
- Queries complexas

**Bom:** `ChapaMDF(espessura=18, acabamento="branco")`
- Tipado no banco
- Queries simples
- Validação nativa

### 3. Por que Paginação?
**Realidade:** Estoque com 10.000+ produtos. GET sem limit?
- Travaria o servidor
- Serializar tudo = lento
- Paginação = eficiente

### 4. Por que Selector?
**Padrão:** Models → Services → Selectors → API
- Cada camada uma responsabilidade
- Reutilizável
- Testável

---

## 🎓 CONCEITOS APRENDIDOS

1. **Django ORM:** Models, querysets, migrations
2. **DRF:** Serializers, APIViews, validação
3. **Pydantic:** Schemas, validação de dados
4. **Transactions:** ACID, atomicidade
5. **Concorrência:** Race conditions, locks
6. **Architecture:** Separação de responsabilidades
7. **API Design:** Paginação, filtros, status codes

---

## 📊 MÉTRICAS

| Métrica | Valor |
|---------|-------|
| Modelos implementados | 2 (Produto, Movimentacao) |
| Services | 2 (produto, movimentacao) |
| Endpoints | 3 (criar produto, mover, listar) |
| Testes criados | 3 scripts com 10+ casos |
| Cobertura | Fluxo básico de estoque |
| Taxa de sucesso | 100% (todos testes passam) |

---

## 🔗 Arquivos Principais

- [apps/estoque/models/produto.py](../apps/estoque/models/produto.py)
- [apps/estoque/models/movimentacao.py](../apps/estoque/models/movimentacao.py)
- [apps/estoque/services/movimentacao_services.py](../apps/estoque/services/movimentacao_services.py)
- [apps/estoque/api/views.py](../apps/estoque/api/views.py)
- [apps/estoque/selectors/movimentacao_selectors.py](../apps/estoque/selectors/movimentacao_selectors.py)
- [config/urls.py](../config/urls.py)
- [config/settings.py](../config/settings.py)

---

## ✏️ Próxima Sessão

Começar refatoração para modelos específicos:
1. Criar `ChapaMDF` com campos específicos
2. Criar `SobraChapaMDF` com regra de bloqueio
3. Implementar `ChapaMDFService` com validações
4. Testes do novo fluxo
5. Endpoints para listar chapas

**Tempo estimado:** 2-3 horas (com explicações)
