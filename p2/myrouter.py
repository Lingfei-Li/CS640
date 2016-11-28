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
        self.queueSeq = 0               #seq number for next queue item
        self.queuePendingARP = {}    #packets pending ARP reply
        self.intfByName = {}

        # build forwarding table & router interface map
        for intf in net.interfaces():
            self.localIpMacMap[intf.ipaddr] = intf.ethaddr
            log_info(intf.ipaddr)
            fwdEntry = [IPv4Network('{}/{}'.format(intf.ipaddr, intf.netmask), strict=False), None, intf.name]
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


    def addToPendingQueue(self, pkt, nextIP, nextDev):
        if nextIP in self.queuePendingARP:
            self.queuePendingARP[nextIP].add(pkt)
        else:
            self.queueSeq += 1
            self.queuePendingARP[nextIP] = PktsPendingARP(pkt, nextIP, nextDev, self.queueSeq)

    def printQueue(self):
        for key in list(self.queuePendingARP.keys()):
            print(key, self.queuePendingARP[key].retry)
               
    def printFwdTable(self):
        print("Forwarding Table:")
        for fwdEntry in self.fwdTable:
            print(fwdEntry)

    def fwdTableLookup(self, ipaddr):
        ''' longest prefix match '''
        log_info("looking up for ipaddr " + str(ipaddr))
        maxLen = 0
        ansEntry = None
        for fwdEntry in self.fwdTable:
            if ipaddr in fwdEntry[0]:
                if fwdEntry[0].prefixlen > maxLen:
                    maxLen = fwdEntry[0].prefixlen
                    ansEntry = fwdEntry
        if ansEntry is None:
            log_info("No entry")
        else:
            log_info("Yes, found fwdEntry")
        return ansEntry

    def makeARPrequest(self, ipaddr, dev):
        log_info('making an ARP request for IP=' + str(ipaddr) + ' to port ' + dev)
        if dev in self.intfByName:
            intf = self.intfByName[dev]
            print("sending arp: ", intf.name, intf.ethaddr, intf.ipaddr, ipaddr)
            arpReq = create_ip_arp_request(intf.ethaddr, intf.ipaddr, ipaddr);
            self.net.send_packet(intf.name, arpReq)
        else:
            log_failure("No interface named" + dev + " found")

    def makeTTLExpiredICMP(self, pkt):
        fwdEntry = self.fwdTableLookup(pkt[IPv4].src)
        if fwdEntry is None:
            log_failure("fwdEntry is None when making TLE ICMP message")
        else:
            nextIP = fwdEntry[1]
            if nextIP is None:
                nextIP = pkt[IPv4].src  # Forwarding entry is from intf. dst directly connected
            nextDev = fwdEntry[2]

            mac = Ethernet()
            mac.src = self.intfByName[nextDev].ethaddr

            ip = IPv4()
            ip.src = self.intfByName[nextDev].ipaddr
            ip.dst = pkt[IPv4].src
            ip.ttl = 64

            icmp = ICMP()
            icmp.icmptype = ICMPType.TimeExceeded
            del pkt[pkt.get_header_index(Ethernet)]
            icmp.icmpdata.data = pkt.to_bytes()[:28]
            icmp.icmpdata.origdgramlen = len(pkt)
            print(str(icmp))

            ttlExpiredMsg = mac + ip + icmp
            self.prepareToSend(ttlExpiredMsg, nextIP, nextDev)

    def makeEchoReply(self, echoReq):
        ''' forward entry lookup. request's src as reply's dst  '''
        fwdEntry = self.fwdTableLookup(echoReq[IPv4].src)
        if fwdEntry is None:
            log_failure("fwdEntry not found when replying echo")
        else:
            nextIP = fwdEntry[1]
            if nextIP is None:
                nextIP = echoReq[IPv4].src  # Forwarding entry is from intf. dst directly connected
            nextDev = fwdEntry[2]

            mac = Ethernet()
            mac.src = self.intfByName[nextDev].ethaddr

            ip = IPv4()
            ip.src = echoReq[IPv4].dst
            ip.dst = echoReq[IPv4].src
            ip.ttl = 64

            icmp = ICMP()
            icmp.icmptype = ICMPType.EchoReply
            icmp.icmpdata.identifier = echoReq[ICMP].icmpdata.identifier
            icmp.icmpdata.sequence = echoReq[ICMP].icmpdata.sequence
            icmp.icmpdata.data = echoReq[ICMP].icmpdata.data

            echoReply = mac + ip + icmp

            self.prepareToSend(echoReply, nextIP, nextDev)


    def makeHostUnreachableError(self, pkt):
        fwdEntry = self.fwdTableLookup(pkt[IPv4].src)   #send icmp back to sender
        if fwdEntry is not None:
            nextIP = fwdEntry[1]
            nextDev = fwdEntry[2]
            if nextIP is None:
                nextIP = pkt[IPv4].src      # Forwarding entry is from intf. dst directly connected

            mac = Ethernet()
            mac.src = self.intfByName[nextDev].ethaddr

            ip = IPv4()
            ip.src = self.intfByName[nextDev].ipaddr
            ip.dst = pkt[IPv4].src
            ip.ttl = 64

            icmp = ICMP()
            icmp.icmptype = ICMPType.DestinationUnreachable
            icmp.icmpcode = ICMPTypeCodeMap[icmp.icmptype].HostUnreachable
            del pkt[pkt.get_header_index(Ethernet)]
            icmp.icmpdata.data = pkt.to_bytes()[:28]
            icmp.icmpdata.origdgramlen = len(pkt)
            
            icmpErrMsg = mac + ip + icmp

            print("host unreachable error packet:")
            print(icmpErrMsg)

            log_info("ready to send unreachable error")
            self.prepareToSend(icmpErrMsg, nextIP, nextDev)

        else: # No forwarding entry found in fwdTable
            log_failure("No fowarding entry found for icmp error message")

    def makeNoFwdEntryErr(self, pkt):
        fwdEntry = self.fwdTableLookup(pkt[IPv4].src)   #send icmp back to sender
        if fwdEntry is not None:
            nextIP = fwdEntry[1]
            nextDev = fwdEntry[2]
            if nextIP is None:
                nextIP = pkt[IPv4].src      # Forwarding entry is from intf. dst directly connected

            mac = Ethernet()
            mac.src = self.intfByName[nextDev].ethaddr

            ip = IPv4()
            ip.src = self.intfByName[nextDev].ipaddr
            ip.dst = pkt[IPv4].src
            ip.ttl = 64

            icmp = ICMP()
            icmp.icmptype = ICMPType.DestinationUnreachable
            icmp.icmpcode = ICMPTypeCodeMap[icmp.icmptype].NetworkUnreachable
            print("ETHER HEADER INDEX: " + str(pkt.get_header_index(Ethernet)))
            del pkt[pkt.get_header_index(Ethernet)]
            icmp.icmpdata.data = pkt.to_bytes()[:28]
            icmp.icmpdata.origdgramlen = len(pkt)
            
            icmpErrMsg = mac + ip + icmp

            print("host unreachable error packet:")
            print(icmpErrMsg)

            log_info("ready to send unreachable error")
            self.prepareToSend(icmpErrMsg, nextIP, nextDev)

        else: # No forwarding entry found in fwdTable
            log_failure("No fowarding entry found for icmp error message")

    def makeNonHandleableErr(self, pkt):
        fwdEntry = self.fwdTableLookup(pkt[IPv4].src)   #send icmp back to sender
        if fwdEntry is not None:
            nextIP = fwdEntry[1]
            nextDev = fwdEntry[2]
            if nextIP is None:
                nextIP = pkt[IPv4].src      # Forwarding entry is from intf. dst directly connected

            mac = Ethernet()
            mac.src = self.intfByName[nextDev].ethaddr

            ip = IPv4()
            ip.src = self.intfByName[nextDev].ipaddr
            ip.dst = pkt[IPv4].src
            ip.ttl = 64

            icmp = ICMP()
            icmp.icmptype = ICMPType.DestinationUnreachable
            icmp.icmpcode = ICMPTypeCodeMap[icmp.icmptype].PortUnreachable
            del pkt[pkt.get_header_index(Ethernet)]
            icmp.icmpdata.data = pkt.to_bytes()[:28]
            icmp.icmpdata.origdgramlen = len(pkt)
            
            icmpErrMsg = mac + ip + icmp

            print("host unreachable error packet:")
            print(icmpErrMsg)

            log_info("ready to send unreachable error")
            self.prepareToSend(icmpErrMsg, nextIP, nextDev)

        else: # No forwarding entry found in fwdTable
            log_failure("No fowarding entry found for icmp error message")



    def checkPendingQueue(self):
        log_info("checking pending queue")
        self.printQueue()
        for key, item in sorted(list(self.queuePendingARP.items()), key=lambda x:x[1].seq): #sort by sequence
            if item.outdated():
                if item.retryLimitReached():
                    log_warn("Retry limit reached")
                    for pkt in item.pkts:
                        self.makeHostUnreachableError(pkt)
                    del self.queuePendingARP[key]
                    self.checkPendingQueue()
                    return
                else:
                    log_info("Sending ARP request for a pending pkt. retry cnt: " + str(item.retry))
                    ''' resend and update counter&timer '''
                    self.makeARPrequest(item.nextIP, item.nextDev)
                    item.arpSent()


    def sendPacketWithEth(self, pkt, dev, nextMac):
        ''' forward the packet (received from others) '''
        log_info("sending a packet from {} to {}".format(pkt[IPv4].src, pkt[IPv4].dst))
        ''' Change Ethernet header: src is router interface, dst is next hop (not dst)  '''
        pkt[Ethernet].src = self.intfByName[dev].ethaddr
        pkt[Ethernet].dst = nextMac

        print("Packet to send:")
        print(pkt)
        
        self.net.send_packet(dev, pkt)



    def prepareToSend(self, pkt, nextIP, nextDev):
        if nextIP in self.remoteIpMacMap:
            ''' Already have ip-mac map. forward it '''
            self.sendPacketWithEth(pkt, nextDev, self.remoteIpMacMap[nextIP])
        else:
            log_info("add a packet to queue with nextIP=" + str(nextIP))
            ''' Don't know MAC address yet. Add to queue and wait for ARP reply '''
            self.addToPendingQueue(pkt, nextIP, nextDev)
        

    def router_main(self):    
        while True:

            self.checkPendingQueue() 

            gotpkt = True
            try:
                dev,pkt = self.net.recv_packet(timeout=0.1)
            except NoPackets:
                log_debug("No packets available in recv_packet")
                gotpkt = False
            except Shutdown:
                log_debug("Got shutdown signal")
                break

            if gotpkt:
                log_info("Router Running...")
                arp = pkt.get_header(Arp)

                if arp is not None:
                    ''' ARP '''

                    ''' Update IP-MAC mapping ''' 
                    print("update remoteIpMacMap: " + str(arp.senderprotoaddr)+"-"+str(arp.senderhwaddr))
                    self.remoteIpMacMap[arp.senderprotoaddr] = arp.senderhwaddr


                    if arp.operation == ArpOperation.Request:
                        ''' ARP Request Received '''

                        ''' Check dst IP '''
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
                            ''' Ignore ARP request that is not targeted at our interfaces'''
                            pass
                    else:
                        ''' ARP Reply Received '''

                        ''' forward all corresponding packets queued '''
                        if arp.senderprotoaddr in self.queuePendingARP:
                            queueItem = self.queuePendingARP[arp.senderprotoaddr]
                            for pkt in queueItem.pkts:
                                self.sendPacketWithEth(pkt, queueItem.nextDev, self.remoteIpMacMap[queueItem.nextIP])
                            del self.queuePendingARP[arp.senderprotoaddr]
                        else:
                            log_warn("ARP reply's IP doesn't match with any queued item")

                else:   
                    ''' Non-ARP Packet '''
                    log_info("Packet Is Not ARP")
                    dstIP = pkt[IPv4].dst
                    fwdEntry = self.fwdTableLookup(dstIP)

                    if fwdEntry is not None:
                        pkt[IPv4].ttl -= 1
                        if pkt[IPv4].ttl > 0:
                            ''' Forwarding Entry Found '''
                            log_info("Fowarding entry found.")
                            print(fwdEntry)
                            nextIP = fwdEntry[1]
                            nextDev = fwdEntry[2]

                            if dstIP in self.localIpMacMap:
                                icmp = pkt.get_header(ICMP)
                                if icmp is not None and icmp.icmptype == ICMPType.EchoRequest:
                                    ''' Echo Request for the router. Make reply '''
                                    self.makeEchoReply(pkt)

                                else: # Packet is for the router, but not ICMP echo request
                                    log_warn("non-EchoRequest packet for router")
                                    self.makeNonHandleableErr(pkt)
                            else:
                                ''' Packet for others. Forward it '''
                                log_debug("packet for someone else. try to forward it")
                                if nextIP is None:
                                    nextIP = pkt[IPv4].dst      # Forwarding entry is from intf. dst directly connected

                                self.prepareToSend(pkt, nextIP, nextDev)
                        else: # TTL < 0
                            log_warn("TTL < 0")
                            self.makeTTLExpiredICMP(pkt)
                    else: # No forwarding entry found in fwdTable
                        log_info("No fowarding entry found. Drop the packet")
                        self.makeNoFwdEntryErr(pkt)


class PktsPendingARP:
    def __init__(self, pkt, nextIP, nextDev, seq):
        self.pkts = [pkt]
        self.retry = 0
        self.arpSentTime = -1
        self.nextIP = nextIP 
        self.nextDev = nextDev
        self.seq = seq

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
