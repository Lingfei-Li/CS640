#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''

import sys
import os
import time
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

class Router(object):
    def __init__(self, net):
        self.net = net
        self.ipHWMap = {}
        # other initialization stuff here
        my_intf = net.interfaces()
        for intf in my_intf:
            self.ipHWMap[intf.ipaddr] = intf.ethaddr
        log_debug(self.ipHWMap)


    def router_main(self):    
        while True:
            gotpkt = True
            try:
                dev,pkt = self.net.recv_packet(timeout=1.0)
            except NoPackets:
                log_debug("No packets available in recv_packet")
                gotpkt = False
            except Shutdown:
                log_debug("Got shutdown signal")
                break

            if gotpkt:
                arp = pkt.get_header(Arp)
                ''' ARP '''
                if arp is not None:
                    ''' Handling ARP Request '''
                    if arp.operation == ArpOperation.Request:
                        targetIP = arp.targetprotoaddr
                        log_info("ARP request for IP=" + str(targetIP))
                        if arp.targetprotoaddr in self.ipHWMap:
                            log_info('yes')
                            targetHW = self.ipHWMap[arp.targetprotoaddr]
                            arpReply = create_ip_arp_reply( 
                                    arp.senderhwaddr, 
                                    targetHW,
                                    arp.senderprotoaddr,
                                    arp.targetprotoaddr);
                            self.net.send_packet(dev, arpReply)
                        else:
                            ''' Ignore ARP request that is not targeted at out interfaces'''
                            pass
                    else:
                        ''' Ignore ARP Reply '''
                        pass
                else:
                    #TODO
                    pass






def switchy_main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()
