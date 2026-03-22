#!/bin/bash

# Script de Backup do Banco de Dados PostgreSQL (Tarugo)

# 1. Configurações
BACKUP_DIR="/home/ubuntu/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/tarugo_db_backup_$TIMESTAMP.sql"

# 2. Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

# 3. Executar o backup do container PostgreSQL
# Substituir 'db' pelo nome real do serviço no docker-compose.yml
# Substituir 'renara_db' pelo nome real do banco de dados
sudo docker-compose exec -T db pg_dump -U renara_user renara_db > $BACKUP_FILE

# 4. Compactar o backup
gzip $BACKUP_FILE

# 5. Limpar backups antigos (manter os últimos 7 dias)
find $BACKUP_DIR -name "tarugo_db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup concluído com sucesso: $BACKUP_FILE.gz"
