# Guia de Configuração de Ambiente no Proxmox - Tarugo v1.1

Este guia detalha os comandos e configurações essenciais para a implantação do ambiente Tarugo v1.1 no Proxmox, utilizando Containers (CTs) baseados em Alpine Linux, Docker, PostgreSQL, Redis, Celery e Nginx. O objetivo é fornecer um passo a passo claro para a configuração de cada componente da infraestrutura.

## Nota de segurança

- Nunca coloque senhas reais no repositório
- Use `.env.example` como base e crie um `.env` local
- Prefira `DEBUG=0` fora do desenvolvimento

## 1. Pré-requisitos

*   Proxmox VE instalado e configurado.
*   Acesso SSH ao servidor Proxmox.
*   Conhecimento básico de Linux, Docker e PostgreSQL.

## 2. Criação dos Containers (CTs) no Proxmox

Recomenda-se criar os seguintes CTs no Proxmox, utilizando o template Alpine Linux para otimização de recursos. Os exemplos abaixo assumem IDs de CTs arbitrários; ajuste conforme sua necessidade.

### 2.1. CT Base (Alpine Linux)

Para cada serviço (Aplicação, PostgreSQL, Redis, Celery Worker, Nginx), crie um novo CT. O template Alpine é leve e ideal para Docker.

**Comando de Exemplo (via CLI do Proxmox ou Web UI):**

```bash
pct create <CT_ID> local:vztmpl/alpine-3.19-default_20240307_amd64.tar.xz \
  --hostname <nome_do_host> \
  --memory <RAM_MB> \
  --swap <SWAP_MB> \
  --rootfs local-lvm:<DISK_GB> \
  --cores <NUM_CORES> \
  --net0 name=eth0,bridge=vmbr0,ip=<IP_ESTATICO>/24,gw=<GATEWAY> \
  --unprivileged 1
```

**Exemplo de Configuração Sugerida:**

| Serviço             | CT ID | Hostname         | RAM (MB) | SWAP (MB) | Disco (GB) | Cores | IP Estático      |
|---------------------|-------|------------------|----------|-----------|------------|-------|------------------|
| **Aplicação Tarugo**| 101   | `tarugo-app`     | 2048     | 512       | 20         | 2     | `192.168.1.101`  |
| **PostgreSQL**      | 102   | `tarugo-db`      | 1024     | 256       | 50         | 1     | `192.168.1.102`  |
| **Redis**           | 103   | `tarugo-redis`   | 512      | 256       | 10         | 1     | `192.168.1.103`  |
| **Celery Worker**   | 104   | `tarugo-worker`  | 1024     | 256       | 20         | 1     | `192.168.1.104`  |
| **Nginx**           | 105   | `tarugo-nginx`   | 512      | 256       | 10         | 1     | `192.168.1.105`  |

**Observações:**

*   Ajuste `CT_ID`, `hostname`, `RAM_MB`, `SWAP_MB`, `DISK_GB`, `NUM_CORES`, `IP_ESTATICO` e `GATEWAY` conforme seu ambiente e recursos disponíveis.
*   `--unprivileged 1` é recomendado para segurança, mas pode exigir ajustes se houver necessidade de acesso a recursos privilegiados dentro do CT.

## 3. Configuração Básica do Alpine Linux (em cada CT)

Após criar e iniciar cada CT, acesse-o via `pct enter <CT_ID>` ou SSH e execute os seguintes comandos:

```bash
# Atualizar o sistema
apk update && apk upgrade

# Instalar pacotes essenciais
apk add bash curl git openssh-server sudo

# Habilitar e iniciar SSH (opcional, mas recomendado para acesso fácil)
rc-update add sshd
service sshd start

# Adicionar um usuário sudo (se necessário, para evitar usar root diretamente)
adduser <seu_usuario>
adduser <seu_usuario> wheel
visudo # Descomente a linha '%wheel ALL=(ALL) ALL' para permitir sudo
```

## 4. Instalação do Docker (nos CTs de Aplicação, Celery Worker e Nginx)

