🎯 ESCOPO DO APP pedidos (versão “no code”)
Nome do módulo: pedidos
Objetivo principal: Ser o Kanban macro de acompanhamento de pedidos, com granularidade por Ambiente.
O app permite que o Comercial crie um Pedido e já divida-o em Ambientes (Cozinha, Living, Quarto, etc.). Cada Ambiente evolui independentemente no fluxo de etapas.
O Pedido como um todo só é considerado concluído quando todos os seus Ambientes estiverem concluídos.
Regra de negócio central (que vai para o Service):
Um lote gerado pelo PCP pode conter peças de vários Ambientes e até de vários Clientes. Por isso o link entre PCP e Pedidos/Ambientes será flexível (não 1:1 rígido).

📋 Etapas do fluxo (catálogo configurável)
O app terá um modelo chamado Etapa com as seguintes etapas iniciais (populadas automaticamente):

COMERCIAL – Prospecção, orçamento, negociação e fechamento
PROJETOS – Elaboração do projeto executivo e validação de método construtivo
COMPRAS – Separação de insumos e matérias-primas
PCP – Otimização de lote, geração de roteiro e envio para fábrica
PRODUÇÃO – Estágios do roteiro + serviços de terceiros
CQL + EXPEDIÇÃO – Controle de qualidade final e expedição
MONTAGEM – Instalação em obra e assistências técnicas

Cada Etapa terá: ordem, cor, descrição e possibilidade de customização futura por cliente SaaS.

🧱 Modelos principais (descrição teórica)

Etapa
Catálogo central de etapas do fluxo. É reutilizável e configurável.
Pedido
Cabeçalho do pedido (não tem mais “etapa atual” direta).
Número do pedido
Cliente
Link opcional com Orçamento
Link flexível com ProcessamentoPCP (porque um lote pode ter vários Ambientes)
Data de criação, conclusão e status geral
Previsão de entrega final (calculada automaticamente como a maior previsão dos Ambientes)

Ambiente
Este é o cartão real do Kanban.
Pertence a um Pedido
Nome (ex: “Cozinha”, “Living”, “Quarto Suíte”)
Descrição (detalhes que o Comercial preenche)
Etapa atual
Previsão de entrega específica deste Ambiente
Status e data de conclusão
Ordem de exibição dentro do Pedido

HistoricoEtapa
Registro de cada passagem de um Ambiente por uma Etapa.
Vinculado ao Ambiente (não ao Pedido)
Qual Etapa
Data de entrada, conclusão e previsão de saída manual
Responsável e observações



🔄 FLUXO PRÁTICO (como vai funcionar no dia a dia)

Comercial
Cria o Pedido
Adiciona um ou mais Ambientes (pode fazer isso de uma vez, em linhas rápidas)
Cada Ambiente começa automaticamente na Etapa COMERCIAL ou PROJETOS

Demais áreas
Trabalham por Ambiente (ex: aprovar só o projeto da Cozinha)
Avançam a Etapa apenas daquele Ambiente
Podem colocar previsão de saída manual em cada Etapa

PCP
Ao processar um arquivo Dinabox, o sistema identifica quais Ambientes estão presentes no lote
Cria ou vincula o ProcessamentoPCP a vários Ambientes (relação Many-to-Many ou via tabela intermediária)
Avança automaticamente os Ambientes presentes para a Etapa PCP

Visão geral
Tela de Kanban mostra colunas por Etapa e cartões são os Ambientes
Pedido pai mostra status agregado (ex: “3 de 5 Ambientes concluídos”)



🔗 RELAÇÕES COM OUTROS APPS (atual e futuro)


AppTipo de relaçãoComo acontece na práticacorePedido → ClienteInalteradoorcamentosPedido → OrçamentoAo aprovar orçamento → cria Pedido + Ambientes automaticamentepcpProcessamentoPCP ↔ Vários AmbientesUm lote pode ter peças de múltiplos Ambientes e múltiplos Clientes → link flexívelestoqueFuturo: Movimentação → AmbienteSaída de material vinculada diretamente ao AmbienteproducaoFuturo (ou dentro de pedidos)Estágios do roteiro avançam Ambiente automaticamenteintegracoesWebhooksFuturo: integração com ERP cria Pedido + Ambientes automaticamente
Ponto crítico de integração com PCP:
Como o PCP já gera lotes mistos, não vamos forçar relação 1:1. O service do PCP, ao finalizar o processamento, vai identificar os Ambientes presentes (pelo número do pedido ou tag no arquivo) e avançar cada um para a Etapa PCP de forma independente.