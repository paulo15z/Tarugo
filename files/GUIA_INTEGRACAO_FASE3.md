# GUIA DE INTEGRAÇÃO — FASE 3: INGESTÃO DE DADOS

## 📋 O QUE FOI CRIADO

✅ **Modelos Django** (Cliente → Ambiente → Módulo → Peça)
✅ **Importador Dinabox** (CSV → Banco de dados)
✅ **API de Bipagem** (POST /api/producao/bipagem/)
✅ **Admin Django** (Gerenciamento completo)
✅ **Management Command** (CLI para importação)

---

## 🚀 PASSO 1: CRIAR O APP PRODUCAO

```bash
python manage.py startapp producao apps/producao
```

---

## 🚀 PASSO 2: COPIAR OS ARQUIVOS

### 2.1 - Models (arquivo principal)
Copie o conteúdo de `/home/claude/models_producao.py` para:
```
apps/producao/models.py
```

### 2.2 - Importador
Crie a pasta `apps/producao/services/` e copie:
```
apps/producao/services/__init__.py  (vazio)
apps/producao/services/importador_dinabox.py
```
Copie de: `/home/claude/importador_dinabox.py`

### 2.3 - API (serializers)
Crie a pasta `apps/producao/api/` e copie:
```
apps/producao/api/__init__.py  (vazio)
apps/producao/api/serializers.py
apps/producao/api/views.py
apps/producao/api/urls.py
```
De: `/home/claude/serializers_producao.py`, `/home/claude/views_producao.py`, `/home/claude/urls_producao.py`

### 2.4 - Admin
Copie para:
```
apps/producao/admin.py
```
De: `/home/claude/admin_producao.py`

### 2.5 - Management Command
Crie a pasta `apps/producao/management/commands/` e copie:
```
apps/producao/management/__init__.py  (vazio)
apps/producao/management/commands/__init__.py  (vazio)
apps/producao/management/commands/importar_dinabox.py
```
De: `/home/claude/importar_dinabox_command.py`

---

## 🚀 PASSO 3: REGISTRAR O APP

Em `config/settings.py`, adicione a `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... apps existentes ...
    'apps.producao',
]
```

---

## 🚀 PASSO 4: CRIAR AS MIGRATIONS

```bash
python manage.py makemigrations producao
python manage.py migrate producao
```

Output esperado:
```
Migrations for 'producao':
  apps/producao/migrations/0001_initial.py
    - Create model Cliente
    - Create model Ambiente
    - Create model Modulo
    - Create model Peca
    - Create model EventoBipagem

Operations to perform:
  Apply all migrations: producao
Running migrations:
  Applying producao.0001_initial... OK
```

---

## 🚀 PASSO 5: REGISTRAR AS URLS

Em `config/urls.py`, adicione:

```python
from django.urls import path, include

urlpatterns = [
    # ... urls existentes ...
    path('api/producao/', include('apps.producao.api.urls')),
]
```

---

## 🚀 PASSO 6: IMPORTAR OS DADOS

### Opção A: Via Command Line (recomendado)

```bash
python manage.py importar_dinabox /home/claude/0253294319_-_CLOSET_MASTER_-_573_-_SÉRGIO_POSSENTI_-_02-04-2026.csv
```

Output esperado:
```
⏳ Importando dados do Dinabox...

✅ Importação concluída: 762 peças em XX módulos
   Cliente: SÉRGIO POSSENTI
   Ambiente: SUÍTE HÓSPEDES (Lote 573)
   Total de peças: 762
   Total de módulos: 15
```

### Opção B: Via API

```bash
curl -X POST http://localhost:8000/api/producao/importar/ \
  -F "arquivo=@/path/to/arquivo.csv"
```

---

## 🎯 PASSO 7: TESTAR AS APIS

### 1. Buscar peça específica

```bash
curl http://localhost:8000/api/producao/peca/10167150/
```

Response:
```json
{
  "id": 1,
  "id_peca": "10167150",
  "descricao": "Base Torre D Guarda Roupa",
  "local": "Caixa",
  "status": "PENDENTE",
  "largura_mm": 601.0,
  "altura_mm": 1055.0,
  "espessura_mm": 15.0,
  "quantidade": 1,
  "material": "Branco TX",
  "modulo_nome": "M10175926 — Torre D Guarda Roupa",
  "cliente_nome": "SÉRGIO POSSENTI",
  "numero_lote": "525770",
  "data_bipagem": null,
  "bipagens": []
}
```

### 2. Registrar bipagem

```bash
curl -X POST http://localhost:8000/api/producao/bipagem/ \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "10167150",
    "usuario": "João da Silva",
    "localizacao": "Máquina COR-01"
  }'
```

Response:
```json
{
  "ok": true,
  "mensagem": "Peça 10167150 bipada com sucesso",
  "peca": {
    "id": 1,
    "status": "BIPADA",
    "data_bipagem": "2026-04-02T14:30:45.123456Z",
    "bipagens": [
      {
        "id": 1,
        "momento": "2026-04-02T14:30:45.123456Z",
        "usuario": "João da Silva",
        "localizacao": "Máquina COR-01"
      }
    ]
  }
}
```

