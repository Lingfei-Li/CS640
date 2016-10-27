#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from operator import itemgetter

def switchy_main(net):

    my_interfaces = net.interfaces() 
    mymacs = [intf.ethaddr for intf in my_interfaces]

    cache = lruCache()

    packetCache = {}
    packetCnt = 0

    while True:
        log_debug("")
        try:
            dev,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return

        log_debug("In {}, on port '{}' received packet:\n{}".format(net.name, dev, packet))

        #check and set/update src->dev mapping. should precede dst->dev map, according to QA
        cache.set(packet[0].src, dev)

        if packet[0].dst in mymacs:
            pass
        else:
            if cache.contains(packet[0].dst):
                outDev = cache.get(packet[0].dst)
                log_debug("Sending packet to {}".format(outDev))
                net.send_packet(outDev, packet)
            else:   #unknown dst or FF:..:FF
                for intf in my_interfaces:
                    if dev != intf.name:
                        log_debug("Flooding packet to {}".format(intf.name))
                        net.send_packet(intf.name, packet)
        cache.dumpSorted()

    net.shutdown()


class lruCache:
    def __init__(self):
        self.dstMap = {}
        self.freshness = {}
        self.limit = 5
        self.cnt = 0

    def dumpSorted(self):
        if not self.dstMap:
            log_debug("lruCache is empty")
        else:
            for dst, freshness in sorted(self.freshness.items(), key=itemgetter(1)):
                log_debug(str(dst) + " -> " + str(self.dstMap[dst]) + " fresh: " + str(freshness))

    def dump(self):
        if not self.dstMap:
            log_debug("lruCache is empty")
        else:
            log_debug("dumping dstMap in lruCache:")
            for dst in self.dstMap:
                log_debug(str(dst) + " -> " + str(self.dstMap[dst]) + " fresh: " + str(self.freshness[dst]))
        log_debug("")

    def contains(self, dst):
        return dst in self.dstMap

    def get(self, dst):
        if dst in self.dstMap:          #return mapped port and upadte to most recently used
            self.freshness[dst] = self.getFreshness()
            return self.dstMap[dst]
        else:
            raise KeyError("lruCache.get - given dst is not in cache")

    def set(self, dst, dev):
        if not self.contains(dst):      #DNE. insert
            log_debug("DNE")
            while len(self.dstMap) >= self.limit:       #table full
                self.kickLRU() 
            self.freshness[dst] = self.getFreshness() #add (dst, dev) as most recently used
            self.dstMap[dst] = dev
        else:                           #exists. update
            log_debug("Exists")
            if not dev == self.dstMap[dst]:
                self.dstMap[dst] = dev         #update port info w/o modifying LRU order

    def kickLRU(self):
        lruDst = None
        lruFreshness = -1
        for dst, fresh in self.freshness.items():
            if lruFreshness == -1 or lruFreshness > fresh:
                lruDst = dst
                lruFreshness = fresh
        if not lruFreshness == -1:
            self.remove(lruDst)

    def remove(self, dst):
        if dst in self.dstMap and dst in self.freshness:
            del self.dstMap[dst]
            del self.freshness[dst]
        else:
            raise KeyError("lruCache.remove - given dst is not in cache")

    def getFreshness(self):
        self.cnt += 1
        return self.cnt


