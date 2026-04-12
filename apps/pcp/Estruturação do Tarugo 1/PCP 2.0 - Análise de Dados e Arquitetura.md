# PCP 2.0 - Análise de Dados e Arquitetura

## 📊 Estrutura de Dados do Dinabox (response1.json)

### Níveis Hierárquicos

```
Project (project_id: "0310366465")
├── project_description: "COZINHA"
├── project_customer_id: "2539544"
├── project_customer_name: "1067 - THIAGO E GABY"
├── holes: [Ferragens globais do projeto]
│   └── {id, ref, name, qt, ...}
└── woodwork: [Módulos/Componentes]
    └── Module (id, mid, ref, type, qt, count)
        ├── name: "Prateleira duplada 02 - Cozinha"
        ├── material_name: "Carvalho Poro - ARAUCO"
        ├── width, height, thickness: [dimensões]
        ├── edge_left, edge_top, edge_bottom, edge_right: [Fitas de borda]
        ├── parts: [Peças individuais]
        │   └── Part (id, ref, type, name, width, height, thickness)
        │       ├── material_name: "Carvalho Poro - ARAUCO"
        │       ├── holes: {A, B, C, D, E, F} → [Operações de furação]
        │       └── edge_*: [Aplicações de borda]
        └── inputs: [Insumos/Hardware]
            └── {id, category_name, name, qt, factory_price, ...}
```

### Dados Operacionais Críticos

**Por Peça (Part):**
- Dimensões: `width`, `height`, `thickness`
- Material: `material_name`, `material_id`
- Bordas: `edge_left`, `edge_top`, `edge_bottom`, `edge_right` (com perimetro)
- Furação: `holes: {A, B, C, D, E, F}` (faces)
- Quantidade: `count` (do módulo)
- Notas: `note` (ex: "encaminhar p/ duplagem")

**Por Módulo (Module):**
- Tipo: `type` (ex: "thickened", "cabinet")
- Descrição: `name`
- Quantidade: `qt`, `count`
- Lista de `parts` (peças que compõem)
- Lista de `inputs` (hardware/insumos)

**Globais:**
- Ferragens: `holes` array (Minifix, Cavilha, etc.)
- Cliente: `project_customer_name`, `project_customer_id`
- Descrição: `project_description` (ex: "COZINHA")

---

## 🏗️ Estado Atual do PCP

### Modelos ORM Existentes

```
LotePCP
├── pid (ID único)
├── cliente_nome, cliente_id_projeto
├── status (pendente, em_producao, finalizado)
└── ambientes: [AmbientePCP]
    └── AmbientePCP
        ├── nome (ex: "COZINHA")
        └── modulos: [ModuloPCP]
            └── ModuloPCP
                ├── nome, codigo_modulo
                └── pecas: [PecaPCP]
                    └── PecaPCP
                        ├── referencia_bruta, codigo_peca
                        ├── descricao, material
                        ├── comprimento, largura, espessura
                        ├── roteiro, plano
                        ├── quantidade_planejada, quantidade_produzida
                        └── status
```

### Fluxo Atual (Legado)

1. Upload CSV/XLS → `ProcessamentoPCP`
2. Parse DataFrame (colunas: REFERENCIA, DESCRIÇÃO, MATERIAL, etc.)
3. Aplicar regras: `consolidar_ripas()`, `calcular_roteiro()`, `determinar_plano_de_corte()`
4. Gerar XLS de saída
5. Bipagem manual

### Problemas Identificados

❌ **Dependência de CSV/XLS** — Cada upload requer parse manual
❌ **Colunas Hardcoded** — Lógica presa a nomes específicos de coluna
❌ **Sem Tipagem** — DataFrame é dict-like, sem validação
❌ **Sem Furação Estruturada** — Furos em coluna de texto, não estruturados
❌ **Sem Bordas Estruturadas** — Bordas espalhadas em múltiplas colunas
❌ **Sem Usinagem** — Operações de usinagem não mapeadas
❌ **Exportação XLS** — Não há exportação XML para cut planning

---

## 🎯 PCP 2.0 - Visão Proposta

