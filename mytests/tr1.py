import sys
import os
import time
from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

def create_scenario():
    s = Scenario("Router test item#1")
    s.add_interface('eth1', '10:00:00:00:00:01', '1.1.1.1')
    s.add_interface('eth2', '10:00:00:00:00:02', '1.1.1.2')
    s.add_interface('eth3', '10:00:00:00:00:03', '1.1.1.3')

    #ARP request for router's interfaces
    requestPkt = create_ip_arp_request( "30:00:00:00:00:01", "3.1.1.1", "1.1.1.1");
    s.expect(PacketInputEvent("eth1", requestPkt, display=Ethernet), "ARP request from eth1")
    replyPkt = create_ip_arp_reply( "10:00:00:00:00:01", "30:00:00:00:00:01", "1.1.1.1", "3.1.1.1");
    s.expect(PacketOutputEvent("eth1", replyPkt, display=Ethernet), "Target is router's interface. ARP Reply from the same port")

    #ARP request that is not for router
    requestPkt = create_ip_arp_request( "30:00:00:00:00:01", "3.1.1.1", "2.1.1.1");
    s.expect(PacketInputEvent("eth1", requestPkt, display=Ethernet), "ARP request from eth1. Target is not router's interface, should be ignored.")

    #ARP reply. Should be ignored
    testpkt = create_ip_arp_reply( "30:00:00:00:00:00", "30:00:00:00:00:01", "192.168.0.0", "1.1.1.1");
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "ARP reply from eth1. Should be ignored")

    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
