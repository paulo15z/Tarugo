# Tarugo — Plataforma Modular para Indústria Moveleira

## 📌 Visão Geral

O Tarugo é uma plataforma web desenvolvida para atender indústrias moveleiras, com foco em automação de processos, integração entre sistemas e controle operacional eficiente.

A proposta é centralizar múltiplas funcionalidades em um único sistema modular, reduzindo retrabalho, erros humanos e falhas de comunicação entre setores.

---

## 🎯 Objetivos do Sistema

- Centralizar dados operacionais da empresa
- Automatizar processos críticos (estoque, backup, integrações)
- Reduzir falhas operacionais (falta de material, atrasos)
- Criar base para integrações com sistemas externos (Dinabox, ERPs)
- Evoluir para um SaaS escalável para o setor moveleiro

---

## 🧩 Arquitetura

A aplicação será baseada em Django, com arquitetura modular orientada a apps:

- core → autenticação, permissões e configurações globais
- estoque → controle de produtos e movimentações
- integracoes → comunicação com APIs externas
- backup → rotinas automatizadas
- dashboard → indicadores operacionais
- crm → (futuro)

---

## 🧠 Princípios Arquiteturais

- API-first
- Separação de responsabilidades:
  - models → estrutura de dados
  - services → regras de negócio
  - api → interface HTTP
- Uso de validação de domínio com Pydantic
- Baixo acoplamento entre módulos
- Código orientado a evolução (MVP → produto)

---

## 📦 Módulos Planejados

### 1. Estoque (MVP inicial)

- Cadastro de produtos
- Controle de quantidade
- Movimentações (entrada/saída)
- Histórico de movimentações
- Alerta de estoque mínimo

---

### 2. Autenticação e Controle de Acesso

- Login de usuários
- Permissões por nível (admin, operador)
- Auditoria básica

---

### 3. Integrações (fase inicial leve)

- Estrutura para integração com APIs externas
- Estudo e implementação futura com Dinabox
- Padronização de serviços de integração

---

### 4. Biblioteca de Scripts (Ruby / Dinabox)

- Armazenamento de scripts reutilizáveis
- Organização por tipo (produção, corte, etc.)
- Possível execução ou exportação

---

### 5. Orçamentos (fase futura)

- Cadastro de pedidos
- Estruturação de itens
- Integração com produção e estoque

---

## 🔗 Integrações Planejadas

- Dinabox (principal)
- ERPs utilizados pela empresa
- APIs REST internas

---

## ⚙️ Infraestrutura

- Backend: Django + DRF
- Banco: PostgreSQL (planejado)
- Assíncrono: Celery + Redis (futuro)
- Ambiente: Proxmox (local)
- Containerização: Docker (planejado)

---

## 🚀 Evolução do Produto

1. MVP interno (estoque + login)
2. Estabilização e uso real na empresa
3. Integrações com sistemas existentes
4. Expansão de funcionalidades (orçamentos, CRM)
5. Transformação em SaaS

---

## ⚠️ Diretrizes

- Priorizar resolver problemas reais antes de expandir features
- Evitar complexidade desnecessária no MVP
- Validar com uso real antes de escalar

## 🧠 Arquitetura de Domínio

O sistema utiliza uma abordagem baseada em domínio:

- Estoque é o primeiro domínio crítico
- Movimentações são eventos rastreáveis
- Todas as alterações devem ser auditáveis

O sistema deve sempre priorizar consistência de dados.