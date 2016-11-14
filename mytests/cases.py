import sys
import os
import time
from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent, PacketInputTimeoutEvent
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *



def init():
    ''' forwarding table:
        192.168.100.0 255.255.255.0 192.168.100.1 router-eth0
        192.168.200.0 255.255.255.0 192.168.200.1 router-eth1
        10.1.0.0      255.255.0.0   10.1.1.1      router-eth2
    '''

    s = Scenario("Router test item#2 item#3")
    s.add_interface('router-eth0', '40:00:00:00:00:01', '192.168.100.2')
    s.add_interface('router-eth1', '40:00:00:00:00:02', '192.168.200.2')
    s.add_interface('router-eth2', '40:00:00:00:00:03', '10.1.1.2')
    return s

def mkIPpkt(srcMac, srcIP, dstIP, dstMac="00:00:00:00:00:00"):
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = srcMac
    testpkt[0].dst = dstMac
    testpkt[1].src = srcIP
    testpkt[1].dst = dstIP
    return testpkt



def case2_1(s): #packet for the router get dropped
    testpkt = mkIPpkt( "10:00:00:00:00:01", "192.168.100.1", "192.168.100.2")
    s.expect(PacketInputEvent("router-eth0", testpkt, display=Ethernet), "packet from router-eth0 (server1) for router. should be dropped")


def case2_2(s): #forward packet. ARP request timeout
    testpkt = mkIPpkt( "10:00:00:00:00:01", "192.168.100.1", "192.168.200.1")
    s.expect(PacketInputEvent("router-eth0", testpkt, display=Ethernet), "server1 - server2. arrive at port router-eth0")

    arpReqPkt = create_ip_arp_request("40:00:00:00:00:02", "192.168.200.2", "192.168.200.1");

    s.expect(PacketOutputEvent("router-eth1", arpReqPkt, display=Ethernet), "1st ARP request to router-eth1 for 192.168.200.1(server2)")
    s.expect(PacketInputTimeoutEvent(1), "wait for 1s to timeout pending queue")
    s.expect(PacketOutputEvent("router-eth1", arpReqPkt, display=Ethernet), "2nd ARP request")
    s.expect(PacketInputTimeoutEvent(1), "wait for 1s to timeout pending queue")
    s.expect(PacketOutputEvent("router-eth1", arpReqPkt, display=Ethernet), "3rd ARP request")
    s.expect(PacketInputTimeoutEvent(1), "wait for 1s to timeout pending queue")
    s.expect(PacketOutputEvent("router-eth1", arpReqPkt, display=Ethernet), "4th ARP request")
    s.expect(PacketInputTimeoutEvent(1), "wait for 1s to timeout pending queue")
    s.expect(PacketOutputEvent("router-eth1", arpReqPkt, display=Ethernet), "5th ARP request")
    s.expect(PacketInputTimeoutEvent(1), "wait for 1s. After 5 retries, no more ARP should be sent")


def case2_3(s): #forward packet. ARP request ok
    # packet (s1 -> s2) arrives at the router
    testpkt = mkIPpkt( "10:00:00:00:00:01", "192.168.100.1", "192.168.200.1")
    s.expect(PacketInputEvent("router-eth0", testpkt, display=Ethernet), "server1 -> server2 from port router-eth0")

    # router makes ARP request. only send to the port in the forwarding table
    arpReqPkt = create_ip_arp_request("40:00:00:00:00:02", "192.168.200.2", "192.168.200.1");
    s.expect(PacketOutputEvent("router-eth1", arpReqPkt, display=Ethernet), "ARP request to router-eth1 for 192.168.200.1(server2)")

    # s2 replies
    server2ArpReply = create_ip_arp_reply("20:00:00:00:00:01", "40:00:00:00:00:02", "192.168.200.1", "192.168.200.2");
    s.expect(PacketInputEvent("router-eth1", server2ArpReply, display=Ethernet), "server2 ARP reply. arrive at port router-eth1")

    # router sets Ethernet header and forwards the packet to s2
    testpkt = mkIPpkt( "40:00:00:00:00:02", "192.168.100.1", "192.168.200.1", "20:00:00:00:00:01")
    s.expect(PacketOutputEvent("router-eth1", testpkt, display=Ethernet), "router sets Ethernet header and forwards the packet")

