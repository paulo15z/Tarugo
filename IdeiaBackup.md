# IdeiaBackup

## 🎯 Objetivo
Garantir:
- Segurança dos dados
- Backup automático diário
- Base pronta para crescimento (saindo do SQLite)

---

# 🧱 1. Problema atual (SQLite)

O SQLite é simples e ótimo para desenvolvimento, mas em produção apresenta limitações:

- ❌ Problemas com concorrência
- ❌ Risco maior de corrupção
- ❌ Backup manual ou limitado
- ❌ Escalabilidade praticamente inexistente

👉 Conclusão: deve ser substituído conforme o sistema cresce.

---

# 🚀 2. Migração para banco robusto

## 🥇 Opção recomendada: PostgreSQL

Motivos:
- Alta confiabilidade
- Suporte nativo a concorrência
- Ferramentas robustas de backup
- Integração perfeita com Django

---

## 🔧 Passo a passo (Django)

### 1. Instalar dependência

```bash
pip install psycopg2-binary
```

---

### 2. Subir PostgreSQL via Docker

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

### 3. Configurar Django

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'app',
        'USER': 'user',
        'PASSWORD': 'password',
        'HOST': 'db',
        'PORT': '5432',
    }
}
```

---

### 4. Migrar dados do SQLite

```bash
python manage.py dumpdata > data.json
python manage.py migrate
python manage.py loaddata data.json
```

---

# 💾 3. Backup automático diário (Google Drive)

## 🧠 Estratégia

1. Gerar backup local
2. Salvar com timestamp
3. Enviar para Google Drive
4. (Opcional) limpar backups antigos

---

## 🥇 Opção recomendada: rclone (mais simples)

### 1. Instalar

```bash
sudo apt install rclone
```

---

### 2. Configurar

```bash
rclone config
```

- Escolher Google Drive
- Fazer login
- Nome: `gdrive`

---

### 3. Script de backup

`backup.sh`

```bash
#!/bin/bash

DATA=$(date +%Y-%m-%d_%H-%M-%S)
PASTA=./backups

mkdir -p $PASTA

# Backup PostgreSQL
pg_dump -U user -h localhost app > $PASTA/db_$DATA.sql

# Enviar para Google Drive
rclone copy $PASTA gdrive:backups

# Limpar backups locais antigos (7 dias)
find $PASTA -type f -mtime +7 -delete
```

---

### 4. Automatizar (cron)

```bash
crontab -e
```

Backup diário às 02:00:

```bash
0 2 * * * /caminho/backup.sh
```

---

# 🔐 4. Boas práticas

## 🔁 Backup

- Sempre manter histórico (não sobrescrever)
- Testar restore periodicamente
- Manter cópia fora do servidor
- Usar compressão (.gz) se crescer muito

---

## 🧯 Segurança

- Nunca versionar banco no Git
- Proteger credenciais
- Usar variáveis de ambiente

---

## ⚙️ Produção

- Monitorar tamanho dos backups
- Definir retenção (ex: 7 ou 30 dias)
- Validar integridade

---

# 🔄 5. Restore (recuperação)

## PostgreSQL

```bash
psql -U user -d app < backup.sql
```

---

# 🎯 Conclusão

Para sair do modo "risco":

1. Migrar SQLite → PostgreSQL
2. Implementar backup automático
3. Enviar para Google Drive

👉 Isso já coloca seu sistema em nível de produção confiável.

