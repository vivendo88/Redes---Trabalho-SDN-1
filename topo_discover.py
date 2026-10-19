import networkx as nx
import matplotlib.pyplot as plt

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
from ryu.lib.packet import packet, arp

class TopoDiscover(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TopoDiscover, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.switches = []
        self.links = []
        self.hosts = {} # Estrutura: {ip: {'mac': mac, 'dpid': dpid, 'port': port}}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=0,
            match=match,
            instructions=inst
        )
        datapath.send_msg(mod)

    @set_ev_cls(event.EventSwitchEnter)
    def _event_switch_enter_handler(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        self.switches = [switch.dp.id for switch in switch_list]
        # Remove hosts de switches que não estão mais ativos
        self.hosts = {ip: info for ip, info in self.hosts.items() if info['dpid'] in self.switches}
        self.logger.info("Switches mapeados atualmente: %s", self.switches)

    @set_ev_cls(event.EventSwitchLeave)
    def _event_switch_leave_handler(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        self.switches = [switch.dp.id for switch in switch_list]
        link_list = get_link(self.topology_api_app, None)
        self.links = [(link.src.dpid, link.dst.dpid, link.src.port_no, link.dst.port_no) for link in link_list]
        # Limpa os hosts associados a switches que saíram da topologia
        self.hosts = {ip: info for ip, info in self.hosts.items() if info['dpid'] in self.switches}

    @set_ev_cls(event.EventLinkAdd)
    def _event_link_add_handler(self, ev):
        link_list = get_link(self.topology_api_app, None)
        self.links = [(link.src.dpid, link.dst.dpid, link.src.port_no, link.dst.port_no) for link in link_list]
        self.logger.info("Total de enlaces descobertos: %d", len(self.links))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        arp_pkt = pkt.get_protocol(arp.arp)

        if arp_pkt:
            self.logger.info("ARP recebido do IP %s, MAC %s no Switch %s, porta %s", 
                             arp_pkt.src_ip, arp_pkt.src_mac, datapath.id, in_port)
            
            # Remove registros antigos na mesma porta do switch (caso a rede tenha sido reiniciada)
            self.hosts = {
                ip: info for ip, info in self.hosts.items()
                if not (info['dpid'] == datapath.id and info['port'] == in_port) and info['dpid'] in self.switches
            }
            
            self.hosts[arp_pkt.src_ip] = {
                'mac': arp_pkt.src_mac,
                'dpid': datapath.id,
                'port': in_port
            }
            
            self.print_full_topology()
            self.salvar_grafo_descoberto()
            
    def salvar_grafo_descoberto(self, nome_arquivo=None):
        if nome_arquivo is None:
            if len(self.switches) == 3:
                nome_arquivo = "topologia_triangulo_descoberta.png"
            elif len(self.switches) == 6:
                nome_arquivo = "topologia_someloops_descoberta.png"
            else:
                nome_arquivo = "topologia_descoberta.png"

        G = nx.Graph()

        # Adiciona switches
        for dpid in self.switches:
            G.add_node(f"s{dpid}", tipo='switch')

        # Adiciona enlaces entre switches
        for src_dpid, dst_dpid, _, _ in self.links:
            G.add_edge(f"s{src_dpid}", f"s{dst_dpid}")

        # Adiciona hosts e suas ligações aos switches
        for ip, info in self.hosts.items():
            host_label = f"Host\n{ip}"
            sw_label = f"s{info['dpid']}"
            G.add_node(host_label, tipo='host')
            G.add_edge(host_label, sw_label)

        # Define as cores dos nós
        cores = ['lightblue' if G.nodes[n].get('tipo') == 'switch' else 'lightgreen' for n in G.nodes()]

        # Layout e renderização
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(
            G, pos,
            with_labels=True,
            node_color=cores,
            node_size=1000,
            font_size=8,
            font_weight='bold',
            edge_color='gray'
        )
        plt.title("Topologia Descoberta (Ryu Controller)")
        plt.savefig(nome_arquivo, bbox_inches='tight')
        plt.close()
        self.logger.info("Imagem do grafo salva em: %s", nome_arquivo)

    def print_full_topology(self):
        self.logger.info("\n" + "=" * 50)
        self.logger.info("           TOPOLOGIA COMPLETA MAPEADA            ")
        self.logger.info("=" * 50)

        self.logger.info("[SWITCHES ATIVOS]")
        for dpid in sorted(self.switches):
            self.logger.info(" -> Switch DPID: %s (s%d)", dpid, dpid)

        self.logger.info("\n[ENLACES ENTRE SWITCHES]")
        for src_dpid, dst_dpid, src_port, dst_port in self.links:
            self.logger.info(" -> Switch %s (porta %s) <---> Switch %s (porta %s)",
                             src_dpid, src_port, dst_dpid, dst_port)

        self.logger.info("\n[HOSTS CONECTADOS]")
        for ip, info in self.hosts.items():
            self.logger.info(" -> IP: %s | MAC: %s | Conectado ao Switch: %s (porta %s)",
                             ip, info['mac'], info['dpid'], info['port'])

        self.logger.info("=" * 50 + "\n")
