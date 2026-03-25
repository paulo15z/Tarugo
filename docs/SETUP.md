
# 🛠️ Setup e Funcionamento — Tarugo

---

# 📌 Visão Geral

O Tarugo é uma aplicação web baseada em Django, construída com arquitetura modular e orientada a serviços.

O sistema foi projetado para ser:

* Escalável
* Modular
* Integrável com sistemas externos
* Fácil de evoluir

---

# 🧱 Arquitetura do Projeto

## Estrutura principal

```
tarugo/
  config/        → configurações do Django
  apps/          → módulos do sistema
    core/        → autenticação e base
    estoque/     → controle de estoque
    integracoes/ → APIs externas
  manage.py
```

---

# 🧠 Separação de responsabilidades

O projeto segue um padrão inspirado em arquitetura limpa.

## models/

Responsável por:

* Estrutura do banco
* Definição das entidades

⚠️ Não deve conter regras complexas

---

## services/

Responsável por:

* Regras de negócio
* Processamento de dados
* Orquestração

👉 Exemplo:

* movimentar estoque
* validar operação

---

## selectors/

Responsável por:

* Consultas ao banco
* Queries reutilizáveis

---

## api/

Responsável por:

* Interface HTTP (Django Rest Framework)
* Entrada e saída de dados

---

# 🔄 Fluxo de funcionamento

```
Request → API → Service → Model → Banco
```

---

# ⚙️ Setup do Ambiente

## 1. Criar ambiente

### Windows

```
python -m venv venv
venv\Scripts\activate
```

### Linux/Mac

```
python -m venv venv
source venv/bin/activate
```

---

## 2. Instalar dependências

```
pip install django djangorestframework pydantic python-dotenv
```

---

## 3. Rodar projeto

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---

# 📦 Desenvolvimento de novos módulos

## Criar app

```
python manage.py startapp nome_app
```

Mover para:

```
apps/nome_app
```

Adicionar:

```
'apps.nome_app'
```

---

# 🧠 Dicionário de Termos (ESSENCIAL)

## 🔹 Serializer

Ferramenta do Django REST Framework usada para:

* Validar dados de entrada (JSON)
* Converter dados para resposta da API

👉 Ele protege sua aplicação contra dados inválidos vindos da requisição.

---

## 🔹 Service

Camada onde fica a  **regra de negócio** .

Exemplos:

* Dar baixa no estoque
* Validar operação
* Processar dados

👉 É o cérebro do sistema.

---

## 🔹 Model

Representa uma tabela no banco de dados.

Exemplo:

* Produto
* Movimentação

👉 Define a estrutura dos dados.

---

## 🔹 Selector

Funções responsáveis por buscar dados no banco.

👉 Evita duplicação de queries espalhadas pelo código.

---

## 🔹 View (API)

Camada que recebe a requisição HTTP.

Responsável por:

* Receber request
* Chamar service
* Retornar response

👉 Não deve conter regra de negócio.

---

## 🔹 Pydantic

Biblioteca usada para validar dados na camada de serviço.

👉 Garante que a regra de negócio receba dados corretos.

---

## 🔹 API

Interface que permite comunicação entre sistemas.

Exemplo:

* Frontend → Backend
* Tarugo → Dinabox

---

## 🔹 JSON

Formato padrão de troca de dados.

Exemplo:

```
{
  "produto_id": 1,
  "quantidade": 5
}
```

---

# 🧠 Conceitos Fundamentais

## 🔹 Por que separar em camadas?

Sem separação:

* Código vira bagunça
* Difícil manutenção
* Difícil escalar

Com separação:

* Código organizado
* Fácil evolução
* Fácil integração

---

## 🔹 Por que usar services?

Se colocar regra na view ou model:

❌ difícil testar
❌ difícil reutilizar
❌ alto acoplamento

Com service:

✅ reutilizável
✅ testável
✅ organizado

---

## 🔹 Por que modularizar (apps)?

Cada app representa um domínio:

* estoque
* crm
* integracoes

👉 Isso permite:

