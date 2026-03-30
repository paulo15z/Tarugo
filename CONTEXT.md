# 📌 CONTEXTO DE DESENVOLVIMENTO --- TARUGO

## 🎯 Objetivo atual

Finalizar o MVP do módulo de estoque com qualidade de produto real.

------------------------------------------------------------------------

## 🧱 Estado atual

Já existe:

-   Estrutura modular bem definida
-   Produto modelado
-   Movimentações implementadas
-   Services e Pydantic utilizados
-   PCP funcional

------------------------------------------------------------------------

## 🚀 Meta principal

Entregar um sistema de estoque confiável e utilizável em produção
interna.

------------------------------------------------------------------------

## ✅ Checklist do MVP

### 1. Movimentação de estoque

-   [ ] Entrada funcionando corretamente
-   [ ] Saída funcionando corretamente
-   [ ] Validação de estoque negativo
-   [ ] Tipos de movimentação definidos

------------------------------------------------------------------------

### 2. Histórico

-   [ ] Listagem de movimentações
-   [ ] Filtros por produto
-   [ ] Filtros por data
-   [ ] Ordenação

------------------------------------------------------------------------

### 3. Produto

-   [ ] CRUD completo
-   [ ] Validação consistente
-   [ ] Integração com movimentações

------------------------------------------------------------------------

### 4. Regras de negócio

-   [ ] Toda lógica em services
-   [ ] Nenhuma regra em views
-   [ ] Uso de Pydantic validando dados críticos

------------------------------------------------------------------------

### 5. API

-   [ ] Endpoints organizados
-   [ ] Serializers limpos
-   [ ] Respostas padronizadas

------------------------------------------------------------------------

## 📈 Próximos passos (pós-MVP)

-   Integração com ERP
-   Automação de compras
-   Controle de insumos
-   Reserva de estoque

------------------------------------------------------------------------

## 🧠 Diretriz mental

-   Pensar como produto
-   Evitar complexidade desnecessária
-   Garantir que tudo funcione de ponta a ponta

------------------------------------------------------------------------

## ⚠️ Regra principal

Se não está no service, está errado.

## Atualização 29/03/2026
Decisão: PCP congelado temporariamente (usuário chato no trabalho).  
Novo foco: Fortalecer `estoque` na ordem B (backend) → A (acessos) → C (frontend).