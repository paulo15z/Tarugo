# 📦 App Pedidos - Tarugo 1.1

## Visão Geral

O app **Pedidos** é o **centralizador do ciclo de vida do pedido** no Tarugo, funcionando como um **"Gêmeo Digital Evolutivo"** que se enriquece progressivamente conforme o pedido avança pelas etapas de production.

### Princípio Central: Evolução Progressiva

O Pedido **não é estático**. Ele nasce no Comercial com informações comerciais simples e se expande com:
- **Dados de Engenharia** (Dinabox API)
- **Métricas de PCP** (Planejamento de Produção)
- **Dados Operacionais** (Bipagem, Expedição)
- **Status de Montagem** (Instalação no cliente)

Isso garante uma **Single Source of Truth** dinâmica e completa.

---

## 🏗️ Arquitetura

Segue rigorosamente o padrão **Tarugo Architecture**:

```
Request → API View → Service (Pydantic) → Selector → Model → Response
```

### Camadas

| Camada | Arquivo | Responsabilidade |
|--------|---------|-----------------|
| **Domain** | `domain/status.py` | Enums puros (Status) |
| **Models** | `models/` | ORM apenas (sem lógica) |
| **Services** | `services/__init__.py` | Regras de negócio (orquestração) |
| **Selectors** | `selectors/__init__.py` | Consultas otimizadas ao banco |
| **Schemas** | `schemas/__init__.py` | Validação Pydantic |
| **Mappers** | `mappers/__init__.py` | Conversão Model ↔ Schema |
| **API** | `api/__init__.py` | Views HTTP (DRF) |
| **Serializers** | `api/serializers.py` | Serialização DRF |
| **Views** | `views.py` | Renderização HTML/Templates |
| **Admin** | `admin.py` | Interface Django Admin |

---

## 📊 Modelos de Dados

### Pedido
Entidade central com identificador único `numero_pedido`.

**Campos Principais:**
- `numero_pedido`: Identificador único (gerado no Comercial)
- `customer_id`: Referência ao cliente na Dinabox
- `cliente_nome`: Nome do cliente
- `status`: Estado atual no ciclo de vida
- `data_criacao`, `data_contrato`, `data_entrega_prevista`, `data_conclusao`
- `observacoes`: Notas gerenciais

**Properties:**
- `total_ambientes`: Quantidade de ambientes
- `ambientes_concluidos`: Ambientes finalizados
- `percentual_conclusao`: % de progresso

### AmbientePedido
Sub-unidade de produção (COZINHA, DORMITÓRIO, etc).

**Campos Principais:**
- `nome_ambiente`: Ex: "COZINHA SUPERIOR"
- `status`: Estado específico do ambiente
- `dados_engenharia`: JSON com dados técnicos (Dinabox)
- `metricas_pcp_resumo`: JSON com dados do PCP
- `dados_operacionais_resumo`: JSON com bipagem/expedição
- `lotes_pcp`: ManyToMany com lotes do PCP

### HistoricoStatusPedido
Auditoria imutável de mudanças de status.

**Campos:**
- `status_anterior`, `status_novo`
- `motivo`: Razão da transição
- `usuario`: Quem fez a mudança
- `data_criacao`

---

## 🔄 Status e Transições

### Status do Pedido
```python
CONTRATO_FECHADO → EM_ENGENHARIA → EM_PRODUCAO → EXPEDICAO → MONTAGEM → CONCLUIDO
```

- **CONTRATO_FECHADO**: Pedido criado, awaiting engineering
- **EM_ENGENHARIA**: Dados técnicos sendo processados
- **EM_PRODUCAO**: Pelo menos um ambiente em produção
- **EXPEDICAO**: Pronto para envio
- **MONTAGEM**: Em instalação no cliente
- **CONCLUIDO**: Ciclo finalizado
- **CANCELADO**: Cancelado

### Status do Ambiente
```python
PENDENTE → EM_ENGENHARIA → AGUARDANDO_PCP → EM_INDUSTRIA → EM_MONTAGEM → CONCLUIDO
```

---

## 🔗 Fluxo de Integração

### 1️⃣ Comercial → Pedidos
```python
PedidoService.criar_pedido_do_comercial(cliente_comercial, numero_pedido)
```
- Cria Pedido com status `CONTRATO_FECHADO`
- Cria AmbientePedido para cada AmbienteOrcamento

### 2️⃣ Dinabox (Engenharia) → Pedidos
```python
PedidoService.processar_engenharia_ambiente(ambiente, dados_engenharia)
```
- Popula `dados_engenharia` do ambiente
- Muda ambiente para `AGUARDANDO_PCP`
- Se todos aguardando PCP → Pedido muda para `EM_ENGENHARIA`

### 3️⃣ PCP → Pedidos
```python
PedidoService.vincular_lote_pcp(ambiente, lote_pcp, metricas_pcp)
```
- Associa LotePCP ao ambiente
- Atualiza `metricas_pcp_resumo`
- Muda ambiente para `EM_INDUSTRIA`
- Se todos em produção → Pedido muda para `EM_PRODUCAO`

### 4️⃣ Bipagem/Expedição → Pedidos
```python
PedidoService.atualizar_dados_operacionais(ambiente, dados_operacionais)
```
- Atualiza `dados_operacionais_resumo`
- Se 100% expedido → Ambiente muda para `CONCLUIDO`

---

## 🛠️ Como Usar

### Criar Pedido a partir do Comercial

```python
from apps.comercial.models import ClienteComercial
from apps.pedidos.services import PedidoService

cliente = ClienteComercial.objects.get(customer_id="12345")
pedido = PedidoService.criar_pedido_do_comercial(
    cliente_comercial=cliente,
    numero_pedido="PED-2026-001",
    usuario=user  # opcional
)
```

