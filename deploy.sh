#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker não encontrado no CT. Instale o Docker antes de rodar este script."
  exit 1
fi

# Compatibilidade: alguns CTs usam 'docker compose', outros 'docker-compose'
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "docker compose/docker-compose não encontrado. Instale o Docker Compose plugin."
  exit 1
fi

echo "Preparando persistências..."
mkdir -p media/pcp/outputs
mkdir -p media

if [ ! -f db.sqlite3 ]; then
  echo "Criando db.sqlite3 (será inicializado via migrations)..."
  touch db.sqlite3
fi

echo "Subindo Tarugo (build + migrações + servidor)..."
$COMPOSE up -d --build

echo "Status do container:"
$COMPOSE ps

echo "Logs recentes (últimas ~100 linhas):"
$COMPOSE logs --tail=100

