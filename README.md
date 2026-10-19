# Descoberta de Topologias de Rede com Mininet, Ryu e NetworkX

Este projeto implementa a instanciação dinâmica de topologias de Redes Definidas por Software (SDN) no **Mininet** a partir de listas de arestas e o mapeamento automático completo da topologia (switches, enlaces LLDP e hosts via *Gratuitous ARP*) utilizando o controlador **Ryu** (OpenFlow 1.3) e visualização gráfica com **NetworkX**.

---

## Estrutura do Projeto

- `topologia.py`: Script do Mininet que lê um arquivo de lista de arestas, instancia os switches (OpenFlow 1.3), cria 1 host por switch e dispara pacotes *Gratuitous ARP* (`arping`).
- `topo_discover.py`: Aplicação do controlador Ryu que descobre switches e enlaces via LLDP (`--observe-links`), intercepta pacotes ARP via `PacketIn`, exibe a topologia completa no console e exporta o grafo da rede em PNG usando NetworkX e Matplotlib.
- `topo_triangle.txt`: Arquivo de definição da topologia de teste *Triangle* (3 switches em anel).
- `topo_someloops.txt`: Arquivo de definição da topologia de teste *Someloops* (6 switches com múltiplos ciclos).
- `install.sh` e `requirements.txt`: Scripts para instalação automatizada das dependências de sistema e criação do ambiente virtual Python isolado (`.venv`).
- `relatorio.tex`: Código-fonte LaTeX do relatório técnico do trabalho.

---

## 1. Configuração e Instalação

O projeto foi preparado para execução em **Ubuntu / Debian** (incluindo Ubuntu Server e WSL2). Como o controlador `ryu==4.34` exige Python 3.9 e versões específicas do `setuptools` e `eventlet`, o script de instalação configura tudo automaticamente dentro de um ambiente virtual isolado (`.venv`).

### Instalação Automatizada (Recomendado)

Na raiz do projeto, dê permissão de execução ao script `install.sh` e execute-o:

```bash
chmod +x install.sh
./install.sh
```

O script realizará automaticamente as seguintes etapas:
1. Instalação dos pacotes de sistema via `apt` (`mininet`, `openvswitch-switch`, `iputils-arping`, `net-tools`, etc.).
2. Inicialização do serviço `openvswitch-switch`.
3. Criação do ambiente virtual `.venv` com **Python 3.9** (via `uv`).
4. Instalação das dependências do `requirements.txt` (`ryu`, `eventlet`, `networkx`, `matplotlib`, `ovs`) dentro da `.venv`.

---

## 2. Como Executar o Projeto

Para executar os experimentos, você precisará de **dois terminais** abertos na pasta do projeto.

### Passo 1: Iniciar o Controlador Ryu (Terminal 1)

Ative o ambiente virtual `.venv` e inicie o `ryu-manager` com a flag `--observe-links` (necessária para a injeção de pacotes LLDP e descoberta de enlaces entre switches):

```bash
source .venv/bin/activate
ryu-manager --observe-links topo_discover.py
```

### Passo 2: Instanciar a Topologia no Mininet (Terminal 2)

No segundo terminal, execute o script `topologia.py` com `sudo` passando o arquivo da topologia desejada:

#### Opção A: Topologia *Triangle*
```bash
sudo python3 topologia.py topo_triangle.txt
```
- **Saída gráfica gerada:** `topologia_triangulo_descoberta.png`

#### Opção B: Topologia *Someloops*
```bash
sudo python3 topologia.py topo_someloops.txt
```
- **Saída gráfica gerada:** `topologia_someloops_descoberta.png`

---

## 3. Encerrando e Limpando o Ambiente

Para encerrar a emulação no terminal do Mininet (`mininet>`), digite:

```text
mininet> exit
```

Caso alguma execução seja interrompida abruptamente e você precise limpar as interfaces virtuais e configurações residuais do Open vSwitch antes de um novo teste, execute:

```bash
sudo mn -c
```

---

## Autores

- **Uálaci dos Anjos Júnior**
- **Jefferson Johnson**
