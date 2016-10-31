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
        self.remoteIpMacMap = {}        #IP-Eth mapping for other nodes
        self.localIpMacMap = {}         #IP-Eth mapping for the router's interfaces
        self.fwdTable = []
        # other initialization stuff here
        my_intf = net.interfaces()
        for intf in my_intf:
            self.localIpMacMap[intf.ipaddr] = intf.ethaddr
            fwdEntry = [IPv4Network('{}/{}'.format(intf.ipaddr, intf.netmask), strict=False), intf.ipaddr, '']
            log_debug(fwdEntry)
            self.fwdTable.append(fwdEntry)


        ''' building forwarding table '''
        with open("forwarding_table.txt") as f:
            for line in f:
                entry = line.split()
                if len(entry) == 4:
                    fwdEntry = [IPv4Network('{}/{}'.format(entry[0], entry[1]), strict=False), IPv4Address(entry[2]), entry[3]]
                    self.fwdTable.append(fwdEntry)
                    log_debug(fwdEntry)
        self.printFwdTable()

               
    def printFwdTable(self):
        for fwdEntry in self.fwdTable:
            print(fwdEntry)

    def fwdTableLookup(self, ipaddr):
        log_info("looking up for ipaddr " + str(ipaddr))
        maxLen = 0
        ansEntry = None
        for fwdEntry in self.fwdTable:
            if ipaddr in fwdEntry[0]:
                if fwdEntry[0].prefixlen > maxLen:
                    maxLen = fwdEntry[0].prefixlen
                    ansEntry = fwdEntry
        return ansEntry

    def makeARPrequest(self, ipaddr):
        log_info('making an ARP request for IP ' + str(ipaddr))
        for intf in self.net.interfaces():
            print("sending arp: ", intf.name, intf.ethaddr, intf.ipaddr, ipaddr)
            arpReq = create_ip_arp_request(intf.ethaddr, intf.ipaddr, ipaddr);
            self.net.send_packet(intf.name, arpReq)


    def router_main(self):    
        while True:
            print("Router Running...")
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
                if arp is not None:
                    ''' ARP '''
                    if arp.operation == ArpOperation.Request:
                        ''' Handling ARP Request '''
                        targetIP = arp.targetprotoaddr
                        log_info("ARP request for IP=" + str(targetIP))
                        if arp.targetprotoaddr in self.localIpMacMap:
                            log_info('Replying ARP')
                            targetHW = self.localIpMacMap[arp.targetprotoaddr]
                            arpReply = create_ip_arp_reply( 
                                    targetHW,
                                    arp.senderhwaddr, 
                                    arp.targetprotoaddr,
                                    arp.senderprotoaddr);
                            self.net.send_packet(dev, arpReply)
                        else:
                            ''' Ignore ARP request that is not targeted at out interfaces'''
                            pass
                    else:
                        ''' Ignore ARP Reply '''
                        pass
                else:   
                    ''' Normal Packet. Forward the packet '''
                    log_info("Packet Is Not ARP")
                    fwdEntry = self.fwdTableLookup(pkt[IPv4].dst)
                    if fwdEntry is not None:
                        ''' Forwarding Entry Found '''
                        log_info("Fowarding entry found.")
                        nextIP = fwdEntry[1]
                        if nextIP in self.localIpMacMap:
                            ''' Packet for the router. Just drop '''
                            log_info("packet for router. drop it")
                            pass
                        else:
                            ''' Packet for others. Forward it '''
                            log_info("packet for someone else. try to forward it")
                            self.makeARPrequest(fwdEntry[1])
                    else:
                        ''' drop the packet '''
                        log_info("No fowarding entry found. Drop the packet")
                        pass



def switchy_main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()