def case2_4(s): #two packets to forward. ARP reply order reverted
    # packet (s1 -> s2) arrives at the router-eth0
    fwd_pkt1 = mkIPpkt( "10:00:00:00:00:01", "192.168.100.1", "192.168.200.1")
    s.expect(PacketInputEvent("router-eth0", fwd_pkt1, display=Ethernet), "server1 -> server2 from port router-eth0")

    # router makes ARP request. only send to the port in the forwarding table
    arp_req1 = create_ip_arp_request("40:00:00:00:00:02", "192.168.200.2", "192.168.200.1");
    s.expect(PacketOutputEvent("router-eth1", arp_req1, display=Ethernet), "ARP request to router-eth1 for 192.168.200.1(server2)")

    # packet (s1 -> c) arrives at the router-eth0
    fwd_pkt2 = mkIPpkt( "10:00:00:00:00:01", "192.168.100.1", "10.1.1.1")
    s.expect(PacketInputEvent("router-eth0", fwd_pkt2, display=Ethernet), "server1 -> client from port router-eth0")

    # router makes ARP request. only send to the port in the forwarding table
    arp_req2 = create_ip_arp_request("40:00:00:00:00:03", "10.1.1.2", "10.1.1.1");
    s.expect(PacketOutputEvent("router-eth2", arp_req2, display=Ethernet), "ARP request to router-eth2 for 10.1.1.1 (client)")

    # client replies ARP (before s2)
    arp_rep_client = create_ip_arp_reply("30:00:00:00:00:01", "40:00:00:00:00:03", "10.1.1.1", "10.1.1.2");
    s.expect(PacketInputEvent("router-eth2", arp_rep_client, display=Ethernet), "client ARP reply. arrive at port router-eth2")

    # router sets Ethernet header and forwards the packet to client
    fwd_pkt2 = mkIPpkt( "40:00:00:00:00:03", "192.168.100.1", "10.1.1.1", "30:00:00:00:00:01")
    s.expect(PacketOutputEvent("router-eth2", fwd_pkt2, display=Ethernet), "router sets Ethernet header and forwards the packet to client")

    # s2 replies ARP
    server2ArpReply = create_ip_arp_reply("20:00:00:00:00:01", "40:00:00:00:00:02", "192.168.200.1", "192.168.200.2");
    s.expect(PacketInputEvent("router-eth1", server2ArpReply, display=Ethernet), "server2 ARP reply. arrive at port router-eth1")

    # router sets Ethernet header and forwards the packet to s2
    fwd_pkt1 = mkIPpkt( "40:00:00:00:00:02", "192.168.100.1", "192.168.200.1", "20:00:00:00:00:01")
    s.expect(PacketOutputEvent("router-eth1", fwd_pkt1, display=Ethernet), "router sets Ethernet header and forwards the packet")


