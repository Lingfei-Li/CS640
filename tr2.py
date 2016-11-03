import sys
import os
import time
from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent, PacketInputTimeoutEvent
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

def mkIPpkt(srcMac, srcIP, dstIP, dstMac="00:00:00:00:00:00"):
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = srcMac
    testpkt[0].dst = dstMac
    testpkt[1].src = srcIP
    testpkt[1].dst = dstIP
    return testpkt

def create_scenario():
    ''' forwarding table:
        192.168.100.0 255.255.255.0 192.168.100.1 router-eth0
        192.168.200.0 255.255.255.0 192.168.200.1 router-eth1
        10.1.0.0      255.255.0.0   10.1.1.1      router-eth2
    '''

    s = Scenario("Router test item#2 item#3")
    s.add_interface('router-eth0', '40:00:00:00:00:01', '192.168.100.2')
    s.add_interface('router-eth1', '40:00:00:00:00:02', '192.168.200.2')
    s.add_interface('router-eth2', '40:00:00:00:00:03', '10.1.1.2')

    #1: packet for the router get dropped
    testpkt = mkIPpkt( "10:00:00:00:00:01", "192.168.100.1", "192.168.100.2")
    s.expect(PacketInputEvent("router-eth0", testpkt, display=Ethernet), "packet from router-eth0 (server1) for router. should be dropped")


    #2: forward packet. ARP request timeout
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


    #3: forward packet. ARP request ok
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


    #4: more packets simultaneously
    #TODO

    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
