
```markdown
---
name: tarugo-architecture-guide
description: Guia operacional completo da arquitetura do Tarugo. Define princípios, padrões, fluxo de desenvolvimento e visão de evolução do projeto. Todo desenvolvedor que entrar em contato com o código deve ler este documento primeiro.
license: MIT
---

# 🏗️ Arquitetura do Tarugo

**Guia Operacional e de Arquitetura**  
Plataforma modular para indústrias moveleiras desenvolvida em Django.

---

## 📌 Visão Geral

O **Tarugo** é um sistema desenvolvido em **Django** com arquitetura modular baseada em apps Django.

**Objetivo principal**:
- Resolver problemas reais da indústria moveleira (estoque, PCP, bipagem/produção, integrações)
- Automatizar processos com foco em simplicidade e escalabilidade futura (SaaS)

**Filosofia do projeto**:
- Simplicidade acima de tudo (evitar overengineering)
- Código reutilizável, testável e de fácil manutenção
- Separação clara de responsabilidades
- Evolução contínua pensando em SaaS (multi-tenant, integrações, escalabilidade)

---

## 🧱 Princípios Arquiteturais (Obrigatórios)

O Tarugo segue rigorosamente a seguinte separação de responsabilidades:

| Camada          | Responsabilidade                          | Localização              | Regra de Ouro |
|-----------------|-------------------------------------------|--------------------------|---------------|
| **Models**      | Estrutura de dados e ORM                  | `models/`                | Apenas campos, relações, properties e signals |
| **Services**    | **Regras de negócio** (coração do sistema)| `services/`              | **NUNCA** colocar lógica de negócio em views ou api |
| **Selectors**   | Consultas complexas/reutilizáveis ao banco| `selectors/`             | Centralizar queries |
| **Schemas**     | Validação de negócio com Pydantic         | `schemas/`               | Validação dupla (DRF + Pydantic) |
| **API**         | Camada HTTP (Django Rest Framework)       | `api/`                   | Apenas serialização, validação DRF e chamada ao Service |
| **Mappers**     | Conversão entre models ↔ schemas/output   | `mappers/`               | Manter models limpos |
| **Domain**      | Tipos, enums e lógica de domínio pura     | `domain/`                | Regras independentes de framework |

**Fluxo padrão de toda requisição**:

Request → DRF Serializer → Service (com Pydantic) → Selector / Model → Banco → Response
```

**Validação dupla obrigatória**:
1. DRF Serializers (validação HTTP)
2. Pydantic Schemas (validação de regras de negócio dentro do Service)

---

## 📦 Módulos Atuais (Apps Django)

| App              | Responsabilidade                                      | Status          | Destaques Principais |
|------------------|-------------------------------------------------------|-----------------|----------------------|
| `core`           | Autenticação, usuários, permissões                    | ✅ Base         | - |
| `estoque`        | Cadastro de produtos, movimentações, reservas         | ✅ MVP maduro   | Services + Pydantic + Selectors + Categorias hierárquicas |
| `pcp`            | Processamento de roteiros Dinabox, cálculo de roteiro e plano de corte | ✅ Em produção | `processamento_service.py`, consolidação de ripas, integração com bipagem |
| `bipagem`        | Controle operacional de produção (scanner de peças)   | ✅ Em produção  | Modelos hierárquicos (Pedido → OrdemProducao → Modulo → Peca), bipagem com histórico, progresso por lote/módulo |
| `integracoes`    | Integrações com sistemas externos (Dinabox, etc.)     | ✅ Em evolução  | Estrutura com `dinabox/` (parsers, schemas Pydantic, classificador) |

---

## 🔍 Detalhes dos Módulos Principais

### **estoque**
- Segue o padrão Tarugo de forma mais completa
- `services/`, `schemas/`, `selectors/`, `domain/`, `mappers/`
- Categorias hierárquicas
- Movimentações com transações atômicas e lock de concorrência

### **pcp**
- Atualmente o módulo mais utilizado em produção
- `pcp_service.py` (legado) está sendo migrado para `processamento_service.py` + `schemas`
- Integração direta com `bipagem` via `importar_de_pcp()`
- Gera roteiros com ROTEIRO + PLANO + consolidação inteligente de ripas

### **bipagem**
- Modelo hierárquico forte: Pedido → Ordem de Produção → Módulo → Peça
- Bipagem idempotente com histórico imutável (`EventoBipagem`)
- Progresso calculado via properties e selectors
- Integração com PCP (importação de roteiros processados)

### **integracoes**
- Foco atual em importação Dinabox (CSV de corte + HTML de compras)
- Schemas Pydantic bem definidos (`ProjetoCompleto`, `Insumo`, `Peca`, etc.)
- Preparado para crescer com outros sistemas (Bling, Tiny, etc.)

---

## ⚙️ Stack Técnica Atual

- **Backend**: Django + Django Rest Framework
- **Validação**: DRF Serializers + **Pydantic** (regras de negócio)
- **Banco**: SQLite (desenvolvimento) → PostgreSQL (produção planejada)
- **Processamento de arquivos**: pandas + xlwt
- **Tarefas assíncronas**: Celery (planejado)
- **Frontend**: Templates Django + API REST (preparado para SPA futura)

---

## 🎯 Como Desenvolver no Tarugo (Passo a Passo)

1. **Nunca** coloque regra de negócio em `views.py`, `api/views.py` ou serializers
2. Crie **Service** em `services/` (use Pydantic para Input/Output quando possível)
3. Crie **Selector** se a consulta for complexa ou reutilizável
4. Use **Mappers** quando precisar transformar Model ↔ Schema
5. No `api/` use DRF Serializer → chama o Service
6. Escreva testes para Services e Selectors (prioridade alta)

**Estrutura recomendada dentro de um app**:
```
apps/estoque/
├── models/
├── domain/
├── schemas/
├── services/
├── selectors/
├── mappers/
├── api/
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── utils/          # (para pcp: parsers, ripas, etc.)
└── tests/
```

---

## 🚀 Visão de Evolução (Roadmap Técnico)

**Fase atual (MVP em produção parcial)**:
- Estoque completo
- PCP + geração de roteiros
- Bipagem operacional com scanner
- Importação básica Dinabox

**Próximas prioridades**:
1. Unificar/refatorar PCP para seguir 100% o padrão Service + Pydantic
2. Multi-tenant / suporte a múltiplas empresas (SaaS readiness)
3. Celery para tarefas pesadas (processamento de arquivos grandes)
4. PostgreSQL + migrações robustas
5. Sistema de permissões por grupo/empresa mais granular
6. Dashboard analítico unificado
7. API pública + integrações externas maduras

---

## 📌 Como Usar Este Guia

**Ao revisar código/PRs**:
- Verifique se lógica de negócio está no Service
- Verifique uso de Pydantic onde faz sentido
- Verifique separação clara de responsabilidades

**Anti-padrões proibidos**:
- Lógica de negócio em views ou api/views
- Consultas complexas diretamente em models/views
- Duplicação de regras entre módulos

---

**Última atualização**: 03 de abril de 2026  
**Versão**: 1.1 (Alinhada com apps estoque, pcp, bipagem e integracoes)

---

---
