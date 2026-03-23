# 🏭 PROCESSOS ATUAIS DA EMPRESA

**Objetivo:** Documentar como os processos funcionam TODAY, para que o Tarugo se integre corretamente.

---

## 📦 1. CADEIA DE SUPRIMENTOS

### 1.1 Aquisição de Matéria-Prima

#### MDFs
- **Padrão:** Branco TX, MDF Ultra (comprados sempre em estoque)
- **Sob Demanda:** Rosa, Amarelo, Verde, Cinza, etc. (comprados conforme projeto)
- **Forma:** Chapas inteiras (2750mm × 1830mm, espessura variável)

#### Ferragens
- Dobradiças, puxadores, trilhos, etc.
- **Fornecedores:** Múltiplos (códigos diferentes por fornecedor)

#### Acessórios
- Vidros, espelhos, pés

#### Insumos
- Cola, verniz, lixa, tinta
- **Embalagem:** Variável (latas, baldes, garrafas)

### 1.2 Recebimento
- Conferência de quantidade
- Armazenamento por tipo/acabamento
- **Sem sistema atualmente:** Controle manual em planilhas

---

## ✂️ 2. PROCESSO DE CORTE (CORE DO NEGÓCIO)

### 2.1 Planejamento (Fim do Dia 0)

**Quem:** Almoxarife + PCP (Planejamento e Controle da Produção)

**O que acontece:**
1. Analisam projetos/pedidos para o dia seguinte
2. Identificam quais chapas serão cortadas (qual projeto, quantidades)
3. Separam as chapas do estoque e as **reservam**
4. Se for sob demanda, confirma que a chapa chegou

**Sistema atual:** Planejamento em planilhas (Excel) + avisos verbais

### 2.2 Execução (Dia 1, início do turno)

**Quem:** Operador da serra CNC + Almoxarife

**O que acontece:**
1. Operador pega as chapas já separadas
2. Programa a CNC com os cortes do projeto
3. Executa os cortes
4. **Material cortado:** segue para a próxima etapa (produção/montagem)
5. **Sobras:** ficam na área de corte (sem rastreio sistemático)

**Problema atual:**
- Sobras não são registradas
- Não sabe se vai reutilizar ou descartar
- Perda de material não é mensurada
- Sobras padrão (Branco TX) são misturadas com sob demanda (Rosa, etc)

### 2.3 Resultado (Fim do Dia 1)

**O que deveria haver:**
1. Registro de qual chapa foi cortada
2. Quantidades utilizadas
3. Dimensões das sobras
4. Se foram descartadas ou armazenadas

**Hoje:** Nada disso é registrado sistematicamente

---

## 🏗️ 3. FLUXO PRODUÇÃO GERAL (FUTURO)

*Nota: Tarugo será expandido para isso depois*

### 3.1 Montagem
- Peças cortadas são montadas
- Insumos (cola, parafusos) são utilizados
- Móvel toma forma

### 3.2 Acabamento
- Pintura/verniz (insumos)
- Lixamento
- Montagem final de ferragens/acessórios

### 3.3 Embalagem
- Móvel pronto é embalado
- Segue para entrega

---

## 💾 4. O QUE NÃO EXISTE ATUALMENTE

- ❌ Rastreio de sobras de corte
- ❌ Mensuração de perdas/desperdício
- ❌ Controle de estoque por acabamento (tudo é "MDF")
- ❌ Vínculo de material com projeto
- ❌ Autorização de reutilização de sobras
- ❌ Histórico de movimentações
- ❌ Alertas de estoque baixo
- ❌ Dashboard de KPIs

---

## 🎯 5. O QUE O TARUGO VAI RESOLVER

### Fase 1 (MVP Atual) ✅
- ✅ Registro de movimentações básicas (entrada/saída)
- ✅ Histórico rastreável
- ✅ Alertas de estoque

### Fase 2 (Próxima)
- 🔄 Separação de cortes por tipo específico (ChapaMDF)
- 🔄 Registro de sobras com dimensões
- 🔄 Bloqueio de sobras sob demanda
- 🔄 Reutilização controlada

