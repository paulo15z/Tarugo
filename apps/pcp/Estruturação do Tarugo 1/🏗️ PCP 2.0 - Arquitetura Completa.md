# 🏗️ PCP 2.0 - Arquitetura Completa

**Versão:** 2.0 (API-First, Zero CSV/XLS)  
**Data:** 11/04/2026  
**Status:** Pronto para Implementação  

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Fluxo de Dados](#fluxo-de-dados)
3. [Modelos de Domínio](#modelos-de-domínio)
4. [Services e Lógica](#services-e-lógica)
5. [Exportação XML](#exportação-xml)
6. [API Endpoints](#api-endpoints)
7. [Exemplos de Uso](#exemplos-de-uso)
8. [Migração do PCP 1.0](#migração-do-pcp-10)

---

## 🎯 Visão Geral

O PCP 2.0 é um **orquestrador de dados operacionais** que:

- **Recebe** projetos estruturados do Dinabox (via `DinaboxProjectOperacional`)
- **Processa** automaticamente sem dependência de CSV/XLS
- **Gera** roteiros, ripas, planos de corte e operações de usinagem
- **Exporta** em XML para máquinas CNC (cut planning, furação, usinagem)
- **Oferece** API REST para integração com outros apps

### Princípios Arquiteturais

| Princípio | Implementação |
|-----------|--------------|
| **API-First** | Dados vêm do Dinabox via schema Pydantic |
| **Tipagem Forte** | Pydantic v2 valida entrada e saída |
| **Sem Parsing** | Dados já estruturados, sem processamento de texto |
| **Modular** | Cada domínio tem seu próprio ORM |
| **Rastreável** | Todas as operações registram status e timestamps |
| **Exportável** | XML para CNC, JSON para API |

---

## 🔄 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ENTRADA: DinaboxProjectOperacional                       │
│    (JSON validado com schema Pydantic)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. PROCESSAMENTO: PCPProcessingService.processar_projeto()  │
│                                                              │
│    ├── Criar LotePCP + Hierarquia                           │
│    │   └── Ambiente → Módulo → Peça                         │
│    │                                                         │
│    ├── Gerar Roteiros                                       │
│    │   └── Sequência automática de etapas                   │
│    │                                                         │
│    ├── Consolidar Ripas                                     │
│    │   └── Agrupa por material/espessura                    │
│    │                                                         │
│    ├── Calcular Planos de Corte                             │
│    │   └── Agrupa por tipo de peça                          │
│    │                                                         │
│    └── Mapear Usinagem                                      │
│        └── Extrai furação/rasgos com coordenadas            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ARMAZENAMENTO: ORM Models                                │
│                                                              │
│    ├── LotePCP (com hierarquia)                             │
│    ├── Roteiro (sequências)                                 │
│    ├── Ripa (tiras consolidadas)                            │
│    ├── PlanoCorte (agrupamentos)                            │
│    └── Usinagem (operações CNC)                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ XML Cut      │ │ XML Usinagem │ │ JSON API     │
│ Planning     │ │              │ │              │
│ (CNC)        │ │ (CNC)        │ │ (Dashboard)  │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 📊 Modelos de Domínio

### 1. Roteiro

**Responsabilidade:** Sequência de etapas de fabricação para cada peça.

```python
class Roteiro(BaseModel):
    peca: FK(PecaPCP)
    sequencia: List[str]  # ['COR', 'BOR', 'FUR', 'EXP']
    tempo_estimado_minutos: int
    observacoes: str
    ativo: bool
```

**Etapas Padrão:**
- `COR` — Corte
- `DUP` — Duplagem
- `BOR` — Aplicação de Borda
- `USI` — Usinagem
- `FUR` — Furação
- `CQL` — Colagem
- `EXP` — Expedição
- `MON` — Montagem
- `ACA` — Acabamento
- `CTL` — Controle de Qualidade

**Lógica de Geração:**
```
1. Sempre começa com CORTE
2. Se tem bordas → adiciona BORDA
3. Se tem furação → adiciona USINAGEM + FURACAO
4. Se é duplagem → adiciona DUPLAGEM após CORTE
5. Sempre termina com EXPEDICAO
```

### 2. Ripa

**Responsabilidade:** Tiras/retalhos gerados durante o corte.

```python
class Ripa(BaseModel):
    lote: FK(LotePCP)
    codigo_ripa: str  # Único
    material_name: str
    espessura_mm: Decimal
    comprimento_mm: Decimal
    largura_mm: Decimal
    quantidade: int
    origem: Choice(CORTE, FONTE)
    destino: Choice(ESTOQUE, REUSO, DESCARTE, PENDENTE)
    status: Choice(PLANEJADA, CORTADA, PROCESSADA, FINALIZADA)
```

**Propriedades Calculadas:**
- `area_m2` — Área em metros quadrados
- `volume_m3` — Volume em metros cúbicos

**Lógica de Consolidação:**
```
1. Agrupar peças por (material, espessura)
2. Calcular dimensões totais
3. Criar registro de Ripa para cada grupo
4. Marcar origem como CORTE
5. Destino pendente até decisão manual
```

### 3. PlanoCorte

**Responsabilidade:** Agrupamento de peças para otimização de corte.

```python
class PlanoCorte(BaseModel):
    lote: FK(LotePCP)
    codigo_plano: Choice(03, 05, 06, 10, 11, 12, 13, 14, 15, 99)
    numero_sequencial: int
    descricao: str
    pecas: M2M(PecaPCP)
    total_pecas: int
    tempo_estimado_minutos: int
    status: Choice(PLANEJADO, APROVADO, EM_CORTE, FINALIZADO, CANCELADO)
    prioridade: int (0-3)
```

**Códigos de Plano:**
| Código | Tipo | Descrição |
|--------|------|-----------|
| 03 | Chapa | MDF, Compensado |
| 05 | Perfil | Madeira Maciça |
| 06 | Porta | Portas |
| 10 | Gaveta | Gavetas |
| 11 | Tamponamento | Tamponamento |
| 12 | Frente | Frentes |
| 13 | Lateral | Laterais |
| 14 | Fundo | Fundos |
| 15 | Prateleira | Prateleiras |
| 99 | Outro | Outros |

**Lógica de Cálculo:**
```
1. Analisar descrição da peça
2. Se contém "porta" → código 06
3. Se contém "gaveta" → código 10
4. Se contém "prateleira" → código 15
5. Senão: Se área < 1m² → código 03 (Chapa)
6. Senão: código 05 (Perfil)
```

### 4. Usinagem

**Responsabilidade:** Operações de usinagem (furação, rasgos, etc.).

```python
class Usinagem(BaseModel):
    peca: FK(PecaPCP)
    tipo: Choice(FURO, RASGO, REBAIXO, ENCAIXE, CHANFRO, OUTRO)
    face: Choice(A, B, C, D, E, F)
    coordenada_x: Decimal  # mm
    coordenada_y: Decimal  # mm
    diametro_mm: Decimal (opcional)
    profundidade_mm: Decimal (opcional)
    largura_mm: Decimal (opcional)
    comprimento_mm: Decimal (opcional)
    quantidade: int
    status: Choice(PLANEJADA, PROGRAMADA, EXECUTADA, VERIFICADA, CANCELADA)
```

**Lógica de Mapeamento:**
```
1. Iterar sobre módulos e peças do Dinabox
2. Para cada peça, extrair dados de holes
3. Para cada furo, criar Usinagem com:
   - tipo = FURO
   - face = A-F (da estrutura Dinabox)
   - coordenadas = x, y do furo
   - diametro = d (diâmetro)
   - profundidade = depth
```

---

## 🔧 Services e Lógica

### PCPProcessingService

**Método Principal:**
```python
@staticmethod
def processar_projeto(
    operacional: DinaboxProjectOperacional,
    usuario_id: int = None
) -> Tuple[LotePCP, ProcessamentoPCPSchema]:
    """Processa projeto completo."""
```

**Fluxo Interno:**
1. `_criar_lote()` — Cria LotePCP + hierarquia
2. `_gerar_roteiros()` — Gera roteiros para cada peça
3. `_consolidar_ripas()` — Consolida ripas por material/espessura
4. `_calcular_planos_corte()` — Agrupa peças por tipo
5. `_mapear_usinagem()` — Extrai furação/rasgos

**Retorno:**
```python
(
    lote: LotePCP,  # Persistido no banco
    schema: ProcessamentoPCPSchema  # Para API
)
```

---

## 📤 Exportação XML

### XMLCutPlanningExporter

**Uso:**
```python
xml_str = XMLCutPlanningExporter.exportar(lote)
```

**Estrutura XML:**
```xml
<?xml version="1.0"?>
<cutting_plan version="1.0" generated="2026-04-11T10:30:00">
  <project>
    <id>L20260411ABC123</id>
    <customer>1067 - THIAGO E GABY</customer>
    <description>COZINHA</description>
    <date>2026-04-11T10:30:00</date>
    <status>pendente</status>
  </project>
  
  <plans>
    <plan id="03-001" type="Chapa (MDF, Compensado)" status="PLANEJADO">
      <description>Plano de Chapa (MDF, Compensado)</description>
      <total_pieces>5</total_pieces>
      <estimated_time>25</estimated_time>
      <priority>1</priority>
      
      <pieces>
        <piece id="P6246017" quantity="1">
          <description>Capa direita</description>
          <material>Carvalho Poro - ARAUCO</material>
          <dimensions>
            <width>260</width>
            <height>1779</height>
            <thickness>15</thickness>
            <unit>mm</unit>
          </dimensions>
          <edges>
            <edge>
              <position>left</position>
              <material>Carvalho Poro - ARAUCO</material>
              <width>35</width>
            </edge>
          </edges>
        </piece>
      </pieces>
    </plan>
  </plans>
  
  <statistics>
    <total_plans>3</total_plans>
    <total_pieces>15</total_pieces>
    <total_estimated_time>180</total_estimated_time>
    <average_time_per_piece>12</average_time_per_piece>
  </statistics>
</cutting_plan>
```

### XMLUsinagemExporter

**Uso:**
```python
xml_str = XMLUsinagemExporter.exportar(lote)
```

**Estrutura XML:**
```xml
<?xml version="1.0"?>
<machining_plan version="1.0" generated="2026-04-11T10:30:00">
  <project>
    <id>L20260411ABC123</id>
    <customer>1067 - THIAGO E GABY</customer>
    <description>COZINHA</description>
    <date>2026-04-11T10:30:00</date>
  </project>
  
  <operations>
    <piece id="P6246017" quantity="1">
      <description>Capa direita</description>
      <material>Carvalho Poro - ARAUCO</material>
      <dimensions>
        <width>260</width>
        <height>1779</height>
        <thickness>15</thickness>
        <unit>mm</unit>
      </dimensions>
      
      <faces>
        <face id="A" total_operations="2">
          <operation id="1" type="Furação" status="PLANEJADA">
            <coordinates>
              <x>125</x>
              <y>50</y>
              <unit>mm</unit>
            </coordinates>
            <parameters>
              <diameter>8</diameter>
              <depth>25</depth>
            </parameters>
          </operation>
          
          <operation id="2" type="Furação" status="PLANEJADA">
            <coordinates>
              <x>125</x>
              <y>100</y>
              <unit>mm</unit>
            </coordinates>
            <parameters>
              <diameter>8</diameter>
              <depth>25</depth>
            </parameters>
          </operation>
        </face>
      </faces>
    </piece>
  </operations>
  
  <statistics>
    <total_operations>12</total_operations>
    <total_pieces>5</total_pieces>
    <operations_by_type>
      <type name="Furação">10</type>
      <type name="Rasgo">2</type>
    </operations_by_type>
  </statistics>
</machining_plan>
```

---

## 🔌 API Endpoints

### 1. Processar Projeto

```
POST /api/pcp/projetos/processar/

Body:
{
  "operacional": DinaboxProjectOperacional (JSON)
}

Response (201):
{
  "lote_id": "L20260411ABC123",
  "cliente_nome": "1067 - THIAGO E GABY",
  "projeto_descricao": "COZINHA",
  "total_pecas": 15,
  "total_roteiros": 15,
  "total_ripas": 3,
  "total_planos": 4,
  "total_usinagens": 42,
  "tempo_total_estimado_minutos": 300,
  "roteiros": [...],
  "ripas": [...],
  "planos_corte": [...],
  "usinagens": [...]
}
```

### 2. Listar Roteiros

```
GET /api/pcp/lotes/{lote_id}/roteiros/

Response (200):
[
  {
    "peca_codigo": "P6246017",
    "sequencia": ["COR", "BOR", "FUR", "EXP"],
    "tempo_estimado_minutos": 45,
    "observacoes": "Encaminhar para duplagem"
  },
  ...
]
```

### 3. Listar Ripas

```
GET /api/pcp/lotes/{lote_id}/ripas/

Response (200):
[
  {
    "material_name": "Carvalho Poro - ARAUCO",
    "espessura_mm": 30,
    "comprimento_mm": 250,
    "largura_mm": 1769,
    "quantidade": 1,
    "origem": "CORTE",
    "destino": "PENDENTE",
    "area_m2": 0.4625
  },
  ...
]
```

### 4. Listar Planos de Corte

```
GET /api/pcp/lotes/{lote_id}/planos-corte/

Response (200):
[
  {
    "codigo_plano": "03",
    "numero_sequencial": 1,
    "descricao": "Plano de Chapa (MDF, Compensado)",
    "peca_codigos": ["P6246017", "P6246016"],
    "total_pecas": 2,
    "tempo_estimado_minutos": 30,
    "prioridade": 1
  },
  ...
]
```

### 5. Listar Usinagem

```
GET /api/pcp/lotes/{lote_id}/usinagem/

Response (200):
[
  {
    "peca_codigo": "P6246017",
    "tipo": "FURO",
    "face": "A",
    "coordenada_x": 125,
    "coordenada_y": 50,
    "diametro_mm": 8,
    "profundidade_mm": 25,
    "quantidade": 1
  },
  ...
]
```

### 6. Exportar XML Cut Planning

```
GET /api/pcp/lotes/{lote_id}/export/xml-cut-planning/

Response (200):
Content-Type: application/xml

<?xml version="1.0"?>
<cutting_plan>
  ...
</cutting_plan>
```

### 7. Exportar XML Usinagem

```
GET /api/pcp/lotes/{lote_id}/export/xml-usinagem/

Response (200):
Content-Type: application/xml

<?xml version="1.0"?>
<machining_plan>
  ...
</machining_plan>
```

---

## 💡 Exemplos de Uso

### Exemplo 1: Processar Projeto Completo

```python
from apps.integracoes.services import DinaboxIntegrationService
from apps.pcp.services.processing import PCPProcessingService

# 1. Obter dados do Dinabox
operacional = DinaboxIntegrationService.get_operacional_view(raw_data)

# 2. Processar no PCP
lote, schema = PCPProcessingService.processar_projeto(operacional, usuario_id=1)

# 3. Exportar XML
from apps.pcp.exporters.xml_cut_planning import XMLCutPlanningExporter
from apps.pcp.exporters.xml_usinagem import XMLUsinagemExporter

xml_cut = XMLCutPlanningExporter.exportar(lote)
xml_usinagem = XMLUsinagemExporter.exportar(lote)

# 4. Salvar ou enviar para máquinas
with open(f"cut_planning_{lote.pid}.xml", "w") as f:
    f.write(xml_cut)
```

### Exemplo 2: Consultar Roteiros

```python
from apps.pcp.models.roteiro import Roteiro
from apps.pcp.models.lote import LotePCP

lote = LotePCP.objects.get(pid="L20260411ABC123")

for roteiro in lote.pecas_all().prefetch_related('roteiro'):
    print(f"{roteiro.codigo_peca}: {roteiro.roteiro.etapas_descricao}")
    print(f"  Tempo: {roteiro.roteiro.tempo_estimado_minutos} min")
```

### Exemplo 3: Listar Planos de Corte por Tipo

```python
from apps.pcp.models.plano_corte import PlanoCorte, TipoPlanoCorte

lote = LotePCP.objects.get(pid="L20260411ABC123")

for tipo_code, tipo_nome in TipoPlanoCorte.choices:
    planos = PlanoCorte.objects.filter(lote=lote, codigo_plano=tipo_code)
    print(f"\n{tipo_nome}:")
    for plano in planos:
        print(f"  {plano.codigo_completo}: {plano.total_pecas} peças")
```

---

## 🔄 Migração do PCP 1.0

### O que Muda

| Aspecto | PCP 1.0 | PCP 2.0 |
|--------|---------|---------|
| **Entrada** | CSV/XLS upload | DinaboxProjectOperacional (API) |
| **Parsing** | DataFrame com colunas | Schema Pydantic validado |
| **Roteiros** | Calculados por heurísticas de texto | Sequência automática tipada |
| **Ripas** | Consolidação em DataFrame | ORM model com rastreamento |
| **Planos** | Colunas de planilha | Agrupamento por tipo com ORM |
| **Usinagem** | Não mapeada | Completa com coordenadas |
| **Exportação** | XLS | XML + JSON |

### Compatibilidade

- **Modelos Existentes:** LotePCP, AmbientePCP, ModuloPCP, PecaPCP continuam iguais
- **Novos Modelos:** Roteiro, Ripa, PlanoCorte, Usinagem
- **API Legada:** Endpoints antigos continuam funcionando (leitura)
- **Migração Gradual:** Pode coexistir com PCP 1.0 durante transição

---

## 📚 Estrutura de Arquivos

```
apps/pcp/
├── models/
│   ├── lote.py ✅ (Existente)
│   ├── roteiro.py 🆕
│   ├── ripa.py 🆕
│   ├── plano_corte.py 🆕
│   └── usinagem.py 🆕
├── schemas/
│   ├── operacional.py ✅ (Existente)
│   └── processamento.py 🆕
├── services/
│   ├── lote_service.py ✅ (Existente)
│   └── processing.py 🆕
├── exporters/
│   ├── xml_cut_planning.py 🆕
│   └── xml_usinagem.py 🆕
├── selectors/
│   ├── lote_selector.py ✅ (Existente)
│   ├── roteiro_selector.py 🆕
│   ├── ripa_selector.py 🆕
│   ├── plano_corte_selector.py 🆕
│   └── usinagem_selector.py 🆕
├── api/
│   ├── views.py 🔄 (Atualizar)
│   ├── serializers.py 🔄 (Atualizar)
│   └── urls.py 🔄 (Atualizar)
└── README.md 🆕
```

---

## ✅ Checklist de Implementação

- [x] Fase 1: Análise de dados
- [x] Fase 2: Domain models
- [x] Fase 3: Schemas Pydantic
- [x] Fase 4: Services de processamento
- [x] Fase 5: Exportadores XML
- [ ] Fase 6: API endpoints
- [ ] Fase 7: Documentação
- [ ] Fase 8: Testes e validação

---

**Próximos Passos:**
1. Implementar API endpoints (Fase 6)
2. Criar selectors para queries (Fase 6)
3. Escrever testes unitários
4. Validar com dados reais do Dinabox
5. Documentar migrações do PCP 1.0

---

**Autor:** Manus AI  
**Última Atualização:** 11/04/2026  
**Versão:** 1.0
