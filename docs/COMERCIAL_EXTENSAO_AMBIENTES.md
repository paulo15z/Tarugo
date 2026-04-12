# Comercial - Extensão de Ambientes

## Objetivo

Permitir que o setor Comercial insira detalhes rápidos sobre os ambientes durante a negociação, para entregar uma especificação clara e bem estruturada ao setor de Projetos.

## Problema Original

Projetos precisa saber:
- ✅ Qual cliente
- ✅ Quantos ambientes
- ✅ Quais ambientes
- ❓ Quais eletros nos ambientes
- ❓ Quais acabamentos confirmados
- ❓ Itens especiais/observações importantes

**Risco**: Falha silenciosa de "não saber como fazer" gera prejuízo enorme na Engenharia.

## Solução Implementada

### 1. Estensão do Modelo `AmbienteOrcamento`

Novos campos:
```python
acabamentos: JSONField = []  # Lista de acabamentos
eletrodomesticos: JSONField = []  # Lista de eletrodomésticos
observacoes_especiais: TextField = ""  # Notas importantes
```

**Exemplo de dados**:
```json
{
  "nome_ambiente": "COZINHA",
  "valor_orcado": 5000.00,
  "acabamentos": [
    "Pintura branca fosca",
    "Piso porcelanato 60x60 cinza",
    "Rodapé MDF branco 15cm"
  ],
  "eletrodomesticos": [
    "Geladeira Brastemp 500L",
    "Fogão 5 bocas Consul branco",
    "Microondas Electrolux 30L"
  ],
  "observacoes_especiais": "Nicho aberto no fundo da cozinha - deixar 50cm de profundidade"
}
```

### 2. Schemas Pydantic

#### `AmbienteDetalhesInputSchema`
Entrada simplificada para adicionar/atualizar detalhes:
```python
{
  "acabamentos": ["Pintura", "Piso"],  # lista ou string separada por vírgula
  "eletrodomesticos": ["Geladeira"],  # lista ou string separada por vírgula
  "observacoes_especiais": "Nota importante"  # string livre
}
```

#### `AmbienteOrcamentoAtualizarSchema`
Atualização completa do ambiente (inclui nome, valor, detalhes):
```python
{
  "nome_ambiente": "COZINHA",  # opcional
  "valor_orcado": 5000,  # opcional
  "acabamentos": [...],  # opcional
  "eletrodomesticos": [...],  # opcional
  "observacoes_especiais": "..."  # opcional
}
```

### 3. Services - Operações CRUD

**Novos métodos em `ClienteComercialService`**:

```python
# Atualizar apenas os detalhes
atualizar_detalhes_ambiente(ambiente, schema: AmbienteDetalhesInputSchema)

# Atualizar ambiente completo (nome, valor, detalhes)
atualizar_ambiente_completo(ambiente, schema: AmbienteOrcamentoAtualizarSchema)

# Adicionar/remover item por item
adicionar_acabamento(ambiente, "Pintura branca")
remover_acabamento(ambiente, "Pintura branca")
adicionar_eletrodomestico(ambiente, "Geladeira")
remover_eletrodomestico(ambiente, "Geladeira")
```

### 4. Selector para Projetos

**Novo método: `ComercialSelector.get_info_para_projetos(cliente_id)`**

Retorna estrutura completa pronta para Projetos:

```json
{
  "cliente_id": 123,
  "customer_id": "2539939",
  "nome_cliente": "WAGNER LEMOS",
  "status": "Em orçamento",
  "total_ambientes": 3,
  "valor_total_orcado": 15000.00,
  "ambientes": [
    {
      "id": 456,
      "nome": "COZINHA",
      "valor": 5000.00,
      "acabamentos": [
        "Pintura branca fosca",
        "Piso porcelanato"
      ],
      "eletrodomesticos": [
        "Geladeira Brastemp 500L"
      ],
      "observacoes": "Nicho no fundo - 50cm de profundidade"
    },
    {
      "id": 457,
      "nome": "SUITE ANA",
      "valor": 7000.00,
      "acabamentos": ["Pintura azul claro"],
      "eletrodomesticos": [],
      "observacoes": "**BICAMA NA SUITE** - estrutura para duas camas"
    },
    {
      "id": 458,
      "nome": "SALA",
      "valor": 3000.00,
      "acabamentos": ["Pintura cinza"],
      "eletrodomesticos": [],
      "observacoes": ""
    }
  ],
  "observacoes_comerciais": [
    {
      "texto": "Cliente indeciso entre cores",
      "autor": "João Silva",
      "data": "2026-04-12T14:30:00"
    }
  ],
  "metadata": {
    "criado_em": "2026-04-10T10:00:00",
    "atualizado_em": "2026-04-12T14:30:00",
    "criado_por": "Pedro Santos"
  }
}
```

## Fluxo de Uso

### Comercial:

1. **Criar cliente** → Adicionar ambientes básicos (nome, valor)
2. **Durante a negociação**:
   - Atualizar `acabamentos` conforme conversas com cliente
   - Atualizar `eletrodomesticos` conforme gostos/necessidades
   - Adicionar `observacoes_especiais` para pontos críticos
3. **Antes de fechar contrato**: Revisar e confirmar todos os detalhes

### Projetos:

1. **Receber cliente** → Chamar `ComercialSelector.get_info_para_projetos(cliente_id)`
2. **Ter tudo estruturado**:
   - ✅ Cliente e contato
   - ✅ Ambientes e valores
   - ✅ Acabamentos confirmados
   - ✅ Eletrodomésticos a considerar
   - ✅ Observações importantes destacadas
3. **Iniciar projeto com confiança** → Menos surpresas, mais qualidade

## Exemplos de Observações Especiais

- "**BICAMA NA SUITE ANA** - estrutura para duas camas lado a lado"
- "Nicho aberto no fundo - deixar 50cm de profundidade"
- "Cliente requisitou painel TV na sala - estrutura com tijolos vazados"
- "Cozinha aberta, considerar acoustic na parede"
- "Piso térreo - umidade observada, usar impermeabilizante"

## Migration

**Arquivo**: `0002_ambiente_detalhes.py`

Adiciona 3 campos a `AmbienteOrcamento`:
- `acabamentos`: JSONField (default: list vazio)
- `eletrodomesticos`: JSONField (default: list vazio)
- `observacoes_especiais`: TextField (default: string vazia)

Execute com: `python manage.py migrate comercial`

## Benefícios

✅ **Comercial mais eficiente**: Input rápido e estruturado  
✅ **Projetos informado**: Toda informação necessária centralizada  
✅ **Menos surpresas**: Detalhes importantes em destaque  
✅ **Rastreabilidade**: Quem inseriu, quando, qual foi a mudança  
✅ **Flexibilidade**: Campos JSON permitem evolução sem nova migration  

## Próximos Passos (Propostos)

1. **APIs REST** para adicionar/remover itens individuais
2. **Templates HTML** para UI em comercial mostrando checkboxes para acabamentos pré-definidos
3. **Integração com Dinabox**: Enviar especificação para compartilhamento com cliente
4. **Histórico**: Rastrear mudanças nos ambientes (audit log)
5. **Presets**: Templates de acabamentos/eletros por tipo de ambiente (cozinha, banheiro, etc)
