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
        self.logger.info("Switches mapeados atualmente: %s", self.switches)

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
            
            self.hosts[arp_pkt.src_ip] = {
                'mac': arp_pkt.src_mac,
                'dpid': datapath.id,
                'port': in_port
            }
            
            self.print_full_topology()
            
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