def case2_5(s): #three packets with the same destination. Only 1 ARP req should be sent
    # packet1 (s1 -> s2) arrives at the router-eth0
    fwd_pkt1 = mkIPpkt( "10:00:00:00:00:01", "192.168.100.1", "192.168.200.1")
    s.expect(PacketInputEvent("router-eth0", fwd_pkt1, display=Ethernet), "server1 -> server2 from port router-eth0")
    
    # router makes ARP request. only send to the port in the forwarding table
    arp_req1 = create_ip_arp_request("40:00:00:00:00:02", "192.168.200.2", "192.168.200.1");
    s.expect(PacketOutputEvent("router-eth1", arp_req1, display=Ethernet), "ARP request to router-eth1 for 192.168.200.1(server2)")

    # packet2 (s1 -> s2) arrives at the router-eth0
    fwd_pkt2 = mkIPpkt( "10:00:00:00:00:01", "192.168.100.1", "192.168.200.1")
    s.expect(PacketInputEvent("router-eth0", fwd_pkt2, display=Ethernet), "server1 -> server2 from port router-eth0")

    # packet3 (c -> s2) arrives at the router-eth0
    fwd_pkt3 = mkIPpkt( "30:00:00:00:00:01", "10.1.1.1", "192.168.200.1")
    s.expect(PacketInputEvent("router-eth2", fwd_pkt3, display=Ethernet), "client -> server2 from port router-eth2")

    # should not send other ARP req
    s.expect(PacketInputTimeoutEvent(0.5), "wait for 0.5s. No ARP req should be sent")

    # s2 replies ARP
    server2ArpReply = create_ip_arp_reply("20:00:00:00:00:01", "40:00:00:00:00:02", "192.168.200.1", "192.168.200.2");
    s.expect(PacketInputEvent("router-eth1", server2ArpReply, display=Ethernet), "server2 ARP reply. arrive at port router-eth1")


    # queued packets sent in order
    # pkt1. set Ethernet header
    fwd_pkt1 = mkIPpkt( "40:00:00:00:00:02", "192.168.100.1", "192.168.200.1", "20:00:00:00:00:01")
    s.expect(PacketOutputEvent("router-eth1", fwd_pkt1, display=Ethernet), "router sets Ethernet header and forwards the packet server1-server2")
    # pkt2. set Ethernet header
    fwd_pkt2 = mkIPpkt( "40:00:00:00:00:02", "192.168.100.1", "192.168.200.1", "20:00:00:00:00:01")
    s.expect(PacketOutputEvent("router-eth1", fwd_pkt2, display=Ethernet), "router sets Ethernet header and forwards the packet server1-server2")
    # pkt3. set Ethernet header
    fwd_pkt3 = mkIPpkt( "40:00:00:00:00:02", "10.1.1.1", "192.168.200.1", "20:00:00:00:00:01")
    s.expect(PacketOutputEvent("router-eth1", fwd_pkt3, display=Ethernet), "router sets Ethernet header and forwards the packet client-server2")



