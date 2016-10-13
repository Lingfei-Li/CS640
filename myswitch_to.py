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
        print("")
        try:
            dev,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
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


class timeoutCache:
    def __init__(self, timeoutSeconds):
        self.dstMap = {}
        self.dstElapsedTime = {}
        self.timeoutSeconds = timeoutSeconds
        self.refreshIntervalSeconds = 1
        self.startRefreshTask()

    def startRefreshTask(self):
        self.refreshCache()
        self.refreshThread = Timer(self.refreshIntervalSeconds, self.startRefreshTask)
        self.refreshThread.start()

    def stopRefreshTask(self):
        self.refreshThread.cancel()
    
    def refreshCache(self):
        self.dump()
        for dst, t in list(self.dstElapsedTime.items()):
            t += 1
            if t >= self.timeoutSeconds:
                self.remove(dst)
            else:
                self.dstElapsedTime[dst] = t

    def dump(self):
        if(not self.dstMap):
            print("timeoutCache is empty")
        else:
            print("dumping dstMap in timeoutCache:")
            for dst in self.dstMap:
                print(str(dst) + " -> " + str(self.dstMap[dst]))
        print("")

    def contains(self, dst):
        return dst in self.dstMap

    def get(self, dst):
        if dst in self.dstMap:
            return self.dstMap[dst]
        else:
            raise KeyError("timeoutCache.get - given dst is not in cache")

    def set(self, dst, dev):
        if not self.contains(dst) or not dev == self.dstMap[dst]:   #same for new/update
            self.dstMap[dst] = dev
            self.dstElapsedTime[dst] = 0

    def remove(self, dst):
        if dst in self.dstMap and dst in self.dstElapsedTime:
            del self.dstMap[dst]
            del self.dstElapsedTime[dst]
        else:
            raise KeyError("remove - given dst is not in dstMap or dstElaspedTime")


