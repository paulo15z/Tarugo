# 🎯 Próximas Etapas - Tarugo Roadmap

**Status**: ✅ Comercial completo | ✅ App Pedidos criado (estrutura) | Integrações iniciando  
**Data**: 12/04/2026  
**Última atualização**: App Pedidos estruturado conforme tarugo-architecture

---

## 🔧 Status do Comercial (Completo)

✅ **MVP Completo** — Comercial está pronto para receber pedidos

### ✅ Implementado
- [x] Criar cliente (Dinabox + Tarugo)
- [x] Sincronizar cliente existente
- [x] Editar status pipeline (primeiro contato → contrato fechado)
- [x] Adicionar observações gerais
- [x] Registrar ambientes (nome + valor)
- [x] Detalhar ambientes (acabamentos + eletros + obs especiais)
- [x] Selector estruturado para enviar para Pedidos

### ✅ Resolvido em Etapas Anteriores
- [x] Erro `NoReverseMatch: 'ambiente_excluir_post'` 
- [x] Migration conflicts
- [x] Frontend ambiente_detalhes

### 📋 Pendente (Nice-to-have v2)
- [ ] Validação robusta de duplicatas (case-insensitive)
- [ ] Histórico de alterações por usuário
- [ ] Template de ambientes comuns pré-preenchidos

**Status**: READY FOR PRODUCTION ✨



---

## ✅ App PEDIDOS - Status de Implementação

**Estrutura completa criada** em `apps/pedidos/` seguindo **100% do padrão Tarugo Architecture**:

### ✅ Implementado (12/04/2026)

#### Camadas
- [x] **Domain** (`domain/status.py`) - Enums `PedidoStatus`, `AmbienteStatus`
- [x] **Models** (3 modelos):
  - `Pedido` - Central com snapshot do cliente, data de entrega, observações
  - `AmbientePedido` - Sub-unidades (COZINHA, SUITE, etc) com JSONField para dados técnicos
  - `HistoricoStatusPedido` - Auditoria imutável de transições
- [x] **Services** - `PedidoService` com:
  - `criar_pedido_do_comercial()` - Cria atomicamente pedido + ambientes
  - `atualizar_status_pedido()` - Transição com histórico
  - `processar_engenharia_ambiente()` - Integração Dinabox
  - `vincular_lote_pcp()` - Integração PCP
  - `atualizar_dados_operacionais()` - Dados de bipagem/expedição
- [x] **Selectors** - 3 classes com queries otimizadas:
  - `PedidoSelector` - Listar, filtrar, buscar pedidos
  - `AmbienteSelector` - Listar, filtrar ambientes
  - `HistoricoStatusSelector` - Histórico de transições
- [x] **Schemas Pydantic** - 10+ schemas para validação
- [x] **Mappers** - Conversão automática Model ↔ Schema
- [x] **API REST** - 6+ endpoints DRF
- [x] **Admin Interface** - 3 modelos registrados com fieldsets
- [x] **Templates** - 4 templates HTML com dashboard, detalhes, busca
- [x] **Documentação** - README.md completo + IMPLEMENTACAO.md

#### Configuração
- [x] Registrado em `INSTALLED_APPS` 
- [x] URLs adicionadas (`config/urls.py`)
- [x] App configurado (`apps.py`)

### 🔄 Próximas Etapas Imediatas

#### 1. Migrações (5 min)
```bash
python manage.py makemigrations apps.pedidos
python manage.py migrate
```

#### 2. Testar Admin Interface (10 min)
- Acessar `/admin/pedidos/`
- Criar teste de Pedido manualmente
- Verificar relacionamentos

#### 3. Integração com Comercial (2-3 horas)
- [ ] Importar `PedidoService` em `apps/comercial/services.py`
- [ ] Adicionar botão "Criar Pedido" no detalhe de ClienteComercial
- [ ] View que chama `criar_pedido_do_comercial()`
- [ ] Redirect para `/pedidos/api/pedidos/{numero_pedido}/`

**Arquivo para editar**: [apps/comercial/views.py](apps/comercial/views.py)