### Princípios

1. **API-First** — Dados vêm do Dinabox via schema Pydantic, não CSV
2. **Tipagem Forte** — `DinaboxProjectOperacional` valida entrada
3. **Sem Parsing** — Dados já estruturados chegam prontos
4. **Exportação XML** — Cut planning, furação, usinagem em XML
5. **Modelos Enriquecidos** — Roteiros, ripas, planos como domain objects

### Fluxo Novo

```
DinaboxProjectOperacional (schema Pydantic)
    ↓
PCPProcessingService.processar_projeto()
    ├── Gerar Roteiros (por peça)
    ├── Consolidar Ripas (por material/espessura)
    ├── Calcular Planos de Corte (por tipo de peça)
    ├── Mapear Furação (por face)
    └── Mapear Usinagem (por operação)
    ↓
LotePCP (ORM) + Roteiro, Ripa, PlanoCorte, Usinagem (Models)
    ↓
Exportadores
    ├── XML para Cut Planning
    ├── XML para Usinagem/Furação
    └── JSON para API/Dashboard
```

### Novos Modelos de Domínio

**Roteiro** (Manufacturing Route)
```
Roteiro
├── peca_id (FK PecaPCP)
├── sequencia: [Etapa]
│   └── Etapa (COR, DUP, BOR, USI, FUR, CQL, EXP, etc.)
├── tempo_estimado
└── observacoes
```

**Ripa** (Strip/Offcut)
```
Ripa
├── lote_id (FK LotePCP)
├── material_name
├── espessura
├── comprimento, largura
├── quantidade
├── origem (CORTE, FONTE)
├── destino (ESTOQUE, REUSO, DESCARTE)
└── status
```

**PlanoCorte** (Cutting Plan)
```
PlanoCorte
├── lote_id (FK LotePCP)
├── codigo_plano (ex: "03", "05", "06")
├── descricao
├── pecas: [PecaPCP]
├── total_pecas
├── tempo_estimado
└── prioridade
```

**Usinagem** (Machining Operation)
```
Usinagem
├── peca_id (FK PecaPCP)
├── tipo (FURO, RASGO, REBAIXO, etc.)
├── face (A, B, C, D, E, F)
├── quantidade
├── coordenadas: [Coord]
├── diametro (para furos)
└── profundidade
```

---

## 📋 Schemas Pydantic Necessários

### Entrada (do Dinabox)

Já existem:
- `DinaboxProjectOperacional` ✅
- `ModuleOperacional` ✅
- `PartOperacional` ✅
- `PartHoles` ✅
- `EdgeDetail` ✅

### Saída (para Exportação)

A criar:
- `RoteiroSchema` — Sequência de etapas
- `RipaSchema` — Descrição de ripa
- `PlanoCorteSchema` — Agrupamento de peças
- `UsinagemSchema` — Operações de furação/rasgo
- `XMLExportSchema` — Estrutura XML para cut planning

---

## 🔄 Services Necessários

### PCPProcessingService

```python
class PCPProcessingService:
    @staticmethod
    def processar_projeto(operacional: DinaboxProjectOperacional) -> LotePCP:
        """Processa projeto completo do Dinabox"""
        
    @staticmethod
    def gerar_roteiros(operacional: DinaboxProjectOperacional) -> List[Roteiro]:
        """Gera roteiros para cada peça"""
        
    @staticmethod
    def consolidar_ripas(operacional: DinaboxProjectOperacional) -> List[Ripa]:
        """Consolida ripas por material/espessura"""
        
    @staticmethod
    def calcular_planos_corte(operacional: DinaboxProjectOperacional) -> List[PlanoCorte]:
        """Calcula planos de corte por tipo de peça"""
        
    @staticmethod
    def mapear_usinagem(operacional: DinaboxProjectOperacional) -> List[Usinagem]:
        """Mapeia operações de furação/usinagem"""
```

### ExportService

