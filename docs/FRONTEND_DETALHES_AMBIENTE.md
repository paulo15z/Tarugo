# Frontend - Detalhes de Ambiente Comercial

## Visão Geral
Implementação completa da interface para gerenciar detalhes de ambientes no setor Comercial. Agora o usuário pode registrar acabamentos, eletrodomésticos e observações especiais para cada ambiente, com dados estruturados para handoff ao setor de Projetos.

## Fluxo de Uso

### 1. Acesso à Página de Detalhes
- Abra a ficha de um cliente em `/comercial/<client_id>/`
- Na seção "Ambientes e valores orçados", clique no botão **"Detalhes"** ao lado de cada ambiente
- Abrirá a página `/comercial/<client_id>/ambiente/<ambiente_id>/detalhes/`

### 2. Gerenciar Acabamentos
**Adicionar:**
- Digite o acabamento (ex: "Granito Preto", "Azulejo 20x20") no campo de entrada
- Clique "Adicionar"

**Remover:**
- Clique no botão "Remover" ao lado do acabamento desejado

### 3. Gerenciar Eletrodomésticos
**Adicionar:**
- Digite o eletrodoméstico (ex: "Fogão Consul 5 bocas", "Geladeira Brastemp") no campo de entrada
- Clique "Adicionar"

**Remover:**
- Clique no botão "Remover" ao lado do eletrodoméstico desejado

### 4. Editar Observações Especiais
- Preencha o textarea com itens que a Engenharia/Projetos deve considerar
- Exemplos: "Bicama na SUITE ANA", "Instalação de ar em janela específica"
- Clique "Salvar observações"

## Estrutura Técnica

### Models
```python
class AmbienteOrcamento(models.Model):
    # ... campos existentes ...
    acabamentos: JSONField  # Lista de strings
    eletrodomesticos: JSONField  # Lista de strings
    observacoes_especiais: TextField  # Texto livre
```

### URLs Disponíveis
```
/comercial/<pk>/ambiente/<ambiente_id>/detalhes/  # GET - Página de edição
/comercial/<pk>/ambiente/<ambiente_id>/acabamento/  # POST - Adicionar
/comercial/<pk>/ambiente/<ambiente_id>/acabamento/remover/  # POST - Remover
/comercial/<pk>/ambiente/<ambiente_id>/eletrodomestico/  # POST - Adicionar
/comercial/<pk>/ambiente/<ambiente_id>/eletrodomestico/remover/  # POST - Remover
/comercial/<pk>/ambiente/<ambiente_id>/observacoes/  # POST - Atualizar
```

### Views
- `ambiente_detalhes()` - Renderiza página de edição
- `ambiente_adicionar_acabamento_post()` - Adiciona acabamento
- `ambiente_remover_acabamento_post()` - Remove acabamento
- `ambiente_adicionar_eletrodomestico_post()` - Adiciona eletrodoméstico
- `ambiente_remover_eletrodomestico_post()` - Remove eletrodoméstico
- `ambiente_atualizar_observacoes_post()` - Atualiza observações

### Template
`apps/comercial/templates/comercial/ambiente_detalhes.html`
- Layout responsivo com 3 seções principais
- Listagem com botões de remover para cada item
- Formulários simples para adicionar
- Resumo visual para Projetos

## Integração com Projetos

Os dados capturados no Comercial podem ser acessados pelo selector:

```python
info = ComercialSelector.get_info_para_projetos(cliente_id)
# Retorna:
{
    "cliente_id": 1,
    "customer_id": "123456",
    "nome_cliente": "João Silva",
    "status": "Em orçamento",
    "ambientes": [
        {
            "nome": "Cozinha",
            "valor": "45000.00",
            "acabamentos": ["Granito Preto", "Azulejo 20x20"],
            "eletrodomesticos": ["Fogão Consul 5 bocas"],
            "observacoes": "Instalação de ar em canto específico"
        }
    ],
    # ... mais dados
}
```

## Permissões
- Requer permissão `comercial_editar_requerido` para todas as operações
- Automaticamente controlado pelas decorators existentes

## Validação
- Campos vazios são rejeitados com mensagem de aviso
- Duplicatas não são adicionadas à lista
- Todos os dados são sanitizados (strip, trim)

## Feedback ao Usuário
- Mensagens de sucesso em verde
- Mensagens de erro em vermelho
- Warnings em azul
- Confirmação antes de remover itens

## Próximas Etapas
1. Integração com Projetos para consumir dados
2. Adicionar validação de duplicatas mais robusta
3. Bulk edit para acabamentos/eletrodomésticos
4. Importação de template de ambientes padrão
5. Histórico de alterações por usuário