```python
from apps.pedidos.services import PedidoService

def cliente_criar_pedido(request, pk):
    cliente = get_object_or_404(ClienteComercial, pk=pk)
    numero_pedido = ComercialService.gerar_numero_pedido()  # TODO: Implementar
    pedido = PedidoService.criar_pedido_do_comercial(
        cliente_comercial=cliente,
        numero_pedido=numero_pedido,
        usuario=request.user
    )
    messages.success(request, f"Pedido {pedido.numero_pedido} criado com sucesso!")
    return redirect('pedidos:api-pedido-detail', numero_pedido=pedido.numero_pedido)
```

#### 4. Integração com Dinabox (3-4 horas)
- [ ] Hook em `apps/integracoes/services.py` para chamar `processar_engenharia_ambiente()`
- [ ] Quando projeto Dinabox é sincronizado, extrair ambiente detalhes
- [ ] Mapear projeto → ambientes mapeados para `AmbientePedido`

**Exemplo**:
```python
# Em DinaboxIntegrationService.process_project()
for modulo in projeto_dados['modulos']:
    ambiente = AmbientePedido.objects.get(
        pedido__customer_id=customer_id,
        nome_ambiente=modulo['name']
    )
    PedidoService.processar_engenharia_ambiente(
        ambiente=ambiente,
        dados_engenharia=modulo['tecnico_dados']
    )
```

#### 5. Integração com PCP (4-5 horas)

**Fluxo Correto - Projetos → Auto-criar Lote → PCP Confirma**

Quando Projetos marca projeto como "CONCLUÍDO" (dados engenharia finalizados):
1. **AUTOMÁTICO**: Lote PCP é criado automaticamente
2. **RESULTADO**: PCP recebe notificação + lista de "Lotes Prontos para Análise"
3. **AÇÃO DO PCP**: Valida specs, ajusta cronograma/horas
4. **CONFIRMAÇÃO**: Chama `vincular_lote_pcp()` com dados validados

**Implementação em 2 etapas**:

**ETAPA 1 - Projetos cria Lote (automático)**
```python
# Em ProjetosService.marcar_projeto_concluido()
projeto = Projeto.objects.get(pk=projeto_id)
lote = LotePCP.objects.create(
    numero_lote=f"LOTE-{projeto.pedido_numero}-{projeto.id}",
    pedido_numero=projeto.pedido_numero,
    total_pecas=projeto.calcular_total_pecas(),
    horas_estimadas=projeto.calcular_horas_engenharia(),
    status='AGUARDANDO_VALIDACAO_PCP',  # Estado novo
    origem='PROJETO_CONCLUIDO'
)
# → Notificar PCP: "Novo lote disponível para análise"
```

**ETAPA 2 - PCP valida e vincula**
```python
# Em PCPService.validar_e_vincular_lote(lote_id)
lote = LotePCP.objects.get(pk=lote_id)

# Validações do PCP (ex: check BOM, viabilidade)
metricas_validadas = {
    'total_pecas_pcp': lote.total_pecas,
    'tempo_producao_validado_horas': pcp_usuario.horas_corrigidas,
    'sequencia_fabricacao': [...],
    'data_inicio_producao': pcp_usuario.data_agendada
}

# Para CADA ambiente do pedido
pedido = Pedido.objects.get(numero_pedido=lote.pedido_numero)
for ambiente in pedido.ambientes.all():
    PedidoService.vincular_lote_pcp(
        ambiente=ambiente,
        lote_pcp=lote,
        metricas_pcp=metricas_validadas,
        usuario=pcp_usuario
    )

# Status muda
lote.status = 'ASSOCIADO_A_PEDIDO'
lote.save()
# → Pedido muda para EM_PRODUCAO (se todos ambientes prontos)
```

**Arquivos a editar**:
- [ ] `apps/pcp/models.py` - Adicionar status "AGUARDANDO_VALIDACAO_PCP"
- [ ] `apps/pcp/services.py` - `criar_lote_do_projeto()` + `validar_e_vincular_lote()`
- [ ] `apps/projetos/services.py` (ou onde existir) - Hook ao concluir projeto
- [ ] `apps/pcp/views.py` - Lista "Lotes Prontos" para PCP validar

#### 6. Integração com Bipagem (2-3 horas)
- [ ] Em `apps/bipagem/services.py` ao registrar bipagem, chamar `atualizar_dados_operacionais()`
- [ ] Passar status de peças bipadas e expedidas

