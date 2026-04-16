# Proposta Técnica: Módulo 'Projetos' no Tarugo

## 1. Introdução

Este documento detalha a proposta técnica para a implementação do novo módulo 'Projetos' no sistema Tarugo. O objetivo principal é integrar o fluxo de trabalho de engenharia e projeto executivo, desde a recepção de um pedido comercial até a liberação para o PCP (Planejamento e Controle da Produção), garantindo rastreabilidade, consistência e aderência à arquitetura modular existente do Tarugo.

O módulo 'Projetos' atuará como uma camada intermediária entre o módulo 'Comercial' e 'PCP', utilizando as entidades `Pedido` e `AmbientePedido` do módulo `pedidos` como base, e enriquecendo-as com informações específicas do processo de projeto, como atribuições de usuários, status de desenvolvimento, anexos e validações.

## 2. Alinhamento com a Arquitetura Tarugo

Conforme o guia `tarugo-architecture`, o desenvolvimento seguirá rigorosamente a separação de responsabilidades:

*   **Models:** Apenas representação do banco de dados, sem lógica de negócio.
*   **Services:** Centralizarão todas as regras de negócio, validações críticas e orquestração de operações.
*   **Schemas (Pydantic):** Responsáveis pela validação de entrada e tipagem forte.
*   **Domain:** Definirá enums e conceitos reutilizáveis, como os status de projeto.
*   **Views:** Receberão requisições, chamarão os `Services` e retornarão respostas, sem lógica de negócio.

O app `estoque` foi utilizado como referência para a implementação dos padrões.

## 3. Modelagem de Dados

Serão criadas novas entidades para gerenciar o ciclo de vida dos projetos. A principal entidade será `Projeto`, que se relacionará diretamente com `Pedido` e `AmbientePedido`.

### 3.1. `Projeto` Model

Representa o projeto executivo de um pedido. Um `Pedido` pode ter um ou mais `Projetos` associados, especialmente se houver múltiplos ambientes que exigem projetos separados ou fases distintas.

```python
# apps/projetos/models/projeto.py

from django.conf import settings
from django.db import models
from apps.pedidos.models import Pedido
from apps.core.models import BaseModel # Assumindo BaseModel para campos comuns

from apps.projetos.domain.status import ProjetoStatus

class Projeto(BaseModel):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="projetos",
        verbose_name="Pedido Associado",
    )
    nome_projeto = models.CharField(
        max_length=255,
        verbose_name="Nome do Projeto",
        help_text="Ex: Projeto Executivo Cozinha",
    )
    status = models.CharField(
        max_length=32,
        choices=ProjetoStatus.choices,
        default=ProjetoStatus.AGUARDANDO_DEFINICOES,
        db_index=True,
        verbose_name="Status do Projeto",
    )
    distribuidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_distribuidos",
        verbose_name="Distribuidor de Projetos",
    )
    projetista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_designados",
        verbose_name="Projetista Responsável",
    )
    liberador_tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_para_liberacao",
        verbose_name="Liberador Técnico",
    )
    data_inicio_prevista = models.DateField(
        null=True, blank=True, verbose_name="Data Início Prevista"
    )
    data_fim_prevista = models.DateField(
        null=True, blank=True, verbose_name="Data Fim Prevista"
    )
    data_inicio_real = models.DateTimeField(
        null=True, blank=True, verbose_name="Data Início Real"
    )
    data_fim_real = models.DateTimeField(
        null=True, blank=True, verbose_name="Data Fim Real"
    )
    observacoes = models.TextField(
        blank=True, verbose_name="Observações Internas"
    )

    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["status", "-criado_em"], name="proj_status_idx"),
            models.Index(fields=["projetista", "status"], name="proj_proj_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Projeto {self.nome_projeto} ({self.pedido.numero_pedido})"

```

### 3.2. `AmbienteProjeto` Model (Opcional, para granularidade)

