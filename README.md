# 🪵 Tarugo

Sistema modular desenvolvido em Django com foco na automação de
processos da indústria moveleira.

------------------------------------------------------------------------

## 📌 Contexto

O Tarugo nasce como um projeto de estudo e aplicação prática, com
objetivo de resolver problemas reais dentro do ambiente industrial.

Pode evoluir futuramente para um SaaS escalável, mas atualmente é
utilizado como:

-   Ferramenta interna
-   Objeto de estudo técnico
-   Base para atividades acadêmicas

------------------------------------------------------------------------

## 🎯 Objetivo

-   Automatizar processos industriais
-   Melhorar controle de estoque e produção
-   Servir como base para integrações com ERPs
-   Estruturar um sistema escalável desde o início

------------------------------------------------------------------------

## 🧱 Arquitetura

-   models → estrutura de dados (ORM)
-   services → regras de negócio
-   selectors → consultas ao banco
-   api → camada HTTP (DRF)

Regra crítica: - Nunca colocar regra de negócio em views\
- Sempre utilizar services

------------------------------------------------------------------------

## 🔄 Fluxo

Request → Serializer → Service → Model → Banco → Response

------------------------------------------------------------------------

## ⚙️ Stack

-   Django
-   DRF
-   Pydantic
-   PostgreSQL (planejado)
-   Celery (planejado)

------------------------------------------------------------------------

## 📦 Módulos

-   core
-   estoque
-   pcp (funcional)
-   integracoes
-   scripts (planejado)
-   orcamentos (planejado)

------------------------------------------------------------------------

## 🚀 MVP atual

-   Controle de estoque
-   Movimentações com histórico
-   Base para integrações
-   Evolução do PCP