### 3. Ver ambiente (lote)

```bash
curl http://localhost:8000/api/producao/ambiente/573/
```

Response:
```json
{
  "ambiente": {
    "id": 1,
    "numero_lote": "573",
    "nome_ambiente": "SUÍTE HÓSPEDES",
    "total_pecas": 762,
    "pecas_bipadas": 5,
    "percentual_concluido": 1
  },
  "modulos": [
    {
      "id": 1,
      "referencia_modulo": "M10175926",
      "nome_modulo": "Torre D Guarda Roupa",
      "total_pecas": 45,
      "pecas_bipadas": 2,
      "percentual_concluido": 4
    }
  ],
  "resumo": {
    "total": 762,
    "bipadas": 5,
    "pendentes": 757,
    "percentual": 1
  }
}
```

### 4. Buscar peças por termo

```bash
curl "http://localhost:8000/api/producao/buscar/?q=Torre"
```

---

## 📊 PASSO 8: ACESSAR O ADMIN

1. Acesse: `http://localhost:8000/admin/`
2. Navegue para **Produção**
3. Veja:
   - **Clientes** (SÉRGIO POSSENTI)
   - **Ambientes** (SUÍTE HÓSPEDES — Lote 573)
   - **Módulos** (Torre D Guarda Roupa, etc)
   - **Peças** (todas as 762)
   - **Eventos de Bipagem** (log de todas as bipagens)

---

## 📱 PASSO 9: CRIAR FRONTEND BIPAGEM (PRÓXIMA ETAPA)

Criar uma interface web simples:
- Input de scanner/teclado
- Feedback visual (✅ OK ou ❌ ERRO)
- Contador de progresso
- Status em tempo real

---

## 🔧 ESTRUTURA FINAL

```
apps/
├── producao/                    # 🆕 APP NOVO
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py      # Auto-gerada
│   ├── management/              # 🆕
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── importar_dinabox.py  # Management command
│   ├── services/                # 🆕
│   │   ├── __init__.py
│   │   └── importador_dinabox.py    # Lógica de importação
│   ├── api/                     # 🆕
│   │   ├── __init__.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── __init__.py
│   ├── admin.py                 # 🆕 Completo com visual
│   ├── models.py                # 🆕 Cliente/Ambiente/Módulo/Peça
│   ├── apps.py
│   └── tests.py
```

---

## 🎯 ESTRUTURA DE DADOS (IMPORTADA)

### Exemplo com seus dados:

```
Cliente: SÉRGIO POSSENTI
  ├─ Ambiente: SUÍTE HÓSPEDES (Lote 573)
  │   ├─ Módulo: M10175926 (Torre D Guarda Roupa)
  │   │   ├─ Peça 10167150: Base Torre D Guarda Roupa [Caixa] — PENDENTE
  │   │   ├─ Peça 10167148: Chapeu [Caixa] — PENDENTE
  │   │   ├─ Peça 10191248: Direita - Sem puxador - Reta [Porta] — PENDENTE
  │   │   └─ ... (mais peças do módulo)
  │   ├─ Módulo: M10176573 (Torre D Guarda Roupa)
  │   └─ ... (mais módulos)
```

---

## ✅ CHECKLIST FINAL

- [ ] App `producao` criado
- [ ] Models copiados e rodado makemigrations
- [ ] Migrations aplicadas
- [ ] Importador em `services/`
- [ ] API em `api/`
- [ ] Admin configurado
- [ ] Management command criado
- [ ] URLs registradas em `config/urls.py`
- [ ] Arquivo CSV importado via command
- [ ] Admin acessível e com dados
- [ ] APIs testadas (GET peca, POST bipagem, etc)

---

## 🚨 PRÓXIMAS FASES

**FASE 3.1 — Frontend de Bipagem**
- Interface web para scan de código
- Feedback visual em tempo real
- Dashboard de progresso

**FASE 3.2 — Integração com PCP**
- Quando PCP processa, cria Peças automaticamente
- Quando Peça é bipada, atualiza PCP

**FASE 3.3 — Estoque Inteligente**
- Usar peças bipadas para avisar compras
- Previsão de consumo

---

## 📞 TROUBLESHOOTING

### "Coluna não encontrada"
Verifique que o CSV tem exatamente essas colunas:
- NOME DO CLIENTE
- LOTE
- NOME DO PROJETO
- REFERÊNCIA DA PEÇA
- ID DA PEÇA
- DESCRIÇÃO DA PEÇA
- LOCAL
- (e outras dimensões)

### "Peça já existe"
O importador verifica `unique_together = ('modulo', 'id_peca')`.
Para reimportar, delete a Ambiente e tente novamente.

### "Erro de encoding"
O parser tenta UTF-8, CP1252 e LATIN-1. Se falhar, abra o CSV com Excel e salve como UTF-8.
