---
name: tarugo-frontend-design
description: Cria interfaces frontend profissionais, limpas e otimizadas para o Tarugo (sistema industrial moveleiro). Use este skill sempre que precisar construir ou melhorar telas, componentes ou páginas (ex: dashboard de lotes, tela de bipagem, listagem de PCP, formulários de estoque). Prioriza legibilidade em ambiente fabril, hierarquia clara, usabilidade rápida e estética Industrial Clean. Evita designs genéricos ou excessivamente artísticos.
license: MIT
---

# 🎨 Tarugo Frontend Design

Guia oficial de design frontend para o Tarugo — sistema para indústria moveleira.

## Quando Usar Este Skill

Use sempre que precisar:
- Criar uma nova tela ou página (dashboard, bipagem, PCP, estoque, etc.)
- Melhorar ou refatorar interface existente
- Desenvolver componentes reutilizáveis (cards de progresso, tabelas, feedback de bipagem)
- Definir estilo visual consistente em todo o sistema

## Diretrizes de Design do Tarugo

**Estilo principal**: **Industrial Clean**

Características obrigatórias:
- Legibilidade máxima (ambiente de fábrica com iluminação variável)
- Hierarquia visual forte
- Feedback rápido e claro
- Interface pensada para uso em telas grandes (computadores e tablets)
- Pouca distração visual — foco na informação

### Paleta de Cores (CSS Variables)

```css
:root {
  --bg: #0a0a0a;
  --surface: #1a1a1a;
  --surface-2: #252525;
  --primary: #3b82f6;        /* Azul industrial */
  --success: #22c55e;
  --warning: #eab308;
  --danger: #ef4444;
  --text: #f1f1f1;
  --text-muted: #a3a3a3;
  --border: #3f3f46;
}
```

### Tipografia

- **Headings**: Satoshi, Space Grotesk ou Inter Display — peso 600/700
- **Body**: Inter ou system sans-serif — peso 400/500
- **Tamanhos**: base 16px; headings 20–28px; labels e pequenos 14px

### Princípios de layout

- Cards grandes e bem espaçados (progresso de lotes e módulos)
- Tabelas com status coloridos e legíveis
- Área de bipagem com feedback grande (sucesso/erro)
- Sidebar de navegação limpa; muito espaço negativo
- Modo escuro como padrão (contexto de fábrica)

### Motion e interações

- Transições 200–300ms
- Bipagem: feedback imediato (scale + cor + ícone)
- Loading claro e não intrusivo; hovers sutis
- Stagger na entrada só quando agregar valor

### Componentes mais usados

- Card de progresso (pedido / lote / módulo)
- Tela de bipagem (foco total)
- Tabela de peças com status
- Dashboard por lote
- Formulários simples e grandes

## Como criar interfaces com este skill

1. Escolher tipo de tela/componente e objetivo principal (ex.: bipar rápido).
2. Aplicar paleta Industrial Clean e hierarquia clara.
3. Incluir estados: vazio, loading, sucesso, erro.
4. Validar legibilidade em fundo escuro.

**Exemplos de prompts:**

- "Crie a tela principal de bipagem com feedback grande"
- "Melhore o dashboard de lotes mantendo estilo industrial clean"
- "Desenvolva o card de progresso de módulo"

## Referências complementares

- [references/component-examples.md](references/component-examples.md) — exemplos de componentes
- [references/color-system.md](references/color-system.md) — paleta detalhada
- [templates/](templates/) — boilerplates

**Última atualização:** 03 de abril de 2026

**Regra de ouro:** Deve parecer um sistema profissional de fábrica — confiável, rápido e sem frescuras, nunca um dashboard bonito de startup.