---

## 🧹 Limpeza de Legacy Code - App PCP

**Por quê?** App PCP tem arquivos antigos que serão substituídos pela nova arquitetura Tarugo.

**O que remover**:

### Deletar (Substituído pela nova arquitetura)
```
apps/pcp/
├── models.py ........................... ❌ DELETAR (usar models/README.md)
├── services/ (se tiver código legado)
├── utils/ ............................. ❌ REVISAR/LIMPAR
└── exporters/ ......................... ❌ REVISAR (mover para mappers/)
```

### Revisar e Limpar
```
apps/pcp/
├── views.py ........................... ⚠️ REFATORAR - converter para nova API pattern
├── api/ ............................... ⚠️ VERIFICAR - manter apenas endpoints em uso
└── schemas/ ........................... ⚠️ CONSOLIDAR - remover schemas deprecated
```

### Áreas Específicas

#### 1. `apps/pcp/models.py` (DELETAR)
- **Causa**: Modelos precisam estar organizados em `models/` subdirectório
- **Ação**: 
  - Mover conteúdo de `models.py` para `models/__init__.py` ou `models/lote_pcp.py`
  - Deletar `models.py` raiz
  - Atualizar imports em todo projeto

#### 2. `apps/pcp/utils/` (REVISAR)
- **Causa**: Funções utilitárias podem estar duplicadas ou não-utilizadas
- **Ação**:
  - Auditar cada arquivo (grep por usage em codebase)
  - Deletar unused
  - Mover used → `services/` (mais apropriado) ou `helpers.py`

#### 3. `apps/pcp/exporters/` (REVISAR → MAPPERS)
- **Causa**: "Exporters" é responsabilidade de `mappers/`
- **Ação**:
  - Revisar content
  - Mover funcionalidades para `mappers/`
  - Deletar `exporters/` vazio

#### 4. `apps/pcp/views.py` (REFATORAR)
- **Causa**: Views antigas podem usar padrão antigo
- **Ação**:
  - Manter APENAS views HTML que são usadas
  - Converter endpoint lógica OLD → chamadas de `services/`
  - Documentar padrão esperado

#### 5. Schemas Deprecated (CONSOLIDAR)
- **Ação**: Remover schemas antigos do Pydantic que não estão em uso

**Script de Auditoria**:
```bash
# 1. Encontrar imports de models.py
grep -r "from apps.pcp.models import" --include="*.py" | wc -l

# 2. Encontrar imports de utils/
grep -r "from apps.pcp.utils import" --include="*.py" | wc -l

# 3. Encontrar imports de exporters/
grep -r "from apps.pcp.exporters import" --include="*.py" | wc -l
```

**Timeline**: ~2-3 horas (1 sprint)

---

## 🔌 Plano Detalhado: Dinabox Integration GO

**Objetivo**: Sincronizar dados de engenharia do Dinabox → Pedidos/Ambientes

### Fase 1: Recon & Spec (30 min - HOJE)
- [ ] Confirmar com Engenharia:
  - ✅ Qual endpoint Dinabox retorna dados de engenharia por projeto?
  - ✅ Qual é a estrutura JSON retornada? (exemplo)
  - ✅ Frequência de sincronização? (real-time, webhook, polling?)
  - ✅ Qual campo identifica "módulo/ambiente" em Dinabox?
  - ✅ Dados estão COMPLETOS ou precisa processar?

**Resposta esperada**: Documento com specs de API Dinabox + examples

### Fase 2: Mock Testing (1-2 horas)
- [ ] Criar `tests/fixtures/dinabox_project_response.json` com sample response
- [ ] Implementar função de parse em `DinaboxIntegrationService.parse_engenharia_dados()`
- [ ] Testes unitários para mapping projeto → ambientes

**Arquivo**: `apps/integracoes/dinabox/services.py`

```python
class DinaboxIntegrationService:
    @staticmethod
    def parse_engenharia_dados(raw_projeto_data: dict) -> dict:
        """
        Parse dados brutos Dinabox → estrutura esperada por Pedidos
        
        Retorna: {
            'modulos': [
                {
                    'id': 'MOD-001',
                    'nome': 'COZINHA SUPERIOR',
                    'dimensoes': '2750x1830',
                    'furacoes': [...],
                    'usinagens': [...]
                }
            ]
        }
        """
        # TODO: Implementar parsing conforme resposta Engenharia
        pass
```

