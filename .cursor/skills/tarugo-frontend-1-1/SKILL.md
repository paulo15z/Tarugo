---
name: tarugo-frontend-1-1
description: Orienta implementação de telas e UI do Tarugo (indústria moveleira) no estilo Industrial Clean e alinhamento com a arquitetura Django do repo. Use ao criar ou refatorar páginas, templates, componentes, dashboards, bipagem, PCP, estoque; ao pedir mockups ou CSS para o Tarugo; ou quando UI e backend (views/serializers/services) forem alterados juntos.
---

# Tarugo frontend 1.1 (Cursor)

## Fonte de verdade no repositório

Este skill é um **índice** para a documentação versionada em `skills/`. Antes de implementar UI relevante, **leia** os arquivos indicados (progressive disclosure).

| Objetivo | Arquivo |
|----------|---------|
| Design, paleta, componentes, fluxo de tela | [skills/tarugo-frontend-design/SKILL.md](skills/tarugo-frontend-design/SKILL.md) |
| Exemplos de componentes | [skills/tarugo-frontend-design/references/component-examples.md](skills/tarugo-frontend-design/references/component-examples.md) |
| Paleta detalhada | [skills/tarugo-frontend-design/references/color-system.md](skills/tarugo-frontend-design/references/color-system.md) |
| Boilerplate de página | [skills/tarugo-frontend-design/templates/page-boilerplate.html](skills/tarugo-frontend-design/templates/page-boilerplate.html) |
| Backend (Services, DRF, Pydantic) junto com UI | [skills/tarugo-architecture/SKILL.md](skills/tarugo-architecture/SKILL.md) |
| Frontend vs camadas (contexto) | [skills/tarugo-architecture/references/frontend-design.md](skills/tarugo-architecture/references/frontend-design.md) |

## Regras rápidas (não substituem os guias)

- Estilo **Industrial Clean**: legibilidade em fábrica, hierarquia forte, pouca decoração, modo escuro como base natural do produto.
- Telas operacionais (bipagem, produção): feedback grande e imediato; estados vazio / loading / erro sempre explícitos.
- Se a mudança incluir lógica de negócio ou API: seguir `tarugo-architecture` (negócio em **Service**, validação em **Pydantic**, etc.).

## Fluxo sugerido para o agente

1. Confirmar tipo de trabalho (só UI vs UI + backend).
2. Abrir `skills/tarugo-frontend-design/SKILL.md` e, se necessário, `references/` ou `templates/`.
3. Se tocar em views, serializers ou regras: abrir `skills/tarugo-architecture/SKILL.md`.
4. Implementar no mesmo padrão de arquivos e convenções já usados no app afetado (`estoque`, `pcp`, `bipagem`, etc.).

## Regra de ouro (Tarugo UI)

Deve parecer sistema profissional de fábrica — confiável e rápido — não dashboard genérico de startup.
