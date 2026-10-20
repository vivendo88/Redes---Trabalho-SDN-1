#!/usr/bin/env bash
set -e

mkdir -p logs

echo "=========================================================="
echo " Validando permissao sudo para o Mininet...               "
echo "=========================================================="
sudo -v

source .venv/bin/activate

TOPOLOGIAS=("linear" "star" "ring" "tree" "mesh")

for topo in "${TOPOLOGIAS[@]}"; do
    arq="topo_${topo}.txt"
    png="topologia_${topo}_descoberta.png"
    ryu_log="logs/ryu_${topo}.log"
    mn_log="logs/mininet_${topo}.log"

    echo ""
    echo "=========================================================="
    echo " Testando topologia: ${arq} -> ${png}"
    echo "=========================================================="

    sudo mn -c > /dev/null 2>&1 || true

    # Inicia o controlador Ryu em background com nome de PNG especifico
    TOPO_OUTPUT_PNG="${png}" ryu-manager --observe-links topo_discover.py > "${ryu_log}" 2>&1 &
    RYU_PID=$!
    sleep 2

    # Executa a topologia no Mininet em modo batch (encerra automaticamente apos os ARPs)
    sudo python3 topologia.py "${arq}" --batch > "${mn_log}" 2>&1 || true

    # Encerra o controlador Ryu
    kill "${RYU_PID}" 2>/dev/null || true
    wait "${RYU_PID}" 2>/dev/null || true

    echo " -> Log do Ryu salvo em:     ${ryu_log}"
    echo " -> Log do Mininet salvo em: ${mn_log}"
    echo " -> Grafo PNG gerado em:     ${png}"
done

sudo mn -c > /dev/null 2>&1 || true
echo ""
echo "=========================================================="
echo " Bateria de testes concluida com sucesso!                 "
echo "=========================================================="