def case4_1(s): #Router replies ping
    mac = Ethernet()
    mac.src = "10:00:00:00:00:01"
    mac.dst = "40:00:00:00:00:01"

    ip = IPv4()
    ip.src = "192.168.100.1"
    ip.dst = "192.168.100.2"
    ip.ttl = 64

    icmp = ICMP()

    echoRequest = mac + ip + icmp
    s.expect(PacketInputEvent("router-eth0", echoRequest, display=Ethernet), "Echo Request arrives at eth1")

    # router makes ARP request. only send to the port in the forwarding table
    arpReqPkt = create_ip_arp_request("40:00:00:00:00:01", "192.168.100.2", "192.168.100.1");
    s.expect(PacketOutputEvent("router-eth0", arpReqPkt, display=Ethernet), "1st ARP request to router-eth1 for 192.168.200.1(server2)")

    # arp reply
    server2ArpReply = create_ip_arp_reply("10:00:00:00:00:01", "40:00:00:00:00:01", "192.168.100.1", "192.168.100.2");
    s.expect(PacketInputEvent("router-eth0", server2ArpReply, display=Ethernet), "server2 ARP reply. arrive at port router-eth1")

    # echo reply
    mac = Ethernet()
    mac.src = "40:00:00:00:00:01"
    mac.dst = "10:00:00:00:00:01"

    ip = IPv4()
    ip.src = echoRequest[IPv4].dst
    ip.dst = echoRequest[IPv4].src
    ip.ttl = 64

    icmp = ICMP()
    icmp.icmptype = ICMPType.EchoReply
    icmp.icmpdata.identifier = echoRequest[ICMP].icmpdata.identifier
    icmp.icmpdata.sequence = echoRequest[ICMP].icmpdata.sequence
    icmp.icmpdata.data = echoRequest[ICMP].icmpdata.data

    echoReply = mac + ip + icmp

    s.expect(PacketOutputEvent("router-eth0", echoReply, display=Ethernet), "router sends echo reply")


    # 2nd ping request, should not have ARP anymore
    s.expect(PacketInputEvent("router-eth0", echoRequest, display=Ethernet), "2nd Echo Request arrives at eth1")
    s.expect(PacketOutputEvent("router-eth0", echoReply, display=Ethernet), "no ARP. router sends echo reply")


    # Multiple echo request arrives (server2 called 1, client called 2)
    mac = Ethernet()
    mac.src = "20:00:00:00:00:01"
    mac.dst = "40:00:00:00:00:02"

    ip = IPv4()
    ip.src = "192.168.200.1"
    ip.dst = "192.168.200.2"
    ip.ttl = 64

    icmp = ICMP()

    icmp.icmpdata.identifier = 1
    echoRequest1_1 = mac + ip + icmp
    icmp.icmpdata.identifier = 2
    echoRequest1_2 = mac + ip + icmp
    icmp.icmpdata.identifier = 3
    echoRequest1_3 = mac + ip + icmp


    mac = Ethernet()
    mac.src = "30:00:00:00:00:01"
    mac.dst = "40:00:00:00:00:03"

    ip = IPv4()
    ip.src = "10.1.1.1"
    ip.dst = "10.1.1.2"
    ip.ttl = 64

    icmp = ICMP()

    icmp.icmpdata.identifier = 1
    echoRequest2_1 = mac + ip + icmp
    icmp.icmpdata.identifier = 2
    echoRequest2_2 = mac + ip + icmp
    icmp.icmpdata.identifier = 3
    echoRequest2_3 = mac + ip + icmp



    # requests arrives in random order
    # 2.3 arrives first
    s.expect(PacketInputEvent("router-eth2", echoRequest2_3, display=Ethernet), "Echo Request 2.3 arrives at eth2")

    # the request triggers ARP request
    arpReqPkt2 = create_ip_arp_request("40:00:00:00:00:03", "10.1.1.2", "10.1.1.1");
    s.expect(PacketOutputEvent("router-eth2", arpReqPkt2, display=Ethernet), "request 2.3 triggers ARP request")

    # 1.1 arrives then
    s.expect(PacketInputEvent("router-eth1", echoRequest1_1, display=Ethernet), "Echo Request 1.1 arrives at eth1")
    # the request triggers ARP request
    arpReqPkt1 = create_ip_arp_request("40:00:00:00:00:02", "192.168.200.2", "192.168.200.1");
    s.expect(PacketOutputEvent("router-eth1", arpReqPkt1, display=Ethernet), "request 1.1 triggers another ARP request")

    # other requests should trigger ARP request
    s.expect(PacketInputEvent("router-eth1", echoRequest1_3, display=Ethernet), "Echo Request 1.3 arrives at eth1")
    s.expect(PacketInputEvent("router-eth2", echoRequest2_1, display=Ethernet), "Echo Request 2.1 arrives at eth2")
    s.expect(PacketInputEvent("router-eth2", echoRequest2_2, display=Ethernet), "Echo Request 2.2 arrives at eth2")
    s.expect(PacketInputEvent("router-eth1", echoRequest1_2, display=Ethernet), "Echo Request 1.2 arrives at eth1")


    s.expect(PacketInputTimeoutEvent(1), "wait for 1s to timeout pending queue")
    s.expect(PacketOutputEvent("router-eth2", arpReqPkt2, display=Ethernet), "retry: request 2.3 triggers ARP request")
    s.expect(PacketOutputEvent("router-eth1", arpReqPkt1, display=Ethernet), "retry: request 1.1 triggers another ARP request")



    # arp reply from 1
    server2ArpReply = create_ip_arp_reply("20:00:00:00:00:01", "40:00:00:00:00:02", "192.168.200.1", "192.168.200.2");
    s.expect(PacketInputEvent("router-eth1", server2ArpReply, display=Ethernet), "server2 ARP reply. arrive at port router-eth1")


    # echo reply for 1.1, 1.3, 1.2 in order
    mac = Ethernet()
    mac.src = "40:00:00:00:00:02"
    mac.dst = "20:00:00:00:00:01"

    ip = IPv4()
    ip.src = echoRequest1_1[IPv4].dst
    ip.dst = echoRequest1_1[IPv4].src
    ip.ttl = 64

    icmp = ICMP()
    icmp.icmptype = ICMPType.EchoReply
    icmp.icmpdata.identifier = echoRequest1_1[ICMP].icmpdata.identifier
    icmp.icmpdata.sequence = echoRequest1_1[ICMP].icmpdata.sequence
    icmp.icmpdata.data = echoRequest1_1[ICMP].icmpdata.data

    echoReply = mac + ip + icmp

    s.expect(PacketOutputEvent("router-eth1", echoReply, display=Ethernet), "router sends echo reply")

    icmp.icmpdata.identifier = echoRequest1_3[ICMP].icmpdata.identifier
    icmp.icmpdata.sequence = echoRequest1_3[ICMP].icmpdata.sequence
    icmp.icmpdata.data = echoRequest1_3[ICMP].icmpdata.data
    echoReply = mac + ip + icmp
    s.expect(PacketOutputEvent("router-eth1", echoReply, display=Ethernet), "router sends echo reply")

    icmp.icmpdata.identifier = echoRequest1_2[ICMP].icmpdata.identifier
    icmp.icmpdata.sequence = echoRequest1_2[ICMP].icmpdata.sequence
    icmp.icmpdata.data = echoRequest1_2[ICMP].icmpdata.data
    echoReply = mac + ip + icmp
    s.expect(PacketOutputEvent("router-eth1", echoReply, display=Ethernet), "router sends echo reply")



    # arp reply from 2
    clientArpReply = create_ip_arp_reply("30:00:00:00:00:01", "40:00:00:00:00:03", "10.1.1.1", "10.1.1.2");
    s.expect(PacketInputEvent("router-eth2", clientArpReply, display=Ethernet), "client ARP reply. arrive at port router-eth2")


    # echo reply for 2.3, 2.1, 2.2 in order
    mac = Ethernet()
    mac.src = "40:00:00:00:00:03"
    mac.dst = "30:00:00:00:00:01"

    ip = IPv4()
    ip.src = echoRequest2_3[IPv4].dst
    ip.dst = echoRequest2_3[IPv4].src
    ip.ttl = 64

    icmp = ICMP()
    icmp.icmptype = ICMPType.EchoReply
    icmp.icmpdata.identifier = echoRequest2_3[ICMP].icmpdata.identifier
    icmp.icmpdata.sequence = echoRequest2_3[ICMP].icmpdata.sequence
    icmp.icmpdata.data = echoRequest2_3[ICMP].icmpdata.data

    echoReply = mac + ip + icmp

    s.expect(PacketOutputEvent("router-eth2", echoReply, display=Ethernet), "router sends echo reply")

    icmp.icmpdata.identifier = echoRequest2_1[ICMP].icmpdata.identifier
    icmp.icmpdata.sequence = echoRequest2_1[ICMP].icmpdata.sequence
    icmp.icmpdata.data = echoRequest2_1[ICMP].icmpdata.data
    echoReply = mac + ip + icmp
    s.expect(PacketOutputEvent("router-eth2", echoReply, display=Ethernet), "router sends echo reply")

    icmp.icmpdata.identifier = echoRequest2_2[ICMP].icmpdata.identifier
    icmp.icmpdata.sequence = echoRequest2_2[ICMP].icmpdata.sequence
    icmp.icmpdata.data = echoRequest2_2[ICMP].icmpdata.data
    echoReply = mac + ip + icmp
    s.expect(PacketOutputEvent("router-eth2", echoReply, display=Ethernet), "router sends echo reply")