### Fase 3: Webhook Setup (2-3 horas)
- [ ] Registrar endpoint webhook em Dinabox
- [ ] Implementar view em `apps/integracoes/dinabox/webhooks.py`:

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.integracoes.dinabox.services import DinaboxIntegrationService
from apps.pedidos.services import PedidoService

@require_POST
def webhook_projeto_concluido(request):
    """
    Dinabox notifica: "Projeto engenharia concluído"
    """
    data = json.loads(request.body)
    
    customer_id = data['customer_id']
    projeto_id = data['project_id']
    projeto_data = data['project_data']  # JSON completo
    
    try:
        # Parse dados
        eng_dados = DinaboxIntegrationService.parse_engenharia_dados(projeto_data)
        
        # Buscar pedido
        pedido = Pedido.objects.get(customer_id=customer_id)
        
        # Atualizar cada ambiente
        for modulo in eng_dados['modulos']:
            ambiente = pedido.ambientes.filter(
                nome_ambiente__icontains=modulo['nome'].lower()
            ).first()
            
            if ambiente:
                PedidoService.processar_engenharia_ambiente(
                    ambiente=ambiente,
                    dados_engenharia=modulo,
                    usuario=None  # Sistema
                )
                logger.info(f"✅ Ambiente {ambiente.nome_ambiente} atualizado")
            else:
                logger.warning(f"⚠️ Ambiente não encontrado: {modulo['nome']}")
        
        return JsonResponse({'success': True, 'pedido': pedido.numero_pedido})
    
    except Pedido.DoesNotExist:
        logger.error(f"❌ Pedido não encontrado para customer_id={customer_id}")
        return JsonResponse({'success': False, 'error': 'Pedido not found'}, status=404)
    
    except Exception as e:
        logger.error(f"❌ Erro processando webhook: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

**URLs**:
```python
# apps/integracoes/urls.py

urlpatterns = [
    # ...
    path('webhooks/dinabox/projeto-concluido/', 
         webhook_projeto_concluido, 
         name='webhook-projeto-concluido'),
]
```

### Fase 4: Test na Produção (1-2 horas)
- [ ] Testar com projeto REAL do Dinabox
- [ ] Verificar match de ambientes
- [ ] Validar dados em Pedido/AmbientePedido
- [ ] Verificar histórico de mudanças

**Checklist**:
```bash
# 1. Criar Pedido
curl -X POST /api/pedidos/ -d '{...}'
# → GET /api/pedidos/PED-001/  retorna ambientes PENDENTE

# 2. Simular webhook Dinabox
curl -X POST /webhooks/dinabox/projeto-concluido/ \
  -H "Content-Type: application/json" \
  -d @webhook_test.json

# 3. Verificar atualização
GET /api/pedidos/PED-001/  → ambientes agora AGUARDANDO_PCP
GET /api/pedidos/PED-001/historico-status/  → nova transição registrada

# 4. Validar dados de engenharia
GET /api/ambientes/1/  → campo dados_engenharia preenchido
```

### Fase 5: Error Handling & Monitoring (1-2 horas)
- [ ] Log de failures
- [ ] Retry policy se webhook falhar
- [ ] Alert se match de ambiente falhar
- [ ] Dashboard de sync status

```python
# Adicionar a views.py
@login_required
def dinabox_sync_status(request):
    """
    Dashboard mostrando status das últimas sincronizações
    """
    # Filtrar HistoricoStatusPedido com origem='DINABOX'
    # Mostrar sucesso/falhas
    # Timeline de eventos
    pass
```

### Timeline Estimado

| Fase | Horas | Est. Conclusão |
|------|-------|--|
| Recon & Spec | 0.5 | Hoje (30 min call) |
| Mock Testing | 1-2 | +1-2 horas |
| Webhook Setup | 2-3 | +2-3 horas |
| Test Produção | 1-2 | +1-2 horas |
| Error Handling | 1-2 | +1-2 horas |
| **TOTAL** | **6-10** | **~1 dia de work** |

### Dependências

- ✅ Pedidos app structure (DONE)
- ⚠️ **Engenharia confirma spec Dinabox** (BLOCADOR)
- ⚠️ **Dinabox aceita registrar webhook** (BLOCADOR)
- ✅ Integracoes app (DONE)

### Riscos

| Risco | Mitigação |
|-------|-----------|
| Spec Dinabox muda | Versionamento webhook |
| Match ambiente falha | Log detalhado + manual override |
| Webhook não chega | Retry + polling backup |
| Dados incompletos | Validação robusta + defaults |

---

## 📊 Matriz de Permissões - PEDIDO

| Operação | Comercial | Engenharia | PCP | Estoque | Bipagem |
|----------|-----------|-----------|-----|---------|---------|
| Criar | ✅ | - | - | - | - |
| Ler | ✅ | ✅ | ✅ | ✅ | ✅ |
| Atualizar own dados | ✅* | ✅ | ✅ | ✅ | ✅ |
| Atualizar status | ✅* | ✅ | ✅ | - | ✅ |
| Archivar | - | - | - | - | ✅ |

*Comercial: apenas correções dentro de 24h da criação

---

## 🎓 Fluxo Completo - Exemplo

```python
# 1. Comercial fecha venda
cliente = ClienteComercial.objects.get(pk=6)
numero_pedido = "PED-2026-001"  # Geração a definir
pedido = PedidoService.criar_pedido_do_comercial(
    cliente_comercial=cliente,
    numero_pedido=numero_pedido,
    usuario=request.user
)
# → Pedido #001: CONTRATO_FECHADO, ambientes: PENDENTE

# 2. Dinabox API popula engenharia
dados_eng = dinabox_api.get_projeto(customer_id)
for ambiente in pedido.ambientes.all():
    if matching_modulo := find_modulo(dados_eng, ambiente.nome):
        PedidoService.processar_engenharia_ambiente(
            ambiente=ambiente,
            dados_engenharia=matching_modulo
        )
# → Ambientes: AGUARDANDO_PCP
# → Pedido: EM_ENGENHARIA (se todos prontos)

# 3. PCP vincula lote
lote = LotePCP.objects.create(pedido_numero=pedido.numero_pedido, ...)
for ambiente in pedido.ambientes.all():
    PedidoService.vincular_lote_pcp(
        ambiente=ambiente,
        lote_pcp=lote,
        metricas_pcp={
            'total_pecas_pcp': 120,
            'tempo_producao_estimado_horas': 8.5
        }
    )
# → Ambientes: EM_INDUSTRIA
# → Pedido: EM_PRODUCAO

# 4. Bipagem atualiza progresso
for peca_bipada in bipar_leitura():
    ambiente = get_ambiente_by_peca(peca_bipada)
    dados_op = ambiente.dados_operacionais_resumo
    dados_op['pecas_bipadas'] = dados_op.get('pecas_bipadas', 0) + 1
    PedidoService.atualizar_dados_operacionais(
        ambiente=ambiente,
        dados_operacionais=dados_op
    )
# → Ambientes: CONCLUIDO (se 100% bipado)
# → Pedido: CONCLUIDO (se todos ambientes prontos)

# 5. Auditoria sempre disponível
historico = HistoricoStatusSelector.list_historico_pedido("PED-2026-001")
# → Histórico completo com usuário, data, motivo
```

---

## 📍 Roadmap Macro

### Sprint Atual (Pedidos Estrutura + Comercial Final)
- [x] **App Pedidos criado** — Models + Services + Selectors + Schemas + API + Admin + Templates
- [x] Estrutura 100% alinhada com tarugo-architecture
- [ ] **Migrações** — `makemigrations && migrate`
- [ ] Testes no Admin interface
- [ ] Integração Comercial → criar_pedido_do_comercial()
- [ ] **Limpeza PCP Legacy** — Auditar/deletar código antigo (~2-3h)
- [ ] **Dinabox Integration RECON** — Confirmar specs com Engenharia (30 min call)
- [ ] **GO for Dinabox** (fases 2-5, ~1 dia)

### Próx Sprint (Integrações Operacionais)
- [ ] **Dinabox → Pedidos**: `processar_engenharia_ambiente()` com **AsyncIO** (webhooks paralelos)
- [ ] **Projetos → PCP**: Auto-criar LotePCP + `criar_lote_do_projeto()` (~3h)
- [ ] **PCP → Pedidos**: `vincular_lote_pcp()` com validação (~2h)
- [ ] **Bipagem → Pedidos**: `atualizar_dados_operacionais()` (~2h)
- [ ] Webhooks/notificações entre apps (async tasks com Celery)
- [ ] Dashboard com status real-time

**DECISÃO ARQUITETURAL**: AsyncIO para integração Dinabox
- **Motivo**: Múltiplas tarefas concatenam em Pedido (Dinabox + PCP + Bipagem)
- **Benefício**: Evita gargalos mesmo com volume baixo, respostas rápidas
- **Implementation**: 4-6h refactor `DinaboxIntegrationService` → async/await

### Sprint +2 (Refinamentos)
- [ ] Geração automática de numero_pedido (format + seq) (~1h)
- [ ] Regras de validação de transição por role (~2h)
- [ ] Cache de queries frequentes (~2h)
- [ ] Testes unitários + integração (~3-4h)
- [ ] Export PDF/Excel (~3h)

### Sprint +3+ (Futuro)
- [ ] Sistema de notificações (websockets)
- [ ] Gráficos de produção por pedido
- [ ] Rastreamento de componentes (Estoque integration)
- [ ] SLA tracking + alertas
- [ ] Machine learning para previsões

---

## 🚨 Bloqueadores & Pontos de Clarificação

| Issue | Severidade | Owner | Ação | Timeline |
|-------|-----------|-------|------|----------|
| **Dinabox API Spec** | 🔴 CRÍTICO | Engenharia | Confirmar: endpoint, response format, webhook support | Hoje (30 min call) |
| **Dinabox Webhook Registration** | 🔴 CRÍTICO | Engenharia | Habilitar endpoint webhook em Dinabox | Após spec confirmada |
| **PCP: Status LotePCP** | ⚠️ IMPORTANTE | PCP | Confirmar novo status "AGUARDANDO_VALIDACAO_PCP" | Sprint atual |
| **Projetos: Conclusão logic** | ⚠️ IMPORTANTE | Projetos | Quando marcar projeto "CONCLUÍDO"? (é manual? % pronto?) | Sprint atual |
| Número Pedido Format | 🟡 MÉDIO | Comercial | Format: "PED-2026-001"? "P001"? Gerador sequencial? | Esta sprint |
| numero_pedido gerador | 🟡 MÉDIO | Comercial | Implementar `ComercialService.gerar_numero_pedido()` | Esta sprint |

---

## ✅ Tarefas de Hoje (Checklist Executivo)

```
□ Call 30min com Engenharia
  └─ Confirmar Dinabox API spec (endpoint + response)
  └─ Confirmar capability de webhook
  └─ Confirmar field que identifica "ambiente/módulo"
  
□ Call 15min com PCP
  └─ Confirmar novo status LotePCP: AGUARDANDO_VALIDACAO_PCP
  └─ Confirmar quando Projetos deve criar Lote automaticamente
  
□ Call 15min com Projetos
  └─ Confirmar definição de "projeto concluído"
  └─ Confirmar campo que correlaciona ambiente Tarugo ↔ módulo Dinabox

□ Documentar findings em PROXIMOS_PASSOS.md
```

Uma vez claro, **EST timeline for Dinabox GO**: ~1 dia

---

## 📋 Quick Start Pós-Implementação

```bash
# 1. Aplicar migrations
python manage.py makemigrations apps.pedidos
python manage.py migrate

# 2. Testar criação de Pedido (Django shell)
python manage.py shell

from apps.comercial.models import ClienteComercial
from apps.pedidos.services import PedidoService

cliente = ClienteComercial.objects.first()
pedido = PedidoService.criar_pedido_do_comercial(
    cliente_comercial=cliente,
    numero_pedido="PED-2026-TEST-001"
)
print(f"✅ Pedido {pedido.numero_pedido} criado com {pedido.total_ambientes} ambientes")

# 3. Acessar interface
# Admin: http://localhost:8000/admin/pedidos/
# Dashboard: http://localhost:8000/pedidos/
# API: http://localhost:8000/api/pedidos/
```

---

## 📚 Documentação

- [Detalhes completos: apps/pedidos/README.md](apps/pedidos/README.md)
- [Checklist implementação: apps/pedidos/IMPLEMENTACAO.md](apps/pedidos/IMPLEMENTACAO.md)
- [Arquitetura Tarugo: skills/tarugo-architecture.skill](skills/tarugo-architecture.skill)
- [Design Frontend: skills/tarugo-frontend-1-1.skill](skills/tarugo-frontend-1-1.skill)

---

## 📞 Contato / Dúvidas

**Implementação**: ✅ Estrutura completa pronta
**Integração com Comercial**: [Próxima tarefa — ~2-3 horas]
**Integração com Dinabox**: [Requer confirmação de API spec]
**Integração com PCP**: [Requer confirmação de LotePCP spec]

---

## 📝 RESUMO EXECUTIVO - Respostas às 3 Questões

### ❓ 1. Fluxo Projetos → PCP → Pedidos: `vincular_lote_pcp` é só trazer para tela?

**Resposta**: NÃO. Fluxo tem 2 etapas claras:

| Etapa | Ator | Ação | Função |
|-------|------|------|--------|
| **1. Auto-criação** | Projetos | Ao marcar projeto "CONCLUÍDO", cria `LotePCP` automaticamente | `ProjetosService.marcar_projeto_concluido()` + auto `LotePCP.create()` |
| **2. Validação PCP** | PCP | Recebe notificação, valida specs, ajusta horas/cronograma | PCP vai para "/pcp/lotes-aguardando-validacao/" |
| **3. Confirmação** | PCP | Confirma validação, chama `vincular_lote_pcp()` | Atualiza AmbientePedido com metricas_pcp, muda status → EM_INDUSTRIA |

**Implementação**:
- [ ] ETAPA 1: Adicionar hook em `ProjetosService.marcar_projeto_concluido()` → auto-create LotePCP
- [ ] ETAPA 2: View em PCP → lista "Lotes Prontos" (status=AGUARDANDO_VALIDACAO_PCP)
- [ ] ETAPA 3: View em PCP → "Confirmar Lote" → chama `PedidoService.vincular_lote_pcp()`

**Timeline**: ~3h (Etapa 1+2) + 2h (Etapa 3) = ~5-6 horas

---

### ❓ 2. Limpeza Legacy no App PCP — O que remover?

**Resposta**: 4 áreas-chave:

| Arquivo/Diretório | Ação | Motivo | Esforço |
|-------------------|------|--------|---------|
| `apps/pcp/models.py` | ❌ DELETAR | Migrar para `models/__init__.py` | 1h |
| `apps/pcp/utils/` | 🔍 REVISAR | Auditar uso, deletar unused, mover usado → services/ | 1.5h |
| `apps/pcp/exporters/` | 🔄 REFACTOR | Mover para `mappers/`, deletar dir | 1h |
| `apps/pcp/views.py` | ⚠️ REFACTOR | Limpar código antigo, manter só o necessário | 1.5h |

**Total**: ~5h (1 sprint curta)

**Script de Audit**:
```bash
grep -r "from apps.pcp.models import" --include="*.py"
grep -r "from apps.pcp.utils import" --include="*.py"
grep -r "from apps.pcp.exporters import" --include="*.py"
```

---

### ❓ 3. Plano para "GO for Dinabox integration"?

**Resposta**: 5 fases sequenciais, ~1 dia total

| # | Fase | Horas | Bloqueador? | Owner |
|---|------|-------|-----------|-------|
| **1** | **Recon & Spec** | 0.5 | 🔴 SIM | Engenharia |
| **2** | Mock Testing | 1-2 | - | Dev |
| **3** | Webhook Setup | 2-3 | 🔴 SIM (fase 1) | Dev |
| **4** | Test Produção | 1-2 | - | Dev |
| **5** | Error Handling | 1-2 | - | Dev |

**Phase 1 Recon Checklist** (30 min call com Engenharia):
- ✅ Endpoint Dinabox que retorna dados engenharia?
- ✅ Exemplo de response JSON?
- ✅ Frequency (real-time, webhook, polling)?
- ✅ Qual field identifica ambiente? (nome? ID padrão?)
- ✅ Dados COMPLETOS ou requer processing?

**Uma vez Fase 1 confirmada**: Dev pode fazer Fases 2-5 em paralelo → **GO em ~1 dia**

**Detalhes completos**: Veja seção ["Plano Detalhado: Dinabox Integration GO"](#plano-detalhado-dinabox-integration-go) acima

---

### 🎯 Action Items HOJE

1. **30 min call** com Engenharia → responder checklist Fase 1 Recon
2. **15 min call** com PCP → confirmar LotePCP status AGUARDANDO_VALIDACAO_PCP
3. **15 min call** com Projetos → confirmar auto-create LotePCP trigger
4. **Documentar** findings em PROXIMOS_PASSOS.md
5. **Kickoff** Limpeza PCP legacy (paralelo)

**ETA**: Dinabox GO em ~2-3 dias após confirmar specs

## MVP Confirmado - Pedido para Projetos

- O `numero_pedido` nasce no `ClienteComercial` e precisa existir mesmo quando o cliente nao virar `Pedido`.
- O handoff para Projetos cria `Pedido` reutilizando exatamente esse numero comercial.
- `Pedido.status` no envio inicial: `ENVIADO_PARA_PROJETOS`.
- `AmbientePedido.status` ao clonar do comercial: `PENDENTE_PROJETOS`.
- O retorno da Dinabox acontece por ambiente, em tempos diferentes, usando `customer_id` + `project_description`.
- Cada `response.json` parcial deve localizar o `Pedido` e o `AmbientePedido` corretos, preencher `dados_engenharia` e mover o ambiente para `AGUARDANDO_PCP`.
## Atualização 2026-04-14 - Ingestão Async Dinabox -> Pedido

- [x] `ClienteComercial.numero_pedido` passou a ser a fonte de verdade do número comercial, mesmo quando o cliente ainda não virou `Pedido`
- [x] Handoff Comercial -> Projetos cria `Pedido` com status `ENVIADO_PARA_PROJETOS`
- [x] `AmbientePedido` nasce com status `PENDENTE_PROJETOS`
- [x] Criado schema mínimo para retorno Dinabox por ambiente em `apps/integracoes/dinabox/schemas/pedido_receiver.py`
- [x] Criada fila persistida `DinaboxImportacaoProjeto` para tirar o peso da API Dinabox do caminho do PCP
- [x] Criado worker leve via management command: `python manage.py processar_importacoes_dinabox --limit 10 --concorrencia 2`
- [x] Importação integra `project_id` -> `Pedido/AmbientePedido` via `project_customer_id + project_description`
- [x] `dados_engenharia` agora preserva payload bruto + metadata + `woodwork` + `holes_summary`
- [x] Testes cobrindo enfileiramento, integração ao pedido e processamento async básico

### Decisão Atual

- O custo pesado da Dinabox deve acontecer na entrada, quando Projetos concluir o ambiente
- PCP e etapas seguintes devem consultar somente dados já persistidos no Tarugo
- `response.json` pequeno por ambiente continua sendo a estratégia preferida
- Async fica concentrado no fetch remoto; gravação ORM continua controlada e curta

### Próximo Passo Imediato

- [ ] Ligar `DinaboxImportacaoProjetoService.enfileirar_importacao(...)` ao evento real de "Projeto concluído"
- [x] Criar endpoint/view explícita para receber esse disparo do setor Projetos
- [x] Exibir fila/status de importação no admin ou em tela simples de acompanhamento
- [ ] Decidir se o worker vai rodar por agendamento, supervisord, cron ou loop dedicado

## Atualização 2026-04-16 - Observabilidade da fila Dinabox

- [x] Endpoint receptor para `Projeto concluído` exposto em `/integracoes/dinabox/importacoes/projeto-concluido/`
- [x] Autorização dupla no endpoint: usuário do grupo `PROJETOS` ou header `X-TARUGO-TRIGGER-TOKEN`
- [x] Tela de acompanhamento em `/integracoes/dinabox/importacoes/` com filtros por status e busca
- [x] `DinaboxImportacaoProjeto` registrado no Django admin para auditoria operacional
- [x] Testes cobrindo enfileiramento por token e listagem da fila