Considerando que o `AmbientePedido` já possui um status e pode ser enriquecido com dados de engenharia, inicialmente, o `Projeto` será a unidade principal de trabalho. No entanto, se houver a necessidade de gerenciar o status de cada ambiente individualmente dentro do fluxo de projetos (ex: um ambiente está 'Em Desenvolvimento' enquanto outro está 'Aguardando Definições' no mesmo projeto), podemos introduzir um `AmbienteProjeto` que se relaciona com `Projeto` e `AmbientePedido`.

**Decisão:** Para o MVP, vamos manter a simplicidade e associar o `Projeto` diretamente ao `Pedido`. O `AmbientePedido` existente no módulo `pedidos` já possui um `status` (`PENDENTE_PROJETOS`, `EM_ENGENHARIA`, etc.) que pode ser atualizado pelo `ProjetoService` para refletir o progresso individual dos ambientes. Isso evita duplicação de dados e complexidade desnecessária para o MVP.

### 3.3. `AnexoProjeto` Model

Para gerenciar os arquivos (PDFs, imagens de obra/medição) que vêm do Comercial ou são gerados durante o projeto.

```python
# apps/projetos/models/anexo.py

from django.conf import settings
from django.db import models
from apps.core.models import BaseModel
from apps.projetos.models.projeto import Projeto

class AnexoProjeto(BaseModel):
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name="anexos",
        verbose_name="Projeto",
    )
    arquivo = models.FileField(
        upload_to="projetos/anexos/%Y/%m/%d/",
        verbose_name="Arquivo",
    )
    nome_arquivo = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nome do Arquivo",
    )
    tipo_anexo = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Tipo de Anexo",
        help_text="Ex: PDF, Imagem, DWG",
    )
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anexos_projetos_uploaded",
        verbose_name="Enviado por",
    )

    class Meta:
        verbose_name = "Anexo de Projeto"
        verbose_name_plural = "Anexos de Projetos"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.nome_arquivo or self.arquivo.name} ({self.projeto.nome_projeto})"

```

## 4. Workflow de Estados do Projeto e Interação com o Pedido

Os estados do projeto serão definidos no `domain` do módulo `projetos` e gerenciados pelo `ProjetoService`. As transições serão controladas por regras de negócio específicas, com uma clara interação com o status do `Pedido` e `AmbientePedido` do módulo `pedidos`.

### 4.1. Arquitetura de Estados por Setor

O sistema Tarugo adota uma **arquitetura de estados por setor**, onde cada módulo gerencia seu próprio ciclo de vida interno para as entidades relevantes. O `Pedido` atua como uma entidade orquestradora de alto nível, cujo status reflete o progresso geral através dos diferentes setores da empresa. O módulo `Projetos` terá seu próprio conjunto de estados (`ProjetoStatus`) que detalham o progresso do projeto executivo, enquanto o `PedidoStatus` (do módulo `pedidos`) indicará que o pedido está na fase de projetos.

Por exemplo, quando um pedido entra no setor de Projetos, seu `PedidoStatus` será `ENVIADO_PARA_PROJETOS`. Internamente, o `Projeto` associado a esse pedido passará por seus próprios estados (`AGUARDANDO_DEFINICOES`, `EM_DESENVOLVIMENTO`, etc.). A transição final do `Projeto` para `LIBERADO_PARA_PCP` será o gatilho para que o `PedidoService` atualize o `PedidoStatus` para `EM_ENGENHARIA` (ou outro status apropriado para a próxima fase, como `AGUARDANDO_PCP` no `AmbienteStatus`).

### 4.2. `ProjetoStatus` Enum

```python
# apps/projetos/domain/status.py

from django.db import models

class ProjetoStatus(models.TextChoices):
    AGUARDANDO_DEFINICOES = "AGUARDANDO_DEFINICOES", "Aguardando Definições"
    AGUARDANDO_PROJETISTA = "AGUARDANDO_PROJETISTA", "Aguardando Projetista"
    EM_DESENVOLVIMENTO = "EM_DESENVOLVIMENTO", "Em Desenvolvimento"
    EM_CONFERENCIA = "EM_CONFERENCIA", "Em Conferência"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO", "Aguardando Aprovação"
    LIBERADO_PARA_PCP = "LIBERADO_PARA_PCP", "Liberado para PCP"
    CANCELADO = "CANCELADO", "Cancelado"

```

