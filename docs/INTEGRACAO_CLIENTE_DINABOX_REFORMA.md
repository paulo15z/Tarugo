# Reforma do App Integrações - Padrão de Cliente Dinabox

## Objetivo
Reformular como o app integrações traz clientes da API Dinabox, seguindo o mesmo padrão robusto já estabelecido para projetos.

## Mudanças Realizadas

### 1. Schema Tipado para Cliente Detail (`schemas/api.py`)
- **Novo**: `DinaboxCustomerDetail` com campos específicos
- Aceita valores `null` para `customer_type`, `customer_status`, etc
- Mantém flexibilidade com `extra="allow"` para campos adicionais
- Tipagem robusta: `str | None`, `list[dict]`, etc
- **Defensivo**: `customer_id` e `customer_name` são opcionais no schema, validados depois

### 2. Parser Dedicado para Clientes (`parsers/customer_detail.py`)
- **Novo arquivo**: Processa dados brutos do Dinabox e normaliza
- Funções auxiliares:
  - `_normalize_emails()`: Extrai emails de várias formas (list, string separada, dict)
  - `_normalize_phones()`: Extrai telefones (mesmo padrão)
  - `_normalize_addresses()`: Filtra endereços (remove campos null)
- `parse_customer_detail()`: Função principal que:
  - Recebe dict/Pydantic cru
  - Aplica defaults para `customer_type="pf"`, `customer_status="on"`
  - Remove campos None/vazios
  - Retorna estrutura tipada e limpa

### 3. API Service com Extração Robusta (`dinabox/api_service.py`)
- **Antes**: `get_customer_detail() → dict` (genérico)
- **Depois**: `get_customer_detail() → DinaboxCustomerDetail` (tipado)

**Tratamento de Respostas**:
A API Dinabox pode retornar de várias formas:
1. Cliente isolado com paginação: `{'page': 1, 'total': 1, 'customer_id': '...', ...}`
2. Cliente em `customer`: `{'page': 1, 'total': 1, 'customer': {...}}`
3. Cliente em `customers` lista: `{'customers': [{...}], 'page': 1, 'total': 1}`

O `get_customer_detail()` agora:
- Extrai cliente de qualquer formato
- Remove campos de paginação
- Valida presence de `customer_id` e `customer_name`
- Retorna schema tipado

✅ **Bug Fix**: Corrige erro 
```
2 validation errors for DinaboxCustomerDetail
customer_id Field required
customer_name Field required
```
Causado por respostas com paginação misturada com dados do cliente.

### 4. Services com Parser (`services.py` - `DinaboxClienteService`)
- **Antes**: Normalização manual e propensa a erros
- **Depois**: Usa `parse_customer_detail()` automaticamente
- `refresh_from_remote()` agora:
  1. Busca na API (tipado)
  2. Processa com parser
  3. Sincroniza para índice com dados normalizados

### 5. Selector de Output (`selectors.py` - novo método)
- `get_cliente_para_comercial(customer_id)`: Retorna estrutura para consumo do comercial
- Formato:
  ```python
  {
      "customer_id": str,
      "customer_name": str,
      "customer_type": str,  # "pf" ou "pj"
      "customer_status": str,  # "on" ou "off"
      "customer_note": str,
      "emails": list[str],  # Normalizado
      "phones": list[str],  # Normalizado
      "addresses": list[dict],  # Filtrado
      "metadata": {...}
  }
  ```

## Fluxo Agora

```
Comercial App
    ↓
IntegrationSelector.get_cliente_para_comercial(customer_id)
    ↓
DinaboxClienteIndex (índice local, sincronizado)
    ↓
DinaboxApiService.get_customer_detail(customer_id)
    ↓
DinaboxAPIClient.get_customer(customer_id) [API raw]
    ↓
Extração + Limpeza de paginação
    ↓
parse_customer_detail() [normaliza, filtra, tipa]
    ↓
DinaboxCustomerDetail [validado Pydantic]
    ↓
Dados limpos para IntegrationSelector
    ↓
Comercial recebe estrutura tipada e pronta
```

## Benefícios

✅ **Tipagem End-to-End**: Schema → Parser → Service → Selector  
✅ **Robustez**: Trata null, vazio, múltiplos formatos, paginação  
✅ **Reutilização**: Parser pode ser usado em batch sync, webhooks, etc  
✅ **Rastreabilidade**: Parser preserva `raw_payload` completo  
✅ **Flexibilidade**: Adicionar novos normalizadores é trivial  
✅ **Padrão Consistente**: Mesma arquitetura de Projetos  
✅ **Bug Fixed**: Respostas com paginação agora tratadas corretamente  

## Exemplos Testados

### Exemplo 1: Cliente com null values (Wagner Lemos - 2539939)
```json
{
    "customer_id": "2539939",
    "customer_status": null,
    "customer_type": null,
    "customer_name": "1223 - WAGNER LEMOS",
    "customer_emails": [],
    "customer_phones": [],
    "customer_addresses": [{"address": null, ...}]
}
```
✅ Validado e normalizado com sucesso!

### Exemplo 2: Resposta com paginação (1721602)
```json
{
    "page": 1,
    "total": 1,
    "customer_id": "1721602",
    "customer_name": "CLIENTE",
    "customer_type": null,
    ...
}
```
✅ Extração de cliente e remoção de paginação bem-sucedida!

## Commits

- `ff76c61` - Reforma inicial: Schema, Parser, Selector tipados
- `34561e4` - Fix: Extrair cliente de resposta com paginação
