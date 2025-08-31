#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink

class WordCountTopo(Topo):
    def build(self, num_clients):  # allow variable number of clients
        s1 = self.addSwitch('s1')

        # Add server
        sv = self.addHost('sv', ip='10.0.0.1/24')
        self.addLink(sv, s1, cls=TCLink, bw=100)

        # Add variable number of clients
        for i in range(1, num_clients + 1):
            h = self.addHost(f'h{i}', ip=f'10.0.0.{i+1}/24')
            self.addLink(h, s1, cls=TCLink, bw=100)

def make_net(num_clients):
    return Mininet(
        topo=WordCountTopo(num_clients=num_clients),
        controller=OVSController,
        autoSetMacs=True,
        autoStaticArp=True
    )