### 4.3. Transições de Estado e Regras de Negócio (via `ProjetoService`)

| Estado Atual | Ação / Próximo Estado | Responsável | Regras de Negócio | Interação com Pedido/Ambiente |
|---|---|---|---|---|
| `AGUARDANDO_DEFINICOES` | Atribuir Projetista / `AGUARDANDO_PROJETISTA` | Distribuidor | Somente Distribuidor pode atribuir. Requer `projetista` preenchido. | `AmbientePedido.status` pode ser `PENDENTE_PROJETOS`. | 
| `AGUARDANDO_PROJETISTA` | Iniciar Desenvolvimento / `EM_DESENVOLVIMENTO` | Projetista | Somente Projetista atribuído pode iniciar. | `AmbientePedido.status` pode ser atualizado para `EM_ENGENHARIA` pelo `ProjetoService` ao iniciar o desenvolvimento do projeto. | 
| `EM_DESENVOLVIMENTO` | Enviar para Conferência / `EM_CONFERENCIA` | Projetista | Projetista finaliza sua parte. Pode exigir upload de anexos obrigatórios. | Nenhuma alteração direta no `PedidoStatus` ou `AmbienteStatus` neste ponto. | 
| `EM_CONFERENCIA` | Aprovar Conferência / `AGUARDANDO_APROVACAO` | Liberador Técnico | Somente Liberador Técnico pode aprovar. | Nenhuma alteração direta no `PedidoStatus` ou `AmbienteStatus` neste ponto. | 
| `AGUARDANDO_APROVACAO` | Aprovar Cliente / `LIBERADO_PARA_PCP` | Admin/Distribuidor | Requer aprovação do cliente (ou liberação administrativa). | Ao transicionar para `LIBERADO_PARA_PCP`, o `ProjetoService` deve:
    1.  Atualizar o `AmbienteStatus` de todos os `AmbientePedido` relacionados para `AGUARDANDO_PCP`.
    2.  Verificar se todos os projetos do `Pedido` estão `LIBERADO_PARA_PCP`. Se sim, o `PedidoService` deve ser chamado para atualizar o `PedidoStatus` para `EM_ENGENHARIA` (ou o próximo status macro). | 
| Qualquer Estado | Cancelar Projeto / `CANCELADO` | Admin/Distribuidor | Requer justificativa. | O `ProjetoService` deve notificar o `PedidoService` para avaliar o impacto no `PedidoStatus` e `AmbienteStatus` (ex: reverter para `CONTRATO_FECHADO` ou marcar ambientes como `CANCELADO`). | 

## 5. Hierarquia de Papéis e Permissões

Serão utilizados os grupos de usuários existentes no Django (`django.contrib.auth.models.Group`) para definir as permissões. Novos grupos podem ser criados conforme a necessidade.

| Papel | Grupo (sugerido) | Permissões Principais | Interações no Módulo Projetos |
|---|---|---|---|
| **Distribuidor de Projetos** | `Projetos_Distribuidor` | Criar, editar, atribuir projetos. Mover projetos entre estados (exceto os de Projetista/Liberador). Acesso a relatórios. | Atribui `Projetista` e `Liberador Técnico`. Pode cancelar projetos. | 
| **Projetista** | `Projetos_Projetista` | Visualizar projetos atribuídos. Mover projetos para `EM_DESENVOLVIMENTO` e `EM_CONFERENCIA`. Fazer upload de anexos. | Responsável pela elaboração do projeto executivo. | 
| **Liberador Técnico** | `Projetos_LiberadorTecnico` | Visualizar projetos. Mover projetos para `AGUARDANDO_APROVACAO`. | Responsável pela validação técnica do projeto. | 
| **Admin** | `Admin` | Todas as permissões. | Pode intervir em qualquer etapa, liberar projetos, etc. | 

