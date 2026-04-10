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

if [ ! -f .env ]; then
  echo "Arquivo .env não encontrado. Copie .env.example para .env e ajuste as credenciais."
  exit 1
fi

echo "Subindo apenas o banco para aguardar disponibilidade..."
$COMPOSE up -d db

echo "Aguardando PostgreSQL ficar pronto..."
for i in $(seq 1 30); do
  if $COMPOSE exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
    echo "PostgreSQL pronto."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Timeout aguardando PostgreSQL."
    exit 1
  fi
  sleep 2
done

echo "Build da imagem..."
$COMPOSE build web

echo "Executando bootstrap idempotente (migrate + seeds)..."
$COMPOSE run --rm web sh ./bootstrap/99_bootstrap_all.sh

echo "Subindo Tarugo..."
$COMPOSE up -d --no-build

echo "Status do container:"
$COMPOSE ps

echo "Logs recentes (ultimas ~100 linhas):"
$COMPOSE logs --tail=100

