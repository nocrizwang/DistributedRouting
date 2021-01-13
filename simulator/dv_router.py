"""
Your awesome Distance Vector router for CS 168

Based on skeleton code by:
  MurphyMc, zhangwen0411, lab352
"""

import sim.api as api
from cs168.dv import RoutePacket, \
                     Table, TableEntry, \
                     DVRouterBase, Ports, \
                     FOREVER, INFINITY

class DVRouter(DVRouterBase):

    # A route should time out after this interval
    ROUTE_TTL = 15

    # Dead entries should time out after this interval
    GARBAGE_TTL = 10

    # -----------------------------------------------
    # At most one of these should ever be on at once
    SPLIT_HORIZON = False
    POISON_REVERSE = False
    # -----------------------------------------------
    
    # Determines if you send poison for expired routes
    POISON_EXPIRED = False

    # Determines if you send updates when a link comes up
    SEND_ON_LINK_UP = False

    # Determines if you send poison when a link goes down
    POISON_ON_LINK_DOWN = False

    def __init__(self):
        """
        Called when the instance is initialized.
        DO NOT remove any existing code from this method.
        However, feel free to add to it for memory purposes in the final stage!
        """
        assert not (self.SPLIT_HORIZON and self.POISON_REVERSE), \
                    "Split horizon and poison reverse can't both be on"
        
        self.start_timer()  # Starts signaling the timer at correct rate.

        # Contains all current ports and their latencies.
        # See the write-up for documentation.
        self.ports = Ports()
        
        # This is the table that contains all current routes
        self.table = Table()
        self.table.owner = self
        self.history = {}

    def add_static_route(self, host, port):
        """
        Adds a static route to this router's table.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        self.table[host] = TableEntry(dst=host,port=port,latency=self.ports.get_latency(port),expire_time=FOREVER)
        self.send_routes()
        assert port in self.ports.get_all_ports(), "Link should be up, but is not."

        # TODO: fill this in!

    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        if packet.dst in self.table and self.table[packet.dst].latency<INFINITY:
            self.send(packet,self.table[packet.dst].port)
        # TODO: fill this in!

    def send_routes(self, force=False, single_port=None):
        """
        Send route advertisements for all routes in the table.

        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
               single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing.
        """
        
        for host,link in self.table.items():
            for each_port in self.ports.get_all_ports():
                if self.SPLIT_HORIZON and each_port == link.port:
                    continue
                if self.POISON_REVERSE and link.port == each_port:
                    latency = INFINITY
                else:
                    latency = link.latency
                if (force == True) or (link.dst not in self.history[each_port]) or (self.history[each_port][link.dst] != latency):
                    if (single_port == None) or (single_port == each_port):
                        self.send_route(each_port,link.dst,latency)
                        self.history[each_port][link.dst] = latency
            
        # TODO: fill this in!

    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        l = []
        for host,link in self.table.items():
            if api.current_time()>link.expire_time:
                self.s_log("Route from {} to {} is expired.",self,host)
                l.append(host)
        for to_delete in l:
            if self.POISON_EXPIRED:
                self.table[to_delete] = TableEntry(dst = to_delete,port = self.table[to_delete].port,latency = INFINITY, expire_time=api.current_time()+self.ROUTE_TTL)
                #self.send_routes()
            else:
                del self.table[to_delete]
        # TODO: fill this in!

    def handle_route_advertisement(self, route_dst, route_latency, port):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing.
        """
        if route_dst not in self.table or route_latency+self.ports.get_latency(port)<self.table[route_dst].latency or (port == self.table[route_dst].port and self.table[route_dst].latency<INFINITY):
            self.table[route_dst] = TableEntry(dst=route_dst,port=port,latency=min(INFINITY,route_latency+self.ports.get_latency(port)),expire_time=api.current_time()+self.ROUTE_TTL)
            self.send_routes()
        #elif route_dst in self.table and self.table[route_dst].latency!=INFINITY and route_latency == INFINITY:
        #    self.send_route(port,route_dst,self.table[route_dst].latency)
        
    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        self.history[port] = {}
        self.ports.add_port(port, latency)
        if self.SEND_ON_LINK_UP:
            self.send_routes(single_port = port)
        # TODO: fill in the rest!

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router does down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
        del self.history[port]
        self.ports.remove_port(port)
        if not self.POISON_ON_LINK_DOWN:
            return
        l = []
        for host,link in self.table.items():
            if link.port == port:
                self.s_log("Route from {} to {} is down.",self,host)
                l.append(host)
        for to_delete in l:
            self.table[to_delete] = TableEntry(dst = to_delete,port = self.table[to_delete].port,latency = INFINITY, expire_time=api.current_time()+self.ROUTE_TTL)
            self.send_routes()
            #del self.table[to_delete]
    # TODO: fill this in!

    # Feel free to add any helper methods!