### Fase 3 (Futura)
- 📋 Planejamento de cortes no sistema
- 📋 Rastreio de cada etapa
- 📋 KPIs de desperdício
- 📋 Integração com Dinabox (enviando dados de cortes)

---

## 📊 6. DADOS IMPORTANTES PARA O TARUGO

### 6.1 Tipos de Acabamento de MDF
- **Padrão (sempre em estoque):**
  - Branco TX
  - MDF Ultra
  
- **Sob demanda (comprado por projeto):**
  - Rosa
  - Amarelo
  - Verde
  - Cinza
  - Preto
  - Outros (custom)

### 6.2 Espessuras Comuns
- 15mm
- 18mm
- 25mm
- Outras (conforme pedido)

### 6.3 Dimensões Padrão de Chapas
- 2750mm (comprimento)
- 1830mm (largura)
- Espessura: variável

### 6.4 Estrutura de Projetos
- **ID do Projeto:** Identificação única (ex: PROJ-202603-001)
- **Tipo de Product:** Qual móvel será feito
- **Data de entrega:** Prazo
- **Lista de materiais:** Quais chapas, ferragens, etc. serão usados

---

## 🔄 7. REGRAS DE NEGÓCIO CRÍTICAS

### Regra 1: Sobras Padrão vs Sob Demanda
```
Sobra de Padrão (Branco TX cortado):
  → Pode ser reutilizada em qualquer projeto
  → Imediatamente disponível
  → Valor: recuperável

Sobra de Sob Demanda (Rosa cortado para Projeto A):
  → Pertence ao Projeto A enquanto estiver ativo
  → Só pode ser reutilizada em outro projeto com autorização de admin
  → Após projeto fechar: pode ser oferecida para outros projetos
  → Valor: pode ser descartada (rosa não é padrão)
```

### Regra 2: Reserva de Material
```
Chapa sob demanda (Rosa):
  Dia 0: Separada do recebimento
  Dia 1: Em corte
  Dia 1 (fim): Convertida em sobra ou descartada
  → Sistema deve validar: só pode ser usada no projeto reservado
```

### Regra 3: Mensuração de Desperdício
```
Chapa inteira: 2750 × 1830 = 5.034.750 mm²
Cortes para projeto: 4.000.000 mm² usados
Sobra: 1.034.750 mm² (20% de desperdício)

Sistema deve rastrear isso para relatórios
```

---

## 📈 8. POTENCIAL DE MELHORIA

### Tempo Economizado
- **Hoje:** Buscar informação de estoque = 5-10 min (manual, erros)
- **Com Tarugo:** < 1 segundo (query automática, preciso)

### Redução de Erros
- **Hoje:** Estoque duplicado em planilha = disparidades
- **Com Tarugo:** Uma fonte de verdade

### Mensuração de Perdas
- **Hoje:** "Perdemos material, mas não sabemos quanto"
- **Com Tarugo:** KPI de desperdício por projeto/mês

### Reutilização Controlada
- **Hoje:** Sobras são descartadas ou perdidas
- **Com Tarugo:** Visibilidade total de reutilização

---

## 🚀 9. ROADMAP DE INTEGRAÇÃO

### Curto Prazo (Próximas semanas)
1. Tarugo rastreia separações de corte
2. Tarugo registra sobras reais
3. Almoxarife usa app para registrar movimentações

### Médio Prazo (Próximos meses)
1. Planejamento de cortes integrado no Tarugo
2. Relatórios de desperdício
3. Alertas de material baixo

### Longo Prazo (Roadmap SaaS)
1. Integração com Dinabox (envio de dados de corte)
2. Dashboard operacional
3. Previsões de compra baseadas em histórico
4. Expansão para outras etapas (montagem, acabamento)

---

## 📝 Perguntas em Aberto

*Para próximas discussões com o time:*

- [ ] Qual é o custo de 1m² de cada acabamento?
- [ ] Qual é o KPI aceitável de desperdício?
- [ ] Como autorizar reutilização de sobra (fluxo)?
- [ ] Precisa de rastreio de localização física no estoque?
- [ ] Qual é o tempo de vida de um projeto no sistema?
- [ ] Existem projetos recorrentes que reutilizam design?

---

**Última atualização:** 23 de Março de 2026
