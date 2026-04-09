# Contexto 08/04/26

## Objetivo deste documento

Este arquivo consolida o contexto construído nesta conversa para orientar a evolucao do app `bipagem` sem perder o fluxo operacional que ja existe em producao.

O ponto principal e:

- o app `bipagem` **nao deve ser recentralizado em uma tela unica**
- o fluxo atual de bipagem de separacao apos o bordo **e essencial e deve ser preservado**
- a evolucao correta do app e por **postos/ambientes operacionais distintos**
- o novo trabalho deve ser entendido como **evolucao do app existente**, e nao como substituicao do fluxo atual por um MVP paralelo


## Escopo real do app

O app `bipagem` e um app operacional de rastreabilidade industrial.

Ele deve acompanhar o produto desde a peca ate a expedicao, sempre derivando de:

- dados ja existentes no PCP
- estrutura de lote, ambiente, modulo e peca
- regras de roteiro ja calculadas
- informacoes adicionais minimas necessarias para a etapa seguinte

O app nao e apenas um scanner unico. Ele deve suportar varios pontos de checagem na fabrica, com operadores diferentes e telas adequadas para cada posto.


## Regra central de dominio

### 1. Antes da marcenaria / preenchimento de modulo

A unidade operacional principal e a `peca`.

A peca precisa carregar contexto completo:

- `lote`
- `cliente`
- `pedido`
- `ambiente`
- `modulo`
- `codigo_modulo`
- `codigo_peca`
- `roteiro`
- `destino/plano`

Isso permite:

- auditoria de roteiro
- rastreio de falhas
- controle de pecas mortas
- identificacao de erros de fabricacao
- saber para onde a peca deve seguir

### 2. A partir dos setores de preenchimento do modulo

O modulo passa a ser um consolidado operacional.

Setores de preenchimento:

- `DUP`
- `MCX`
- `MPE`
- `MAR`
- `MEL`
- `XMAR`
- `XBOR`

O modulo nao deve ser tratado como se todas as pecas avancassem juntas.

O correto e:

- cada peca avancar no seu proprio ritmo
- o modulo mostrar prontidao por setor
- o modulo ficar `aguardando`, `parcial`, `liberado` ou `concluido` por setor

Exemplo:

- fundo de gaveta pode estar pronto para `MCX`
- lateral da gaveta ainda pode estar em `BOR`, `USI` ou `FUR`
- o modulo fica `parcial` em `MCX`, nao `concluido`


## Fluxo operacional correto do app

O app deve evoluir para pelo menos 3 ambientes distintos de operacao.

### Ambiente 1. Saida do corte

Objetivo:

- conferir o que saiu do corte
- direcionar a peca para maquina/processo seguinte
- ou mandar direto para setor de marcenaria quando aplicavel

Uso esperado:

- peca como unidade principal
- leitura rapida por operador do corte
- indicacao do proximo destino da peca

### Ambiente 2. Bipagem de separacao apos o bordo

Este e o fluxo ja usado hoje e **nao pode ser quebrado**.

Objetivo:

- separar pecas apos o bordo
- indicar destino operacional
- alimentar a transicao para setores de marcenaria e montagem

Uso esperado:

- manter tela/fluxo atual funcionando
- preservar comportamento operacional existente
- evoluir por integracao, nao por substituicao

### Ambiente 3. Expedicao

Objetivo:

- conferir o que chegou na expedicao
- agrupar em `viagens`
- registrar motorista, ajudante opcional, destinos e carga
- marcar chegada e liberacao

Uso esperado:

- conferencia por peca e/ou por modulo
- permissao para expedir lotes parciais
- permissao para misturar mais de um cliente na mesma viagem


## Tecnica de agrupamento

### PCP como fonte da verdade

Os modulos ja sao identificaveis pela referencia importada da lista de corte do PCP.

Logo:

- nao devemos criar cadastro paralelo de modulo
- devemos consolidar e validar o que o PCP ja entrega

Chaves operacionais importantes:

- `pid do lote`
- `ambiente`
- `codigo_modulo`
- `codigo_peca`

### Agrupamento para expedicao

A expedicao deve operar com granularidade suficiente para:

- enviar parte de um lote
- enviar parte de um ambiente
- enviar modulo inteiro
- enviar peca individual
- misturar mais de um cliente na mesma viagem

Mas isso deve continuar derivando dos mesmos dados estruturais do PCP.


## Normas e diretrizes de evolucao

### 1. Nao quebrar fluxo operacional existente

Qualquer extensao do app deve respeitar:

- o fluxo legado de separacao apos o bordo
- os usuarios e postos atuais
- a necessidade de evolucao gradual

