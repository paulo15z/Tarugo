# 🧠 TARUGO PROJECT MEMORY (Gêmeo Digital & PCP)

Este documento serve como o **contexto mestre** para o projeto Tarugo, permitindo que qualquer nova sessão do Manus entenda o estado atual, as decisões tomadas e os próximos passos.

---

## 🚀 ESTADO ATUAL (MVP MADURO)

O projeto evoluiu de um simples sistema de roteiros para um **Gêmeo Digital** funcional, onde a produção física e o estoque digital estão sincronizados.

### 1. Gêmeo Digital & Sincronia
- **Baixa Automática**: Cada bipagem na fábrica dispara o `GemeoDigitalService`, que calcula o consumo (m² para chapas, UN para ferragens) e abate do estoque.
- **Mapeamento de Materiais**: Existe um "De/Para" entre os nomes do Dinabox e os produtos do estoque (`MapeamentoMaterial`).
- **Dashboard de Discrepâncias**: Interface industrial que aponta falhas de sincronia (ex: bipagem sem estoque ou sem mapeamento).

### 2. PCP Avançado
- **Liberação Manual**: O PCP agora controla explicitamente quando um lote vai para a **Bipagem** e quando vai para a **Viagem (Expedição)**.
- **Roteirização**: Lógica de cálculo de roteiros e planos de corte consolidada no `ProcessamentoPCPService`.

### 3. Estoque & Reservas
- **Padrões de Mercado**: Injetados padrões Duratex, Arauco e Leo Madeiras nas espessuras 6, 15, 18 e 25mm.
- **Reservas por Projeto**: Implementada a lógica de `ReservaService` para garantir que o material de um pedido aprovado não seja consumido por outro.

---

## 🧱 ARQUITETURA (Skill: `tarugo-architecture`)

O projeto segue rigorosamente a separação de responsabilidades:
- **Models**: Dados puros.
- **Services**: Toda a lógica de negócio (Ex: `MovimentacaoService`, `ReservaService`).
- **Selectors**: Queries complexas (Ex: `DiscrepanciaSelector`).
- **Schemas**: Validação forte com Pydantic.
- **Domain**: Enums e tipos puros.

---

## 🛠️ PRÓXIMOS PASSOS (BACKLOG)

1. **Multi-tenant**: Preparar o sistema para rodar como SaaS (isolamento de dados por marcenaria).
2. **Dashboard de Produção**: Visão consolidada de produtividade por operador e por máquina.
3. **Integração ERP**: Exportação de dados financeiros e de compras.
4. **App Mobile**: Refinar a UX da bipagem para dispositivos móveis de baixo custo.

---

## ⚠️ NOTAS IMPORTANTES PARA O MANUS
- **Regra de Ouro**: Se não está no service, está errado.
- **Frontend**: Use a skill `frontend-design` com foco industrial (IBM Plex Mono, tons de cinza, verde para sucesso).
- **Scanner**: O input de bipagem deve suportar Enter automático e debounce de 500ms.

---
*Última atualização: 03/04/2026*
