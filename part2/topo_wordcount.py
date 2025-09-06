"""
Custom Mininet topology for Part 2: (N clients) -- (1 switch) -- (1 server)
"""
from mininet.topo import Topo

class Part2Topo(Topo):
    "Star topology for Part 2 with N clients and 1 server."

    def build(self, n_clients=2):
        # Add a single switch
        switch = self.addSwitch('s1')

        # Add the server host
        server = self.addHost('h_server')
        self.addLink(server, switch)

        # Add N client hosts
        for i in range(1, n_clients + 1):
            client_host = self.addHost(f'h_client{i}')
            self.addLink(client_host, switch)

def make_net(n_clients=2):
    """Factory function to create the network for experiments."""
    from mininet.net import Mininet
    from mininet.log import setLogLevel
    setLogLevel('info')

    topo = Part2Topo(n_clients=n_clients)
    # Important: We need to use the 'host' link to ensure the server's IP is predictable
    # The first host added ('h_server') will get 10.0.0.1
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    return net

if __name__ == '__main__':
    # This part is for debugging and allows you to run the topology directly
    from mininet.cli import CLI
    from mininet.link import TCLink
    from mininet.node import CPULimitedHost

    net = make_net(n_clients=4)
    net.start()
    print("Topology running. Server is h_server (10.0.0.1). Clients are h_client1, etc.")
    CLI(net)
    net.stop()