Regra:

- novo fluxo entra em paralelo
- fluxo antigo so e substituido quando o novo estiver homologado e aceito operacionalmente

### 2. Nao recentralizar a operacao em uma tela unica

O app nao deve ser desenhado como um painel central unico para todos os operadores.

Deve haver telas/ambientes por posto:

- corte
- separacao/destino
- setores da marcenaria
- expedicao

### 3. Derivar do que ja existe

Evitar qualquer duplicacao estrutural desnecessaria.

Prioridade:

- usar `PecaPCP`
- usar `ModuloPCP`
- usar roteiro existente
- usar metadados de lote/ambiente/modulo
- gravar apenas eventos operacionais e dados necessarios para o proximo passo

### 4. Seguir o padrao de arquitetura Tarugo

Separacao obrigatoria:

- `models/`: estrutura e persistencia
- `services/`: regra de negocio
- `selectors/`: consultas reutilizaveis
- `schemas/`: validacao de entrada/saida
- `api/`: camada HTTP
- `templates/views`: interface por posto


## Arquitetura proposta do app

### Camada de dominio

O app precisa trabalhar com:

- `EtapaOperacional`
- `MovimentoOperacional`
- `EscopoOperacional`
- `StatusViagem/Expedicao`

### Eventos

O nucleo da rastreabilidade deve ser por `evento operacional`.

Cada evento precisa carregar:

- etapa
- movimento
- usuario
- localizacao/posto
- lote
- ambiente
- modulo
- peca
- destino
- observacao

### Viagens

A expedicao deve usar um agregado proprio:

- `Viagem`
- itens da viagem

Campos esperados:

- codigo
- descricao
- transportadora
- placa
- motorista
- ajudante opcional
- destino principal
- destinos secundarios
- status
- recebido em
- liberado em


## Funcionalidades previstas

### Ja previstas/necessarias

- check de saida do corte
- check da separacao apos o bordo
- check de ida/saida para setores de marcenaria
- check de chegada e liberacao na expedicao
- consolidado de prontidao de modulo por setor
- conferencia de viagem com motorista e destinos
- envio parcial
- envio por modulo
- envio por peca
- carga com mais de um cliente

### Futuras

- ASM
- excecoes de substituicao de peca
- interface de reposicao por ambiente/modulo
- tratamento mais rico de pecas mortas/erros
- dashboards gerenciais por posto


## MVP correto

O MVP correto nao e um app novo paralelo. E a primeira etapa da evolucao do app `bipagem`.

Ele deve entregar:

1. Fluxo atual de separacao apos o bordo preservado e operacional.
2. Base de auditoria por peca antes dos setores de preenchimento.
3. Leitura de prontidao de modulo por setor de marcenaria.
4. Expedicao em viagens com conferencia de entrada e saida.
5. Pelo menos 3 ambientes/telas operacionais distintos:
   - saida do corte
   - separacao/destino apos bordo
   - expedicao/viagens


## O que foi feito nesta conversa

Foi iniciada uma base nova dentro do app `bipagem` para suportar:

- eventos operacionais por etapa
- consolidado de modulo por setor
- expedicao em envios/viagens
- APIs novas para operacao
- telas novas de acompanhamento operacional

Tambem foram adicionadas migrations e testes cobrindo:

- separacao de destinos
- fluxo de expedicao
- consolidado parcial de modulo
- renderizacao da tela operacional

### Observacao critica

Apesar de a base tecnica estar util para a evolucao, a direcao conceitual precisa ser corrigida daqui para frente:

- o app nao deve convergir para uma experiencia centralizada unica
- a tela/fluxo legado continua sendo parte essencial do produto
- os novos fluxos precisam ser organizados por posto operacional


## Direcao daqui para frente

Proximas entregas devem seguir esta ordem:

1. preservar e estabilizar o fluxo legado de separacao apos o bordo
2. criar uma tela especifica para saida do corte
3. manter a tela de separacao por destino como ambiente proprio
4. tratar setores da marcenaria como checkpoints por peca/modulo
5. consolidar expedicao como tela propria de viagens
6. so depois disso pensar em ASM


## Resumo executivo

O app `bipagem` deve evoluir para um sistema de checkpoints operacionais distribuidos, e nao para uma tela unica de controle.

A verdade operacional ate a marcenaria e a `peca`.
O consolidado gerencial e logistico a partir dali passa a ser o `modulo`.
Na expedicao, o agregado operacional final e a `viagem`.

Tudo deve continuar derivando do PCP e preservar o fluxo de producao ja existente.
