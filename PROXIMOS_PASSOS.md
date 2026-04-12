# 🎯 Próximas Etapas - Tarugo Roadmap

**Status**: Comercial em fase final | Projetos iniciando  
**Data**: 12/04/2026  
**Última atualização**: Pós-implementação de Ambiente Detalhes

---

## 🔧 Correções Imediatas (Comercial)

### ✅ RESOLVIDO
- [x] Erro `NoReverseMatch: 'ambiente_excluir_post'` — URL adicionada em `apps/comercial/urls.py`
- [x] Migration conflict — Typo em modelo fixado, migrations regeneradas
- [x] Frontend ambiente_detalhes — Template completo com CRUD

### ⚠️ Pendentes (Triviais)
- [ ] Validação de duplicatas robusta em acabamentos/eletrodomésticos
  - **Onde**: `apps/comercial/services/cliente_service.py`
  - **O quê**: Verificar duplicata antes de adicionar (case-insensitive + trim)
  - **Esforço**: ~10 min
  
- [ ] Histórico de alterações por usuário (opcional para MVP)
  - **Onde**: Add timestamp + user_id em cada mudança de detalhe
  - **Esforço**: 30 min (pode ficar para v2)

- [ ] Template padrão de ambientes comuns
  - **Exemplo**: "Cozinha", "Sala", "Quarto", "Banheiro" com eletros pré-preenchidos
  - **Esforço**: 20 min (v2)

---

## ✨ Checklist Final - Comercial (MVP)

- [x] Criar cliente (Dinabox + Tarugo)
- [x] Sincronizar cliente existente
- [x] Editar status pipeline (primeiro contato → contrato fechado)
- [x] Adicionar observações gerais
- [x] Registrar ambientes (nome + valor)
- [x] **Detalhar ambientes** (acabamentos + eletros + obs especiais)
- [x] Enviar para Projetos via selector estruturado
- [ ] **Testar fluxo completo end-to-end**

### Action: Teste Rápido Antes de Partir
```bash
# 1. Abra cliente em /comercial/6/
# 2. Adicione um ambiente (nome + valor)
# 3. Clique "Detalhes"
# 4. Adicione: 1 acabamento, 1 eletro, 1 observação
# 5. Volte e confirme dados persistiram
# 6. Valide estrutura em: ComercialSelector.get_info_para_projetos(6)
```

---

## 🎁 Arquitetura PEDIDO (Projetos)

### O que é PEDIDO?

**PEDIDO** é a **entidade central** que nascerá do fechamento do contrato no Comercial e evoluirá conforme passa pelos setores (Projetos → PCP → Estoque → Bipagem).

```
COMERCIAL            PROJETOS         PCP              ESTOQUE           BIPAGEM
   |                    |              |                  |                 |
Contrato Fechado → CRIA PEDIDO ← Recebe + Detalha → Fabrica + Prepara → Monta + Entrega
   |                    |              |                  |                 |
Detalhes Cliente       Layout         Orçamento         Estoque         Instalação
Ambientes             Furação        Cronograma       Componentes       Final Check
Acabamentos           Cortes         Controle         Logística         Assinatura
Eletros               Dobragem         MOs           Rastreamento
Obs Especiais       Acabamentos
                    Orçamento
```

### Por quê centralizar em PEDIDO?

**Problema anterior**: Cada setor tinha seu próprio modelo
- Redundância de dados
- Inconsistência
- Difícil rastreamento

**Solução**: Um único PEDIDO que cresce em contexto
- Comercial preenchePrimeira camada
- Projetos adiciona layout + furação
- PCP adiciona cronograma + materiais
- Estoque marca componentes como prontos
- Bipagem finaliza com instalação

---

## 📋 Estrutura do PEDIDO (v1)