* crescer sem quebrar tudo
* trabalhar em partes isoladas
* transformar em SaaS no futuro

---

## 🔹 O que é desacoplamento?

É quando partes do sistema não dependem diretamente umas das outras.

👉 Benefícios:

* trocar partes sem quebrar tudo
* facilitar manutenção
* escalar sistema

---

## 🔹 O que é MVP?

Produto mínimo viável.

👉 No Tarugo:

* estoque
* login

Sem complexidade desnecessária.

---

# 🔐 Autenticação

Inicial:

* Django Auth padrão

Futuro:

* JWT
* Permissões por grupo

---

# 🔄 Integrações

Regra:

❌ Nunca chamar API direto na view
✅ Sempre usar services

---

# 📊 Boas práticas

* Não colocar lógica na view
* Services para regras
* Código simples
* Nomeação clara
* Pensar em evolução

---

# 🚀 Filosofia do Projeto

O Tarugo não é apenas um sistema interno.

É uma base para um produto SaaS do setor moveleiro.

Cada decisão deve considerar:

* Escalabilidade
* Reuso
* Integração futura

# 🧠 Padrão de Desenvolvimento (IMPORTANTE)

Toda nova funcionalidade deve seguir:

1. Criar Model (se necessário)
2. Criar Schema (Pydantic)
3. Criar Service
4. Criar Serializer
5. Criar View

---

# 🔥 Regra de Ouro

Se existir regra de negócio:

👉 Ela DEVE estar no service

---
# 🚀 Deploy com Docker em CT Proxmox (MVP PCP)

## Pré-requisitos no CT
- Docker e Docker Compose instalados
- Um diretório persistente para o projeto, de preferência com permissão de escrita para o usuário do Docker

## Rodar
1. Garanta que você tenha no diretório do projeto:
   - `db.sqlite3` (arquivo do banco)
   - `media/` (pasta onde o PCP grava os XLS gerados; se não existir, o compose vai criar ao subir)
2. Suba o container:
   ```bash
   docker compose up -d --build
   ```
3. Acesse:
   - `http://<IP_DO_CT>:8000/pcp/`

## Persistência
- `db.sqlite3` é persistido via volume: `./db.sqlite3:/app/db.sqlite3`
- Arquivos gerados pelo PCP são persistidos em `media/`, principalmente em `media/pcp/outputs`

## Arquivos Excel (XLS/XLSX)
- No seu uso atual do MVP PCP você envia apenas `CSV`.
- Por isso, nesta rodada, o deploy usa somente o `requirements.txt` atual.
- Se no futuro você precisar processar `XLS`/`XLSX`, aí sim adicione as dependências no `requirements.txt` e reconstrua a imagem.

## Smoke test (check rápido)
- Carregar a página: `GET /pcp/` e verificar se a tela abre
- Fluxo completo:
  - `POST /pcp/processar/` enviando um `CSV` válido
  - checar se o retorno JSON traz um `pid`
  - baixar o arquivo com `GET /pcp/download/<pid>/` e validar que chega um `.xls`

### Script Python (requests) para o smoke test
Ajuste `URL_BASE` e `CAMINHO_CSV`:
```python
import re
import requests

URL_BASE = "http://IP_DO_CT:8000"
CAMINHO_CSV = "seu_arquivo.csv"

session = requests.Session()
page = session.get(f"{URL_BASE}/pcp/")
page.raise_for_status()

m = re.search(r'id="csrf-token" value="([^"]+)"', page.text)
assert m, "CSRF token não encontrado"
csrf = m.group(1)

with open(CAMINHO_CSV, "rb") as f:
    resp = session.post(
        f"{URL_BASE}/pcp/processar/",
        files={"arquivo": f},
        data={"csrfmiddlewaretoken": csrf},
    )
resp.raise_for_status()
data = resp.json()
pid = data["pid"]

download = session.get(f"{URL_BASE}/pcp/download/{pid}/")
download.raise_for_status()

out_name = f"ROTEIRO_{pid}.xls"
with open(out_name, "wb") as out:
    out.write(download.content)

print("OK:", out_name)
```