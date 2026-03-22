#!/bin/bash

# Script de Deploy para Tarugo no Proxmox (LXC ou VM Ubuntu)

# 1. Atualizar sistema e instalar dependências
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose git

# 2. Clonar o repositório (substituir pela URL real)
# git clone https://github.com/seu-usuario/tarugo.git
# cd tarugo

# 3. Configurar variáveis de ambiente
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Arquivo .env criado. Por favor, edite-o com as configurações reais."
fi

# 4. Iniciar containers
sudo docker-compose up -d --build

# 5. Executar migrações e coletar arquivos estáticos
sudo docker-compose exec web python tarugo/manage.py migrate
sudo docker-compose exec web python tarugo/manage.py collectstatic --noinput

# 6. Criar superusuário inicial (opcional)
echo "Deseja criar um superusuário inicial? (s/n)"
read create_user
if [ "$create_user" == "s" ]; then
    sudo docker-compose exec web python tarugo/manage.py createsuperuser
fi

echo "Deploy concluído! Acesse a aplicação no IP do Proxmox na porta 8000."
