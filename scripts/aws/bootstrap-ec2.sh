#!/usr/bin/env bash
# Prepara una EC2 con Amazon Linux 2023: Docker + plugin Compose + Git.
# Uso (una sola vez, como ec2-user):  bash bootstrap-ec2.sh
set -euo pipefail

sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

# Plugin de Docker Compose v2 (no viene en los repositorios de AL2023).
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -fsSL "https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Swap de 1 GB: una t3.micro/t2.micro (1 GB de RAM) compila imágenes con holgura justa.
if ! swapon --show | grep -q swapfile; then
  sudo dd if=/dev/zero of=/swapfile bs=1M count=1024 status=none
  sudo chmod 600 /swapfile && sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "Listo. CIERRA la sesión SSH y vuelve a entrar (para aplicar el grupo docker), luego: docker compose version"
