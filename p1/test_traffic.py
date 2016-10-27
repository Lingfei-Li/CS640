#!/usr/bin/env python3

import sys
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from switchyard.lib.testing import *

def mkpkt(src, dst):
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = src
    testpkt[0].dst = dst
    return testpkt

def test_traffic():
    s = Scenario("Traffic switch test")
    s.add_interface('eth1', '10:00:00:00:00:01')
    s.add_interface('eth2', '10:00:00:00:00:02')
    s.add_interface('eth3', '10:00:00:00:00:03')
    s.add_interface('eth4', '10:00:00:00:00:04')
    s.add_interface('eth5', '10:00:00:00:00:05')
    s.add_interface('eth6', '10:00:00:00:00:06')
    s.add_interface('eth7', '10:00:00:00:00:07')

    # test case 1: broadcast destination should get send out of all ports except the input port
    testpkt = mkpkt( "30:00:00:00:00:01", "ff:ff:ff:ff:ff:ff")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt,"eth7", testpkt, display=Ethernet), "broadcast: flood eth2-7")

    # test case 2: packet for the switch: dropped
    testpkt = mkpkt( "30:00:00:00:00:01", "10:00:00:00:00:01")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")

    # test case 3: before any learning: flood
    testpkt = mkpkt( "30:00:00:00:00:01", "30:00:00:00:00:02")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt,"eth7", testpkt, display=Ethernet), "before learning: flood eth2-7")


    # test case 4: after learning: send to port
    testpkt = mkpkt( "30:00:00:00:00:03", "30:00:00:00:00:01")
    s.expect(PacketInputEvent("eth3", testpkt, display=Ethernet), "packet from eth3")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "after learning: only send to eth1") 
    #eth1 should have traffic 1, eth3 should have traffic 0 now

    # test case 5: table full -> kick least traffic entry
    #preparation: get more entries and traffic
    testpkt = mkpkt( "30:00:00:00:00:02", "30:00:00:00:00:01")
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "packet from eth2")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "after learning: only send to eth1") 

    testpkt = mkpkt( "30:00:00:00:00:03", "30:00:00:00:00:02")
    s.expect(PacketInputEvent("eth3", testpkt, display=Ethernet), "packet from eth2")
    s.expect(PacketOutputEvent("eth2", testpkt, display=Ethernet), "after learning: only send to eth2") 

    testpkt = mkpkt( "30:00:00:00:00:04", "30:00:00:00:00:03")
    s.expect(PacketInputEvent("eth4", testpkt, display=Ethernet), "packet from eth4")
    s.expect(PacketOutputEvent("eth3", testpkt, display=Ethernet), "after learning: only send to eth3") 

    testpkt = mkpkt( "30:00:00:00:00:05", "30:00:00:00:00:04")
    s.expect(PacketInputEvent("eth5", testpkt, display=Ethernet), "packet from eth5")
    s.expect(PacketOutputEvent("eth4", testpkt, display=Ethernet), "after learning: only send to eth4") 
    #until now, 05->eth5 mapping has the lowest traffic 0, and should be kicked in next operation

    testpkt = mkpkt( "30:00:00:00:00:06", "30:00:00:00:00:05")
    s.expect(PacketInputEvent("eth6", testpkt, display=Ethernet), "packet from eth6")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth7", testpkt, display=Ethernet), "eth5 shuold be kicked, as its traffic is the lowest (0). Packet should be flooded")


    # test case 5: topology change. should not change traffic. 
    #change mapping from 06->eth6 to 06->eth3
    testpkt = mkpkt( "30:00:00:00:00:06", "30:00:00:00:00:05")
    s.expect(PacketInputEvent("eth3", testpkt, display=Ethernet), "packet from eth3")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, "eth4", testpkt, "eth5", testpkt, "eth6", testpkt,"eth7", testpkt, display=Ethernet), "mapping for 05 is not existent")
    # new mapping should kick 06->eth6 mapping which should has traffic 0
    testpkt = mkpkt( "30:00:00:00:00:07", "30:00:00:00:00:06")
    s.expect(PacketInputEvent("eth7", testpkt, display=Ethernet), "packet from eth7")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt, display=Ethernet), "mapping for 06 should be kicked")


    return s

scenario = test_traffic()