## 6. Estrutura de Telas (MVP)

As telas seguirão o padrão de simplicidade e usabilidade do Tarugo, focando nas funcionalidades essenciais para o MVP.

### 6.1. Telas por Usuário

*   **Meus Projetos (Projetista):** Listagem dos projetos atribuídos ao projetista logado, com filtros por status. Cada item da lista levará a uma tela de detalhes do projeto.
    *   **Detalhe do Projeto:** Exibirá informações do pedido, dados do projeto, status atual, histórico de atividades, e uma seção para upload/visualização de anexos. Haverá botões de ação para as transições de estado permitidas ao projetista (ex: 
Iniciar Desenvolvimento, Enviar para Conferência).
*   **Produção (Distribuidor/Gestão):** Listagem de projetos finalizados (`LIBERADO_PARA_PCP`) em um determinado período, com informações de performance e produtividade.

### 6.2. Funcionalidades Essenciais

*   **Listagem de Projetos:** Visão geral dos projetos, com filtros por status, projetista, distribuidor, etc.
*   **Formulário de Atribuição/Criação de Projeto:** O Distribuidor poderá criar um novo `Projeto` a partir de um `Pedido` existente e atribuir `Projetista` e `Liberador Técnico`.
*   **Upload de Anexos:** Funcionalidade para anexar arquivos (PDFs, imagens) ao `Projeto`.
*   **Checklist de Liberação:** Um mecanismo simples (com alerta de confirmação) para o Projetista passar o projeto para o Liberador Técnico.

## 7. Integração com Módulos Existentes

*   **Módulo `pedidos`:** O `Projeto` estará diretamente ligado ao `Pedido`. O `ProjetoService` será responsável por interagir com o `PedidoService` para atualizar o `PedidoStatus` e `AmbienteStatus` conforme o progresso do projeto.
*   **Módulo `comercial`:** Informações iniciais do `Pedido` e `AmbienteOrcamento` serão utilizadas para iniciar o `Projeto`.
*   **Módulo `core`:** Utilização do modelo de usuário (`AUTH_USER_MODEL`) e grupos para gerenciamento de papéis e permissões.

## 8. Checklist de Qualidade (Módulo Projetos)

Antes de finalizar qualquer implementação, o seguinte checklist será rigorosamente seguido:

*   [ ] A lógica de negócio está exclusivamente nos `Services`?
*   [ ] Os `Schemas` (Pydantic) validam todas as entradas?
*   [ ] As transições de status são atômicas (`@transaction.atomic`)?
*   [ ] O `ProjetoStatus` reflete corretamente o estado interno do projeto?
*   [ ] A interação com `PedidoStatus` e `AmbienteStatus` é consistente e ocorre no momento certo?
*   [ ] O código está simples, claro e aderente aos padrões do Tarugo?
*   [ ] As permissões de usuário estão corretamente aplicadas para cada transição de estado?

## 9. Próximos Passos

1.  Criação do app `projetos`.
2.  Implementação dos Models (`Projeto`, `AnexoProjeto`).
3.  Definição dos `ProjetoStatus` no `domain`.
4.  Desenvolvimento do `ProjetoService` com as regras de transição de estado e interação com `PedidoService`.
5.  Criação dos `Schemas` para validação de entrada.
6.  Implementação das `Views` e templates para as telas do MVP.
7.  Configuração das permissões e grupos de usuários.

## 10. Referências

[1] tarugo-architecture skill: `/home/ubuntu/skills/tarugo-architecture/SKILL.md`
[2] Pedidos Application Architecture and Data Flow: `https://www.notion.so/manus-ai/Pedidos-Application-Architecture-and-Data-Flow-iB9soARhxjfdRGsbsAqPgA`
[3] `apps/pedidos/models/pedido.py`
[4] `apps/pedidos/models/ambiente.py`
[5] `apps/pedidos/domain/status.py`
[6] `apps/comercial/models.py`
[7] `apps/core/management/commands/seed_initial_users.py`
