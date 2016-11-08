#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''

import sys
import os
import time
from queue import Queue
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

class Router(object):
    def __init__(self, net):
        self.net = net
        self.remoteIpMacMap = {}        #IP-Eth mapping for other nodes
        self.localIpMacMap = {}         #IP-Eth mapping for the router's interfaces
        self.fwdTable = []              #forwarding table <ip_network, next_ip, eth_name>
        self.queuePendingARP = {}    #packets pending ARP reply
        self.intfByName = {}

        # build forwarding table & router interface map
        for intf in net.interfaces():
            self.localIpMacMap[intf.ipaddr] = intf.ethaddr
            fwdEntry = [IPv4Network('{}/{}'.format(intf.ipaddr, intf.netmask), strict=False), intf.ipaddr, '']
            log_debug(fwdEntry)
            self.fwdTable.append(fwdEntry)
            self.intfByName[intf.name] = intf

        # build forwarding table from file
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

    def makeARPrequest(self, ipaddr, dev):
        log_info('making an ARP request for IP ' + str(ipaddr) + ' to port ' + dev)
        if dev in self.intfByName:
            intf = self.intfByName[dev]
            print("sending arp: ", intf.name, intf.ethaddr, intf.ipaddr, ipaddr)
            arpReq = create_ip_arp_request(intf.ethaddr, intf.ipaddr, ipaddr);
            self.net.send_packet(intf.name, arpReq)
        else:
            log_failure("No interface named" + dev + " found")


    def checkPendingQueue(self):
        log_info("checking pending queue")
        for key, item in list(self.queuePendingARP.items()):
            if item.retryLimitReached():
                log_info("Retry limit reached")
                del self.queuePendingARP[key]
            else:
                if item.outdated():
                    log_info("Sending ARP request for a pending pkt")
                    ''' resend and update counter&timer '''
                    self.makeARPrequest(item.nextIP, item.nextDev)
                    item.arpSent()

    def forwardPacket(self, pkt, dev):
        nextIP = pkt[IPv4].dst
        log_info("forwarding a packet from {} to {}".format(pkt[IPv4].src, nextIP))
        if not nextIP in self.remoteIpMacMap:
            log_failure("IP-MAC mapping DNE for packet to be forwarded")
            return
        nextMac = self.remoteIpMacMap[nextIP]
        pkt[Ethernet].src = self.intfByName[dev].ethaddr
        pkt[Ethernet].dst = nextMac
        self.net.send_packet(dev, pkt)
        

    def router_main(self):    
        while True:
            print("Router Running...")

            self.checkPendingQueue()

            gotpkt = True
            try:
                dev,pkt = self.net.recv_packet(timeout=0.2)
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
                        ''' ARP Request '''
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
                        ''' ARP Reply '''

                        ''' Update mapping ''' 
                        self.remoteIpMacMap[arp.senderprotoaddr] = arp.senderhwaddr

                        ''' forward all corresponding packets queued '''
                        if arp.senderprotoaddr in self.queuePendingARP:
                            queueItem = self.queuePendingARP[arp.senderprotoaddr]
                            for pkt in queueItem.pkts:
                                self.forwardPacket(pkt, queueItem.nextDev)
                            del self.queuePendingARP[arp.senderprotoaddr]
                        else:
                            log_warn("ARP reply's IP doesn't match with any queued item")

                else:   
                    ''' Non-ARP Packet '''
                    log_info("Packet Is Not ARP")
                    fwdEntry = self.fwdTableLookup(pkt[IPv4].dst)

                    if fwdEntry is not None:
                        ''' Forwarding Entry Found '''
                        log_info("Fowarding entry found.")
                        nextIP = fwdEntry[1]
                        nextDev = fwdEntry[2]

                        if nextIP in self.localIpMacMap:
                            ''' Packet for the router. Just drop '''
                            log_info("packet for router. drop it")
                        else:
                            ''' Packet for others. Forward it '''
                            log_info("packet for someone else. try to forward it")
                            if nextIP in self.remoteIpMacMap:
                                ''' Already have ip-mac map. forward it '''
                                self.forwardPacket(pkt, nextDev)
                            else:
                                log_info("Don't have ip-mac map. Add to ARP pending queue!")
                                log_info("{} to {}".format(pkt[IPv4].src, pkt[IPv4].dst))

                                if nextIP in self.queuePendingARP:
                                    self.queuePendingARP[nextIP].add(pkt)
                                else:
                                    self.queuePendingARP[nextIP] = PktsPendingARP(pkt, nextIP, nextDev)
                    else:
                        ''' No forwarding entry. drop the packet '''
                        log_info("No fowarding entry found. Drop the packet")


class PktsPendingARP:
    def __init__(self, pkt, nextIP, nextDev):
        self.pkts = [pkt]
        self.retry = 0
        self.arpSentTime = -1
        self.nextIP = nextIP
        self.nextDev = nextDev

    def add(self, pkt):
        self.pkts.append(pkt)

    def outdated(self):
        return time.time() > self.arpSentTime + 1

    def arpSent(self):
        self.retry += 1
        self.arpSentTime = time.time()

    def retryLimitReached(self):
        return self.retry >= 5


def switchy_main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()
