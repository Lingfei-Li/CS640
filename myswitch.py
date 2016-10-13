#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
import lruCache, timeCache

def switchy_main(net):

    my_interfaces = net.interfaces() 
    mymacs = [intf.ethaddr for intf in my_interfaces]

    cache = lruCache.lruCache()
    #cache = timeCache.timeCache(10)

    packetCache = {}
    packetCnt = 0

    while True:
        print("")
        try:
            dev,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            if isinstance(cache, timeCache.timeCache):  #stop refresh task for timeCache
                cache.stopRefreshTask()
            return

        print("In {}, on port '{}' received packet:\n{}".format(net.name, dev, packet))

        #check and set/update src->dev mapping. should precede dst->dev map, according to QA
        cache.set(packet[0].src, dev)

        if packet[0].dst in mymacs:
            pass
        else:
            if cache.contains(packet[0].dst):
                outDev = cache.get(packet[0].dst)
                print("Sending packet to {}".format(outDev))
                net.send_packet(outDev, packet)
            else:   #unknown dst or FF:..:FF
                for intf in my_interfaces:
                    if dev != intf.name:
                        print("Flooding packet to {}".format(intf.name))
                        net.send_packet(intf.name, packet)
        cache.dump()

    net.shutdown()