### Núcleo (Imutável - criado em Comercial)
```python
class Pedido(models.Model):
    # Rastreamento
    numero_pedido = AutoField(primary_key=True)  # 001, 002, ...
    data_criacao = DateTimeField(auto_now_add=True)
    
    # Cliente (snapshot do momento)
    cliente_comercial = ForeignKey(ClienteComercial)
    customer_id_dinabox = CharField()  # Backup
    nome_cliente = CharField()
    cpf_cnpj = CharField()
    email_principal = EmailField()
    telefone_principal = CharField()
    
    # Endereço de Entrega
    endereco_logradouro = CharField()
    endereco_numero = CharField()
    endereco_complemento = CharField()
    endereco_cidade = CharField()
    endereco_estado = CharField()
    endereco_cep = CharField()
    
    # Comercial
    status_pedido = CharField(choices=[
        ('pedido_criado', 'Iniciado'),
        ('projetando', 'Em Projetos'),
        ('pcp_validando', 'PCP Validando'),
        ('fabricando', 'Fabricando'),
        ('estoque_preparando', 'Estoque Preparando'),
        ('em_entrega', 'Em Entrega'),
        ('finalizado', 'Finalizado'),
    ])
    data_prazo_entrega = DateField()
    valor_total = DecimalField(max_digits=14, decimal_places=2)
    
    # Timestamps
    criado_em = DateTimeField(auto_now_add=True)
    atualizado_em = DateTimeField(auto_now=True)
    atualizado_por = ForeignKey(User, null=True, blank=True)
```

### Módulos por Setor

#### Projetos (PedidoProjetos)
```python
class PedidoProjetos(models.Model):
    pedido = OneToOneField(Pedido, on_delete=CASCADE)
    
    # Por ambiente
    ambientes = JSONField()  # [{
    #   "id": "cozinha",
    #   "nome": "Cozinha",
    #   "acabamentos_confirmados": [...],
    #   "eletros_confirmados": [...],
    #   "plantas": [url1, url2],
    #   "furacao": {...},
    #   "cortes": {...},
    #   "dobragens": {...},
    #   "valor_projeto": 5000,
    #   "status": "aprovado"
    # }]
    
    arquivos_plantas = FileField(multiple=True)
    observacoes_tecnicas = TextField()
    responsavel_projeto = ForeignKey(User)
```

#### PCP (PedidoPCP)
```python
class PedidoPCP(models.Model):
    pedido = OneToOneField(Pedido)
    
    cronograma = JSONField()  # Datas críticas
    materiais_necessarios = JSONField()  # BOM
    sequencia_fabricacao = JSONField()
    controle_qualidade = JSONField()
    mao_de_obra_estimada = IntegerField()  # horas
    responsavel_pcp = ForeignKey(User)
```

#### Estoque (PedidoEstoque)
```python
class PedidoEstoque(models.Model):
    pedido = OneToOneField(Pedido)
    
    componentes = JSONField()  # {
    #   "sku": "MDF-18MM-IMBUIA",
    #   "quantidade": 10,
    #   "unidade": "unidade",
    #   "status": "em_estoque|separado|expedido"
    # }
    
    local_armazenagem = CharField()
    data_separacao = DateField(null=True)
    data_expedicao = DateField(null=True)
```

#### Bipagem (PedidoBipagem)
```python
class PedidoBipagem(models.Model):
    pedido = OneToOneField(Pedido)
    
    local_instalacao = CharField()
    data_agendamento = DateField()
    equipe_instalacao = JSONField()  # [{name, phone, skills}]
    status_instalacao = CharField(choices=[
        'agendado', 'em_instalacao', 'concluido', 'com_problema'
    ])
    obs_instalacao = TextField()
    assinatura_cliente = FileField(null=True)
    fotos_antes = FileField(multiple=True)
    fotos_depois = FileField(multiple=True)
```

---

## 🔄 Fluxo de Dados - PEDIDO

```
1. COMERCIAL (Fecha venda)
   └─ Cria PEDIDO com núcleo + ambientes détail
   └─ Status: pedido_criado
   └─ Envia para: ComercialSelector.get_info_para_projetos()
   
2. PROJETOS (Recebe + Detalha layout)
   └─ PopulaRequests PedidoProjetos
   └─ Adiciona plantas, furação, cortes, dobragens
   └─ Valida com Comercial se mudança é necessária
   └─ Status: projetando → aprovado
   └─ Envia para: ProjetosSelector.get_info_para_pcp()
   
3. PCP (Fabrica + Cronograma)
   └─ Popula PedidoPCP
   └─ Create BOM (Bill of Materials)
   └─ Define datas críticas
   └─ Aloca equipe
   └─ Status: pcp_validando → fabricando
   └─ Envia para: PCPSelector.get_info_para_estoque()
   
4. ESTOQUE (Separa + Prepara)
   └─ Popula PedidoEstoque
   └─ Separa componentes
   └─ Valida BOM contra real
   └─ Status: fabricando → em_entrega
   └─ Envia para Bipagem
   
5. BIPAGEM (Monta + Entrega)
   └─ Popula PedidoBipagem
   └─ Instala conforme plantas
   └─ Valida qualidade
   └─ Colhe assinatura
   └─ Status: → finalizado
   └─ Envia para: ARQUIVADO
```