No CT da Aplicação (`tarugo-app`), Celery Worker (`tarugo-worker`) e Nginx (`tarugo-nginx`):

```bash
# Instalar Docker e Docker Compose
apk add docker docker-compose

# Iniciar e habilitar o serviço Docker
rc-update add docker boot
service docker start

# Adicionar seu usuário ao grupo docker para executar comandos sem sudo
adduser <seu_usuario> docker
# Saia e entre novamente no CT para que as mudanças de grupo tenham efeito
```

## 5. Configuração do PostgreSQL (no CT `tarugo-db`)

No CT do PostgreSQL (`tarugo-db`):

```bash
# Instalar PostgreSQL
apk add postgresql postgresql-client

# Inicializar o banco de dados
su - postgres -c "initdb --locale en_US.UTF-8 -D /var/lib/postgresql/data"

# Habilitar e iniciar o serviço PostgreSQL
rc-update add postgresql
service postgresql start

# Criar usuário e banco de dados para o Tarugo
su - postgres -c "psql" <<EOF
CREATE USER tarugo WITH PASSWORD 'sua_senha_segura';
CREATE DATABASE tarugo_db OWNER tarugo;
\q
EOF

# Configurar acesso remoto (opcional, mas necessário se a aplicação estiver em outro CT)
# Edite /var/lib/postgresql/data/postgresql.conf
# listen_addresses = '*' # ou o IP do CT do PostgreSQL
# Edite /var/lib/postgresql/data/pg_hba.conf
# host    all             all             0.0.0.0/0               md5
# Reinicie o PostgreSQL após as alterações
service postgresql restart
```

## 6. Configuração do Redis (no CT `tarugo-redis`)

No CT do Redis (`tarugo-redis`):

```bash
# Instalar Redis
apk add redis

# Habilitar e iniciar o serviço Redis
rc-update add redis
service redis start

# (Opcional) Configurar persistência e segurança, editando /etc/redis.conf
# requirepass sua_senha_segura
# bind 0.0.0.0 # Se precisar de acesso de outros CTs
# Reinicie o Redis após as alterações
service redis restart
```

## 7. Implantação da Aplicação Tarugo (no CT `tarugo-app`)

No CT da Aplicação (`tarugo-app`):

1.  **Clonar o Repositório:**
    ```bash
git clone https://github.com/paulo15z/Tarugo.git /opt/tarugo
cd /opt/tarugo
    ```

2.  **Ajustar `docker-compose.yml`:** O arquivo da raiz do projeto já deve apontar para PostgreSQL via `DATABASE_URL` e não deve mais montar `db.sqlite3`.
    *   O serviço `web` deve ler as variáveis do `.env`.
    *   As credenciais não devem ficar hardcoded no compose.
    *   O volume de SQLite deve ser removido definitivamente.

    **Exemplo de trecho adaptado para `docker-compose.yml` (simplificado):**

    ```yaml
services:
  db:
    image: postgres:16-alpine
    env_file:
      - .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: sh -c "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"
    env_file:
      - .env
    volumes:
      - .:/app
      - media_data:/app/media
      - static_data:/app/staticfiles
    ports:
      - "8000:8000"
    environment:
      - DEBUG=0
    depends_on:
      - db

volumes:
  postgres_data:
  media_data:
  static_data:
    ```

    **Nota:** No ambiente Proxmox, o PostgreSQL normalmente roda no CT `tarugo-db`, enquanto a aplicação fica no CT `tarugo-app`. Se você optar por um único `docker-compose.yml` local, o padrão acima já funciona com banco em container.

3.  **Configurar Variáveis de Ambiente:** Crie um arquivo `.env` na raiz do projeto (`/opt/tarugo/.env`) com as variáveis de ambiente necessárias, como `DJANGO_SETTINGS_MODULE`, `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, etc.

    ```ini