### Atualizar Status

```python
from apps.pedidos.models import Pedido
from apps.pedidos.services import PedidoService
from apps.pedidos.domain.status import PedidoStatus

pedido = Pedido.objects.get(numero_pedido="PED-2026-001")
pedido = PedidoService.atualizar_status_pedido(
    pedido=pedido,
    novo_status=PedidoStatus.EM_ENGENHARIA,
    motivo="Todos ambientes recebidos da Dinabox",
    usuario=user
)
```

### Processar Engenharia (Dinabox)

```python
from apps.pedidos.models import AmbientePedido
from apps.pedidos.services import PedidoService

ambiente = AmbientePedido.objects.get(pk=1)
ambiente = PedidoService.processar_engenharia_ambiente(
    ambiente=ambiente,
    dados_engenharia={
        "dimensoes": "2750x1830",
        "furacoes": [...],
        "usinagens": [...]
    },
    usuario=user
)
```

### Vincular Lote PCP

```python
from apps.pcp.models import LotePCP

lote = LotePCP.objects.get(pk=1)
ambiente = PedidoService.vincular_lote_pcp(
    ambiente=ambiente,
    lote_pcp=lote,
    metricas_pcp={
        "total_pecas_pcp": 120,
        "pecas_corte_estimado": 100,
        "tempo_producao_estimado_horas": 8.5
    }
)
```

### Buscar Pedidos (Selectors)

```python
from apps.pedidos.selectors import PedidoSelector

# Todos os pedidos ativos
pedidos = PedidoSelector.list_pedidos_ativos()

# Por status
em_producao = PedidoSelector.list_pedidos_por_status("EM_PRODUCAO")

# Por cliente
pedidos_cliente = PedidoSelector.list_pedidos_por_cliente("12345")

# Detalhado (com ambientes e histórico)
pedido = PedidoSelector.get_pedido_completo("PED-2026-001")

# Busca
resultados = PedidoSelector.search_pedidos("Sérgio")

# Em atraso
atrasados = PedidoSelector.list_pedidos_em_atraso()
```

### API REST

```bash
# Listar pedidos
GET /api/pedidos/?status=EM_PRODUCAO&limit=20

# Detalhes
GET /api/pedidos/PED-2026-001/

# Atualizar status
POST /api/pedidos/PED-2026-001/atualizar-status/
{
  "novo_status": "EM_PRODUCAO",
  "motivo": "Lote iniciou produção"
}

# Histórico de mudanças
GET /api/pedidos/PED-2026-001/historico-status/

# Listar ambientes
GET /api/ambientes/?pedido_numero=PED-2026-001

# Processar engenharia
POST /api/ambientes/1/processar-engenharia/
{
  "dimensoes": "2750x1830",
  "furacoes": [...],
  "usinagens": [...]
}
```

---

## 🔒 Regras de Negócio (Obrigatórias)

1. **Toda lógica reside em Services** ✅
   - Views apenas chamam services
   - Selectors centralizam queries

2. **Validação dupla** ✅
   - DRF (entrada HTTP)
   - Pydantic (regra de negócio)

3. **Transições de Status Atomicamente** ✅
   - `@transaction.atomic` em todas as mudanças
   - Histórico registrado em tempo real

4. **Soft-delete na auditoria** ✅
   - Nunca deletar, apenas desativar
   - HistoricoStatusPedido é imutável

5. **Properties para cálculos** ✅
   - `percentual_conclusao` sempre calculado
   - Não armazenar valores derivados

---

## 📋 Validação Pydantic

Todo input pass por validação Pydantic antes de ser processado:

```python
from apps.pedidos.schemas import AtualizarStatusSchema

input_data = {"novo_status": "EM_PRODUCAO", "motivo": "..."}
schema = AtualizarStatusSchema(**input_data)
# Valida tipo, enum, obrigatoriedade
```

---

## 🎯 Rodeiro de Implementação

- [ ] Migração inicial: `python manage.py makemigrations && python manage.py migrate`
- [ ] Admin interface: Acessar `/admin/pedidos/`
- [ ] API: Testar endpoints em `/api/pedidos/`
- [ ] Templates: Renderizar dashboard em `/pedidos/`
- [ ] Integração com Comercial
- [ ] Integração com Dinabox (Engenharia)
- [ ] Integração com PCP
- [ ] Integração com Bipagem/Expedição

---

## 📚 Referências

- [Arquitetura Tarugo](../skills/tarugo-architecture.skill)
- [Frontend Design](../skills/tarugo-frontend-1-1.skill)
- [Django Docs](https://docs.djangoproject.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [Django REST Framework](https://www.django-rest-framework.org/)

---

## 👥 Responsabilidades

| Papel | Interações |
|-------|-----------|
| **Comercial** | Cria pedido via `criar_pedido_do_comercial()` |
| **Engenharia (Dinabox)** | Alimenta `processar_engenharia_ambiente()` |
| **PCP** | Limpa `vincular_lote_pcp()` |
| **Bipagem** | Atualiza `atualizar_dados_operacionais()` |
| **Operações** | Consulta via Selectors |

---

## 🚀 Próximas Etapas

1. Gerar migrations: `python manage.py makemigrations apps.pedidos`
2. Aplicar migrations: `python manage.py migrate`
3. Registrar no admin (✅ já feito)
4. Testar API REST
5. Criar frontend com feedback visual
6. Integrar com webhooks do Dinabox
7. Implementar notificações de mudança de status