---

## 🛠️ Tasks de Implementação PEDIDO

### Fase 1: Model + Admin (1-2 dias)
- [ ] Criar models em nova app `apps/pedidos/`
- [ ] Registrar no admin Django
- [ ] Criar factories para testes
- [ ] Migrations

### Fase 2: Criação via Comercial (1 dia)
- [ ] View post-contrato que cria PEDIDO
- [ ] Popula núcleo + PedidoProjetos stub
- [ ] Envia notificação para Projetos
- [ ] Redirect para detalhe do PEDIDO

### Fase 3: API de Leitura (1 dia)
- [ ] Endpoints para consultar PEDIDO
- [ ] Selectors para cada setor (`get_info_para_pcp`, etc)
- [ ] Filtros por status

### Fase 4: API de Escrita (2 dias)
- [ ] Endpoints para cada setor atualizar seu módulo
- [ ] Validações por role/setor
- [ ] Audit trail (quem mudou, quando)
- [ ] Notificações entre setores

---

## 📊 Matriz de Permissões - PEDIDO

| Operação | Comercial | Projetos | PCP | Estoque | Bipagem |
|----------|-----------|----------|-----|---------|---------|
| Criar | ✅ | - | - | - | - |
| Ler | ✅ | ✅ | ✅ | ✅ | ✅ |
| Editar Núcleo | ✅* | - | - | - | - |
| Editar ProjN | - | ✅ | Leitura | - | - |
| Editar PCP | - | - | ✅ | Leitura | - |
| Editar Estoque | - | - | - | ✅ | Leitura |
| Editar Bipagem | - | - | - | - | ✅ |
| Archivar | - | - | - | - | ✅ |

*apenas correções dentro de 24h da criação

---

## 🎓 Exemplo de Fluxo Completo

```python
# 1. Comercial fecha venda
cliente = ClienteComercial.objects.get(pk=6)
pedido = ComercialService.fechar_venda_criar_pedido(cliente)
# → PEDIDO #001 criado, status=pedido_criado

# 2. Projetos recebe dados estruturados
info = PedidoSelector.get_info_para_pcp(pedido_id=1)
# → {cliente, ambientes, detalhes_comercial}

# 3. Projetos popula seu módulo
ProjetosService.criar_plantas_e_furacoes(
    pedido_id=1,
    ambientes_detalhados={...}
)
# → PedidoProjetos criada, status=projetando

# 4. PCP consulta specs finais
spec = PedidoSelector.get_pedido_completo(1)
pcp_service.gerar_cronograma(spec)
# → PedidoPCP criada, BOM gerada

# 5. Timeline auditável
pedido = Pedido.objects.get(1)
pedido.historico  # ← Quem mudou o quê e quando
```

---

## 📍 Roadmap Macro

### Sprint Atual (Comercial Final)
- [x] Detalhes de ambiente
- [ ] Teste end-to-end comercial
- [ ] **GO/NOGO** para Projetos

### Próx Sprint (Pedidos + Projetos)
- [ ] Model PEDIDO
- [ ] Integração Comercial → PEDIDO
- [ ] Selectors de leitura
- [ ] Projetos consome + popula

### Sprint +2 (PCP + Estoque)
- [ ] PedidoPCP model
- [ ] PedidoEstoque model
- [ ] Integrações

### Sprint +3 (Bipagem)
- [ ] PedidoBipagem model
- [ ] Fluxo final
- [ ] Assinatura + archivamento

---

## 🚨 Bloqueadores

Nenhum atualmente. ✅

---

## 📞 Contato / Dúvidas

**Comercial**: [Usuario] — Validar fluxo final antes de GO
**Arquitetura**: [Usuario] — PEDIDO é o coração do fluxo futuro

