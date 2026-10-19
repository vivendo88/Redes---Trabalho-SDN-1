#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " 1. Instalando dependências do sistema (Mininet e OVS)    "
echo "=========================================================="

sudo apt-get update
sudo apt-get install -y \
    curl \
    mininet \
    openvswitch-switch \
    openvswitch-common \
    iputils-arping \
    net-tools \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev

echo "=========================================================="
echo " 2. Iniciando o serviço do Open vSwitch                   "
echo "=========================================================="
sudo service openvswitch-switch start || sudo systemctl start openvswitch-switch

echo "=========================================================="
echo " 3. Criando ambiente virtual (.venv) com Python 3.9       "
echo "    (Necessário pois o Ryu 4.34 exige Python <= 3.9)      "
echo "=========================================================="
if ! command -v uv &> /dev/null && [ ! -f "$HOME/.local/bin/uv" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

# Cria a venv .venv baixando automaticamente o Python 3.9 isolado para o projeto
uv venv .venv --python 3.9 --seed

echo "=========================================================="
echo " 4. Instalando pacotes na .venv (requirements.txt)        "
echo "=========================================================="
./.venv/bin/pip install "setuptools<58.0.0" "pip<24.1" wheel
./.venv/bin/pip install --no-build-isolation -r requirements.txt

echo "=========================================================="
echo " Instalação concluída com sucesso!                        "
echo "=========================================================="
echo ""
echo "Como executar o projeto:"
echo ""
echo "  1. Ative a venv no terminal onde for rodar o Ryu:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Inicie o controlador Ryu (Terminal 1 - com a venv ativa):"
echo "     ryu-manager --observe-links topo_discover.py"
echo ""
echo "  3. Inicie a topologia no Mininet (Terminal 2):"
echo "     sudo python3 topologia.py topo_triangle.txt"
echo "     (ou: sudo python3 topologia.py topo_someloops.txt)"
