# #!/usr/bin/env python3

# from mininet.topo import Topo
# from mininet.net import Mininet
# from mininet.node import OVSSwitch
# from mininet.cli import CLI
# from mininet.log import setLogLevel
# from mininet.link import TCLink

# DEFAULT_CLIENTS = 10
# BANDWIDTH = 1        # Mbps
# DELAY = "5ms"        # example value, can be changed
# BUFFER_SIZE = 100    # packets

# class SimpleTopo(Topo):
#     "Star topology with 1 server, 10 clients, and 1 switch."

#     def __init__(self, num_clients=DEFAULT_CLIENTS):
#         Topo.__init__(self)

#         # Create switch
#         switch = self.addSwitch('s1', cls=OVSSwitch)

#         # Create server (fixed IP at .100 for clarity)
#         server = self.addHost('server', ip='10.0.0.100')

#         # Create clients
#         clients = []
#         for i in range(num_clients):
#             client_ip = f'10.0.0.{i+1}'
#             client = self.addHost(f'client{i+1}', ip=client_ip)
#             clients.append(client)

#         # Connect server to switch
#         self.addLink(server, switch, bw=BANDWIDTH, delay=DELAY, max_queue_size=BUFFER_SIZE)

#         # Connect each client to switch
#         for client in clients:
#             self.addLink(client, switch, bw=BANDWIDTH, delay=DELAY, max_queue_size=BUFFER_SIZE)


# def create_network(num_clients=DEFAULT_CLIENTS):
#     """Create and start the Part 2 network with hardcoded link params."""
#     topo = SimpleTopo(num_clients)
#     net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink)
#     net.start()
#     return net


# if __name__ == '__main__':
#     setLogLevel('info')

#     print(f"Creating network with {DEFAULT_CLIENTS} clients")
#     print(f"All links bandwidth: {BANDWIDTH} Mbps (hardcoded)")
#     print(f"All links delay: {DELAY}")
#     print(f"All links buffer: {BUFFER_SIZE} packets")

#     net = create_network()

#     print("Network created successfully!")
#     print("Hosts:", [h.name for h in net.hosts])
#     print("Links:", [(link.intf1.node, link.intf2.node) for link in net.links])

#     CLI(net)
#     net.stop()

#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink

class WordCountTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        h1 = self.addHost('h1', ip='10.0.0.100/24')
        h2 = self.addHost('h2', ip='10.0.0.1/24')
        self.addLink(h1, s1, cls=TCLink, bw=100)
        self.addLink(h2, s1, cls=TCLink, bw=100)

def make_net():
    return Mininet(topo=WordCountTopo(), controller=OVSController,
                   autoSetMacs=True, autoStaticArp=True)
