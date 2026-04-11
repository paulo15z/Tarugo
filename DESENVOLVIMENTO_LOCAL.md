# 🚀 Desenvolvimento Local - Guia Rápido

## ⚡ Opção 1: SQLite (MAIS RÁPIDO - Recomendado para começar)

Ideal para desenvolvimento rápido sem dependências externas.

```bash
# 1. Copie o arquivo .env.local para .env
cp .env.local .env

# 2. Limpe o banco anterior (opcional)
rm db.sqlite3

# 3. Rode as migrações
python manage.py migrate

# 4. Crie um superuser
python manage.py createsuperuser

# 5. Inicie o servidor
python manage.py runserver
```

✅ **Vantagens:** Rápido, sem dependências, funciona offline  
❌ **Desvantagens:** Não testa problemas específicos do PostgreSQL

---

## 🐳 Opção 2: PostgreSQL em Docker (MAIS REALISTA)

Ideal para testar no mesmo banco que a produção.

### Prerequisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado

### Passos

```bash
# 1. Inicie o PostgreSQL em Docker
docker-compose -f docker-compose.local.yml up -d

# 2. Verifique se está rodando
docker-compose -f docker-compose.local.yml ps

# 3. Copie o arquivo de configuração
cp .env.docker-local .env

# 4. Rode as migrações
python manage.py migrate

# 5. Crie um superuser
python manage.py createsuperuser

# 6. Inicie o servidor
python manage.py runserver
```

### Parar o Docker
```bash
docker-compose -f docker-compose.local.yml down
```

### Acessar o banco PostgreSQL diretamente
```bash
psql postgresql://tarugo:tarugo123@localhost:5432/tarugo_local
```

✅ **Vantagens:** Testa com PostgreSQL real, imita produção  
❌ **Desvantagens:** Requer Docker, um pouco mais lento

---

## 🔄 Alternando entre SQLite e PostgreSQL

```bash
# Para SQLite
cp .env.local .env

# Para PostgreSQL (com Docker)
cp .env.docker-local .env

# Depois atualize o banco
python manage.py migrate
python manage.py runserver
```

---

## 📝 Estrutura de Arquivos

- **`.env.local`** → SQLite local (sem dependências)
- **`.env.docker-local`** → PostgreSQL local (com Docker)
- **`docker-compose.local.yml`** → Configuração do Docker PostgreSQL
- **`.env`** → Arquivo que você copia um dos anteriores (não commit)

---

## ⚠️ Importante!

- **Nunca commit** `.env` - é específico de cada máquina
- **`.env.local` e `.env.docker-local`** podem ficar no repo (valores de exemplo)
- Para produção, use PostgreSQL remoto com credenciais seguras

---

## 🆘 Troubleshooting

### Erro "port 5432 already in use"
```bash
# Verifique qual container está usando
docker ps | grep 5432

# Pare o container
docker stop tarugo_db_local
```

### Erro de conexão PostgreSQL
```bash
# Verifique se o Docker está rodando
docker-compose -f docker-compose.local.yml ps

# Check logsa
docker-compose -f docker-compose.local.yml logs db
```

### Erro de migração
```bash
# Force reset (CUIDADO - apaga dados!)
python manage.py migrate estoque zero
python manage.py migrate
```
