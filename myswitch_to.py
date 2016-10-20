#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from threading import Timer, Thread, Event
import time

def switchy_main(net):

    my_interfaces = net.interfaces() 
    mymacs = [intf.ethaddr for intf in my_interfaces]

    cache = timeoutCache(10)

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
        cache.dump()

    net.shutdown()


class timeoutCache:
    def __init__(self, timeoutSeconds):
        self.dstMap = {}
        self.dstTimer = {}
        self.timeoutSeconds = timeoutSeconds
        #self.refresh()

    def refresh(self):
        self.dump()
        self.refreshThread = Timer(1, self.refresh)
        self.refreshThread.start()


    def dump(self):
        if(not self.dstMap):
            log_debug("timeoutCache is empty")
        else:
            log_debug("dumping dstMap in timeoutCache:")
            for dst in self.dstMap:
                log_debug(str(dst) + " -> " + str(self.dstMap[dst]))
        log_debug("")

    def contains(self, dst):
        return dst in self.dstMap

    def get(self, dst):
        if dst in self.dstMap:
            return self.dstMap[dst]
        else:
            raise KeyError("timeoutCache.get - given dst is not in cache")

    def set(self, dst, dev):
        if dst in self.dstTimer:
            self.dstTimer[dst].cancel()
        self.dstTimer[dst] = Timer(self.timeoutSeconds, self.remove, [dst])
        self.dstTimer[dst].start()

        if not self.contains(dst) or not dev == self.dstMap[dst]:   #same op for new/update
            self.dstMap[dst] = dev

    def remove(self, dst):
        log_debug("removing " + str(dst))
        if dst in self.dstMap:
            del self.dstMap[dst]
            self.dstTimer[dst].cancel()
            del self.dstTimer[dst]
        else:
            raise KeyError("remove - given dst is not in dstMap or dstElaspedTime")