```python
class ExportService:
    @staticmethod
    def exportar_xml_cut_planning(lote: LotePCP) -> str:
        """Exporta XML para cut planning"""
        
    @staticmethod
    def exportar_xml_usinagem(lote: LotePCP) -> str:
        """Exporta XML para usinagem/furação"""
        
    @staticmethod
    def exportar_json_operacional(lote: LotePCP) -> dict:
        """Exporta JSON para dashboard/API"""
```

---

## 🔌 API Endpoints PCP 2.0

```
POST   /api/pcp/projetos/processar/
       Body: DinaboxProjectOperacional
       Response: {lote_id, roteiros, ripas, planos, usinagem}

GET    /api/pcp/lotes/{lote_id}/roteiros/
       Response: [Roteiro]

GET    /api/pcp/lotes/{lote_id}/ripas/
       Response: [Ripa]

GET    /api/pcp/lotes/{lote_id}/planos-corte/
       Response: [PlanoCorte]

GET    /api/pcp/lotes/{lote_id}/usinagem/
       Response: [Usinagem]

GET    /api/pcp/lotes/{lote_id}/export/xml-cut-planning/
       Response: XML

GET    /api/pcp/lotes/{lote_id}/export/xml-usinagem/
       Response: XML

GET    /api/pcp/lotes/{lote_id}/export/json/
       Response: JSON
```

---

## 📦 Estrutura de Arquivos PCP 2.0

```
apps/pcp/
├── models/
│   ├── lote.py (LotePCP, AmbientePCP, ModuloPCP, PecaPCP) ✅ Existente
│   ├── roteiro.py (Roteiro, Etapa) 🆕
│   ├── ripa.py (Ripa) 🆕
│   ├── plano_corte.py (PlanoCorte) 🆕
│   └── usinagem.py (Usinagem) 🆕
├── schemas/
│   ├── operacional.py (Schemas de entrada) ✅ Existente
│   ├── roteiro.py (RoteiroSchema) 🆕
│   ├── ripa.py (RipaSchema) 🆕
│   ├── plano_corte.py (PlanoCorteSchema) 🆕
│   └── usinagem.py (UsinagemSchema) 🆕
├── services/
│   ├── lote_service.py (LotePCPService) ✅ Existente
│   ├── processing.py (PCPProcessingService) 🆕
│   ├── roteiro_service.py (RoteiroService) 🆕
│   ├── ripa_service.py (RipaService) 🆕
│   ├── plano_corte_service.py (PlanoCorteService) 🆕
│   ├── usinagem_service.py (UsinagemService) 🆕
│   └── export.py (ExportService) 🆕
├── domain/
│   ├── roteiros.py (Regras de roteiro) 🆕
│   ├── ripas.py (Regras de consolidação de ripas) 🆕
│   ├── planos.py (Regras de plano de corte) 🆕
│   └── usinagem.py (Regras de usinagem) 🆕
├── exporters/
│   ├── xml_cut_planning.py (XMLCutPlanningExporter) 🆕
│   ├── xml_usinagem.py (XMLUsinagemExporter) 🆕
│   └── json_exporter.py (JSONExporter) 🆕
├── selectors/
│   ├── lote_selector.py ✅ Existente
│   ├── roteiro_selector.py (RoteiroSelector) 🆕
│   ├── ripa_selector.py (RipaSelector) 🆕
│   ├── plano_corte_selector.py (PlanoCorteSelector) 🆕
│   └── usinagem_selector.py (UsinagemSelector) 🆕
├── api/
│   ├── views.py (Endpoints) 🔄 Atualizar
│   ├── serializers.py (Serializers) 🔄 Atualizar
│   └── urls.py (Rotas) 🔄 Atualizar
└── README.md (Documentação) 🆕
```

---

## ✅ Próximos Passos

1. **Fase 2:** Definir domain models (Roteiro, Ripa, PlanoCorte, Usinagem)
2. **Fase 3:** Criar schemas Pydantic para entrada/saída
3. **Fase 4:** Implementar services de processamento
4. **Fase 5:** Criar exportadores XML
5. **Fase 6:** Implementar API endpoints
6. **Fase 7:** Documentação e exemplos

---

**Data:** 11/04/2026  
**Versão:** PCP 2.0 - API-First, Zero CSV/XLS
