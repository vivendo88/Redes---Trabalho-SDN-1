from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cl                                                    s
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
        self.hosts = {} # Estrutura: {ip: {'mac': mac, 'dpid': dpid, 'port': por                                                    t}}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Instala o fluxo padrao (table-miss) para encaminhar pacotes nao recon                                                    hecidos ao controlador."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Regra de prioridade 0 enviando para a porta do controlador
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCM                                                    L_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, action                                                    s)]

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
        self.logger.info("Switches mapeados atualmente: %s", self.switches)

    @set_ev_cls(event.EventLinkAdd)
    def _event_link_add_handler(self, ev):
        link_list = get_link(self.topology_api_app, None)
        self.links = [(link.src.dpid, link.dst.dpid, link.src.port_no, link.dst.                                                    port_no) for link in link_list]
        self.logger.info("Total de enlaces descobertos: %d", len(self.links))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        arp_pkt = pkt.get_protocol(arp.arp)

        if arp_pkt:
            self.logger.info("ARP recebido do IP %s, MAC %s no Switch %s, porta                                                     %s",
                             arp_pkt.src_ip, arp_pkt.src_mac, datapath.id, in_po                                                    rt)

            # Guarda as informacoes do host descoberto
            self.hosts[arp_pkt.src_ip] = {
                'mac': arp_pkt.src_mac,
                'dpid': datapath.id,
                'port': in_port
            }

            # Imprime a topologia completa no log
            self.print_full_topology()

    def print_full_topology(self):
        """Imprime a topologia completa mapeada."""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("           TOPOLOGIA COMPLETA MAPEADA            ")
        self.logger.info("=" * 50)

        # 1. Switches ativos
        self.logger.info("[SWITCHES ATIVOS]")
        if self.switches:
            for dpid in sorted(self.switches):
                self.logger.info(" -> Switch DPID: %s (s%d)", dpid, dpid)
        else:
            self.logger.info(" -> Nenhum switch detectado.")

        # 2. Enlaces entre switches
        self.logger.info("\n[ENLACES ENTRE SWITCHES]")
        if self.links:
            for src_dpid, dst_dpid, src_port, dst_port in self.links:
                self.logger.info(" -> Switch %s (porta %s) <---> Switch %s (port                                                    a %s)",
                                 src_dpid, src_port, dst_dpid, dst_port)
        else:
            self.logger.info(" -> Nenhum enlace detectado.")

        # 3. Hosts mapeados via ARP
        self.logger.info("\n[HOSTS CONECTADOS]")
        if self.hosts:
            for ip, info in self.hosts.items():
                self.logger.info(" -> IP: %s | MAC: %s | Conectado ao Switch: %s                                                     (porta %s)",
                                 ip, info['mac'], info['dpid'], info['port'])
        else:
            self.logger.info(" -> Nenhum host registrado.")

        self.logger.info("=" * 50 + "\n")
