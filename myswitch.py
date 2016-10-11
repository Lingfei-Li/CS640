#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
import lruCache 

def switchy_main(net):

    my_interfaces = net.interfaces() 
    mymacs = [intf.ethaddr for intf in my_interfaces]

    cache = lruCache.lruCache()

    while True:
        print("")
        try:
            dev,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return

        print("In {}, on port '{}' received packet {}".format(net.name, packet, dev))
        if packet[0].dst in mymacs:
            print("Packet intended for me")
        else:
            if cache.contains(packet[0].dst):
                outDev = cache.get(packet[0].dst)
                print("src in cache: " + outDev)
                print("Sending packet {} to {}".format(packet, outDev))
                net.send_packet(outDev, packet)
            else:
                print("flooding")
                for intf in my_interfaces:
                    if dev != intf.name:
                        print("Flooding packet {} to {}".format(packet, intf.name))
                        net.send_packet(intf.name, packet)
            if not cache.contains(packet[0].src):
                print("Caching {} -> {}".format(packet[0].src, dev))
                cache.set(packet[0].src, dev)
    net.shutdown()
