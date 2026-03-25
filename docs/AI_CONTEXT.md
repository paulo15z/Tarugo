# 🧠 CONTEXTO DO PROJETO — TARUGO

## 📌 SOBRE O PROJETO

O Tarugo é uma plataforma web em desenvolvimento voltada para indústrias moveleiras.

Objetivo:

* Resolver problemas reais da operação (estoque, produção, integração)
* Automatizar processos
* Centralizar dados
* Evoluir para um SaaS

---

## 🧱 STACK

* Django
* Django Rest Framework
* Pydantic
* SQLite (MVP) → PostgreSQL (futuro)
* Proxmox (infra local)

---

## 🧩 ARQUITETURA

Arquitetura modular baseada em apps Django:

* core → autenticação e base
* estoque → produtos e movimentações
* integracoes → APIs externas (Dinabox, ERP)
* scripts → biblioteca de scripts (planejado)
* orcamentos → (planejado)

---

## 🧠 PADRÃO DE DESENVOLVIMENTO

Separação de responsabilidades:

* models → estrutura de dados
* services → regras de negócio
* selectors → consultas ao banco
* api → interface HTTP

---

## ⚠️ REGRAS IMPORTANTES

* NUNCA colocar regra de negócio em views
* SEMPRE usar services
* Validar dados em duas camadas:

  * DRF (entrada HTTP)
  * Pydantic (regra de negócio)
* Código deve ser modular e reutilizável

---

## 🔄 FLUXO DO SISTEMA

Request → Serializer → Service → Model → Banco → Response

---

## 📦 STATUS ATUAL

Já implementado:

* Estrutura do projeto Django modular
* App `estoque`
* Model `Produto`
* Model `Movimentacao`
* Service de movimentação com:

  * transaction.atomic
  * select_for_update
* Validação com Pydantic
* Endpoint de movimentação

---

## 🎯 OBJETIVO ATUAL

Estamos desenvolvendo o MVP com foco em:

* Controle de estoque
* Movimentações com histórico
* Base para integração futura

---

## 🚀 PRÓXIMOS PASSOS

* Criar histórico de movimentações (listagem)
* Implementar selectors
* Criar filtros (produto, data)
* Melhorar regras de estoque (mínimo, alertas)
* Estruturar integração com Dinabox

---

## 🧠 FILOSOFIA

O Tarugo não é apenas um sistema interno.

É uma base para um produto SaaS.

Toda decisão deve considerar:

* Escalabilidade
* Integração
* Reuso
* Simplicidade

---

## 📌 COMO RESPONDER

* Seguir arquitetura definida
* Explicar decisões técnicas
* Priorizar soluções simples e profissionais
* Evitar overengineering

---

## 🎯 CONTEXTO DO USUÁRIO

* Desenvolvedor com base em Python
* Aprendendo Django com foco em boas práticas
* Projeto sendo usado em contexto real (empresa moveleira)
* Busca aprendizado + construção de produto real

---

Continuar o desenvolvimento respeitando este contexto.