DJANGO_SETTINGS_MODULE=config.settings
DATABASE_URL=postgresql://tarugo:sua_senha_segura@192.168.1.102:5432/tarugo_db
SECRET_KEY=sua_secret_key_aqui
DEBUG=0
DJANGO_ALLOWED_HOSTS=192.168.1.101,seu_dominio.com
CSRF_TRUSTED_ORIGINS=http://192.168.1.101
POSTGRES_DB=tarugo_db
POSTGRES_USER=tarugo
POSTGRES_PASSWORD=sua_senha_segura
DEFAULT_PASSWORD=Trocar123!
RESET_PASSWORDS=0
RUN_ESTOQUE_SEEDS=0
DINABOX_SERVICE_USERNAME=preencha_se_usar_integracao
DINABOX_SERVICE_PASSWORD=preencha_se_usar_integracao
    ```

4.  **Build e Execução:**
    ```bash
docker compose up -d db
docker compose run --rm web sh ./bootstrap/99_bootstrap_all.sh
docker compose up -d web
    ```

    **Nota:** Para um ambiente de produção, é recomendado usar um orquestrador como Kubernetes ou Docker Swarm, ou um sistema de gerenciamento de processos como `systemd` para o container Docker.

## 8. Configuração do Nginx (no CT `tarugo-nginx`)

No CT do Nginx (`tarugo-nginx`):

1.  **Instalar Nginx:**
    ```bash
apk add nginx
    ```

2.  **Configurar Nginx:** Crie um arquivo de configuração para o seu site em `/etc/nginx/conf.d/tarugo.conf`.

    ```nginx
server {
    listen 80;
    server_name seu_dominio.com 192.168.1.105;

    location /static/ {
        alias /var/www/tarugo/static/;
    }

    location /media/ {
        alias /var/www/tarugo/media/;
    }

    location / {
        proxy_pass http://192.168.1.101:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
    ```

    **Nota:** Você precisará montar os volumes de `static` e `media` do CT da aplicação no CT do Nginx, ou configurar o Django para servir esses arquivos de um serviço de armazenamento de objetos (S3, etc.). Para simplificar, pode-se usar `scp` ou `rsync` para copiar os arquivos estáticos e de mídia para o Nginx após o `collectstatic` do Django.

3.  **Habilitar e Iniciar Nginx:**
    ```bash
rc-update add nginx
service nginx start
    ```

## 9. Configuração do Celery Worker (no CT `tarugo-worker` - Futuro)

No CT do Celery Worker (`tarugo-worker`):

1.  **Clonar o Repositório:**
    ```bash
git clone https://github.com/paulo15z/Tarugo.git /opt/tarugo
cd /opt/tarugo
    ```

2.  **Configurar Variáveis de Ambiente:** Crie um arquivo `.env` similar ao da aplicação, mas com foco nas configurações do Celery e Redis.

3.  **Build e Execução do Worker:**
    ```bash
docker build -t tarugo-worker .
docker run -d --name celery-worker --env-file .env tarugo-worker celery -A config worker -l info
    ```

    **Nota:** A configuração do Celery (`config.celery.py` ou similar) precisará ser criada no projeto Tarugo para definir as tarefas e o broker (Redis).

## 10. Considerações Finais

*   **Segurança:** Sempre utilize senhas fortes e gerencie-as de forma segura (ex: variáveis de ambiente, HashiCorp Vault).
*   **Monitoramento:** Implemente ferramentas de monitoramento para acompanhar a saúde e performance de cada CT e serviço.
*   **Backup:** Configure rotinas de backup para o PostgreSQL e outros dados críticos.
*   **CI/CD:** Considere a implementação de um pipeline de CI/CD para automatizar o deploy e as atualizações.

## Referências

[1] Proxmox VE Documentation: [https://pve.proxmox.com/pve-docs/](https://pve.proxmox.com/pve-docs/)
[2] Docker Documentation: [https://docs.docker.com/](https://docs.docker.com/)
[3] PostgreSQL Documentation: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)
[4] Redis Documentation: [https://redis.io/docs/](https://redis.io/docs/)
[5] Nginx Documentation: [https://nginx.org/en/docs/](https://nginx.org/en/docs/)
[6] Celery Documentation: [https://docs.celeryq.dev/en/stable/](https://docs.celeryq.dev/en/stable/)
