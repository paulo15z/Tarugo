# Integração Dinabox — Visão Geral e Modelo de Dados

## Objetivo

Descrever a ideia, propósito e estrutura de dados para a integração com a API Dinabox.
Este documento orienta como buscar clientes, listar seus ambientes/projetos, extrair módulos/assemblies e enumerar peças (parts/woodwork), normalizando os campos essenciais para uso em toda a aplicação.

## Tarugo vs Dinabox — fonte de verdade

- **Acompanhamento de processo** (comercial, etapas, observações ricas, orçamentos por ambiente, status internos, histórico para Projetos/PCP/produção/expedição): **integralmente no Tarugo** (PostgreSQL, models + services).
- **API Dinabox**: usar de forma **pontual** para **entregar** e **trazer** dados que a indústria moveleira já trafega pelo ecossistema — em especial:
  1. **Clientes** — criar/atualizar cadastro essencial e manter referência `customer_id` estável.
  2. **Projetos** — listar/consultar detalhe de projeto (peças, módulos, metadados) para alimentar PCP, estoque, bipagem, etc.

Não delegar ao Dinabox o fluxo operacional nem o registo fino do negócio; a Dinabox é fronteira de dados de desenho/cadastro, não sistema de gestão do Tarugo.

## Fluxo recomendado

1. Autenticar conta técnica (token) e capturar/armazenar expiry.
2. Buscar cliente: `GET /api/clients/{client_id}` (ou equivalente Dinabox).
3. Listar projetos/ambientes do cliente: `GET /api/clients/{client_id}/projects`.
4. Para cada projeto: buscar detalhes do projeto `GET /api/projects/{project_id}`.
   - Preferir estrutura `modules` ou `woodwork` quando disponível.
5. Para cada módulo (se houver): extrair lista de peças; caso contrário, considerar o conjunto de peças do projeto como `SEM_MODULO`.

> Observação: a Dinabox pode retornar partes como JSON estruturado (recomendado) ou como arquivos (CSV/HTML). Implementar parser/fallback para CSV/HTML.

## Campos essenciais (canonical)

Normalizar cada peça com este conjunto mínimo (nomes canônicos):

- `reference` (string | opcional): referência/ID da peça
- `description` (string): descrição
- `material` (object | opcional): { `id`: string|int|null, `name`: string|null }
- `width` / `largura` (float | mm)
- `height` / `altura` (float | mm)
- `depth` / `profundidade` (float | mm) — quando aplicável
- `thickness` / `espessura` (float | mm) — quando relevante
- `quantity` / `quantidade` (int)
- `module` (string | null): identificador ou nome do módulo; `null` ou `"SEM_MODULO"` quando não existir
- `source_meta` (dict): traz `source`, `source_id`, `imported_at`, `version`
- `raw` (dict): payload original para auditoria

Use sempre tipos numéricos (float) para dimensões; coagir vírgula → ponto e validar com fallback (`None` quando inválido).

## Exemplos de Pydantic (sugestão)

```python
from pydantic import BaseModel
from typing import Optional, List, Dict

class Material(BaseModel):
    id: Optional[str]
    name: Optional[str]

class Part(BaseModel):
    reference: Optional[str]
    description: str
    material: Optional[Material]
    width: Optional[float]
    height: Optional[float]
    depth: Optional[float]
    thickness: Optional[float]
    quantity: int = 1
    module: Optional[str]
    source_meta: Dict = {}
    raw: Optional[Dict] = None

class Module(BaseModel):
    id: Optional[str]
    name: str
    parts: List[Part] = []

class Project(BaseModel):
    id: str
    name: Optional[str]
    client_id: Optional[str]
    modules: List[Module] = []
    parts: List[Part] = []
    metadata: Dict = {}
```

## Mapeamento (heurística) de chaves comuns

- dimensões: `largura|width|width_mm` → `width`; `altura|height|height_mm` → `height`; `profundidade|depth|depth_mm` → `depth`; `espessura|thickness` → `thickness`.
- material: `material|material_name|material_description` → `material.name`; `material_id|material_code` → `material.id`.
- quantidade: `quantidade|quantity|qty` → `quantity`.
- módulos: `modules|modulos|assemblies|groups|ambientes` → lista de `Module`.
- peças: `woodwork|parts|pieces|components|items|panels` → lista de `Part`.

Implementar o parser para percorrer alternativas e usar a primeira chave encontrada. Manter o `raw` para investigações futuras.

## Casos especiais e fallback

- Quando a API devolver apenas links (CSV/HTML):
  - Baixar o arquivo (respeitar autenticação/cookies), e rodar parser CSV ou HTML (BeautifulSoup). Reutilizar parsers existentes (`apps/integracoes/dinabox/parsers/*`).
- Quando não houver módulo: agrupar como `SEM_MODULO` ou deixar `module=null` conforme a necessidade da aplicação.
- Material desconhecido: gravar `material.name=null` e manter `raw`.

## Arquitetura e onde integrar no projeto

- Service layer: `DinaboxApiService` — responsável por chamadas HTTP, autenticação, paginação e cache de tokens.
- Parsers: `apps/integracoes/dinabox/parsers/` — transformar `detail` → `Project` normalizado (já existe `project_detail.py`).
- Schemas: `apps/integracoes/dinabox/schemas/` — Pydantic models para validação de entrada/saída.
- API pública: criar endpoints DRF (opcional) para expor dados normalizados para outras partes do sistema.
- Persistência/caching:
  - Cache em Redis para respostas transitórias (listagens);
  - Persistir importações importantes em models locais se precisar histórico/edição;
  - Manter `source_meta` com `version` e `imported_at` para detectar mudanças.

## Erros, retries e limites

- Tratar `DinaboxAuthError` (renovar token) e `DinaboxRequestError` (retry com backoff).
- Respeitar rate-limits, usar exponencial backoff e circuit-breaker para chamadas falhas repetidas.
- Registrar (log) payloads inválidos e armazenar o `raw` para suporte.

## Exemplo de saída (JSON normalizado)

```json
{
  "project": {"id": "0492827589", "name": "SUITE MASTER"},
  "client": {"id": "1101", "name": "MARCELO E KELLY"},
  "modules": [
    {"id": null, "name": "SEM_MODULO", "parts": [
      {"reference": null, "description": "tampo - mesa", "material": {"id": null, "name": "Branco TX"}, "width": 430.0, "height": 750.0, "depth": null, "thickness": 18.0, "quantity": 1}
    ]}
  ],
  "metadata": {"source": "dinabox", "imported_at": "2026-02-27T13:26:56", "version": 16396}
}
```

## Próximos passos (priorizados)

1. Implementar/ajustar Pydantic schemas em `apps/integracoes/dinabox/schemas/`.
2. Centralizar parsing em `apps/integracoes/dinabox/parsers/project_detail.py` (já criado) e expandir cobertura para CSV/HTML.
3. Criar endpoints DRF para expor dados normalizados (paginação, filtros por `client_id` e `project_id`).
4. Adicionar testes automatizados com payloads reais (mockados) e fixtures CSV/HTML.
5. Implantar cache (Redis) para listagens e metadados para reduzir chamadas à Dinabox.

---

Arquivo criado em `skills/dinabox-integration.md`.
