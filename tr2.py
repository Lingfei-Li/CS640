import sys
import os
import time
from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

def mkIPpkt(srcMac, srcIP, dstIP):
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = srcMac
    testpkt[1].src = srcIP
    testpkt[1].dst = dstIP
    return testpkt

def create_scenario():
    s = Scenario("Router test")
    s.add_interface('eth1', '10:00:00:00:00:01', '1.1.1.1')
    s.add_interface('eth2', '10:00:00:00:00:02', '1.1.1.2')
    s.add_interface('eth3', '10:00:00:00:00:03', '1.1.1.3')

    testpkt = mkIPpkt( "30:00:00:00:00:01", "3.1.1.1", "1.1.1.1")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")


    testpkt = mkIPpkt( "30:00:00:00:00:01", "3.1.1.1", "192.168.100.1")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    arpReqPkt = create_ip_arp_request("10:00:00:00:00:01", "1.1.1.1", "192.168.100.1");
    s.expect(PacketOutputEvent("eth1", arpReqPkt, display=Ethernet), "Router should flood an ARP request to eth1 for target IP")
    arpReqPkt = create_ip_arp_request("10:00:00:00:00:02", "1.1.1.2", "192.168.100.1");
    s.expect(PacketOutputEvent("eth2", arpReqPkt, display=Ethernet), "Router should flood an ARP request to eth2 for target IP")
    arpReqPkt = create_ip_arp_request("10:00:00:00:00:03", "1.1.1.3", "192.168.100.1");
    s.expect(PacketOutputEvent("eth3", arpReqPkt, display=Ethernet), "Router should flood an ARP request to eth3 for target IP")


    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
