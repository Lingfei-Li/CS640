from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent, PacketInputTimeoutEvent
from switchyard.lib.packet import *

def mkpkt(src, dst):
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = src
    testpkt[0].dst = dst
    return testpkt

def create_scenario():
    s = Scenario("Timeout switch test")
    s.add_interface('eth1', '10:00:00:00:00:01')
    s.add_interface('eth2', '10:00:00:00:00:02')
    s.add_interface('eth3', '10:00:00:00:00:03')
    s.add_interface('eth4', '10:00:00:00:00:04')
    s.add_interface('eth5', '10:00:00:00:00:05')
    s.add_interface('eth6', '10:00:00:00:00:06')
    s.add_interface('eth7', '10:00:00:00:00:07')

    #case1: broadcasting
    testpkt = mkpkt( "30:00:00:00:00:01", "ff:ff:ff:ff:ff:ff")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt,"eth7", testpkt, display=Ethernet), "broadcast: flood all but incoming ports")

    #case2: packet for the switch get dropped
    testpkt = mkpkt( "30:00:00:00:00:01", "10:00:00:00:00:01")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")

    #case3: before learning: flood
    testpkt = mkpkt( "30:00:00:00:00:01", "30:00:00:00:00:02")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt,"eth7", testpkt, display=Ethernet), "before learning flood eth2-7")

    #case4: after learning send to port
    testpkt = mkpkt( "30:00:00:00:00:02", "30:00:00:00:00:01")
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "packet from eth2")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "After learning & before TO, only send to eth1")

    #case 5: after timeout the entry should be kicked
    testpkt = mkpkt( "30:00:00:00:00:01", "10:00:00:00:00:01")      #send to switch to simply drop the packet
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    #wait for timeout
    s.expect(PacketInputTimeoutEvent(11), "wait for 11 sec")
    #mapping for 02 should be kicked -> flood
    testpkt = mkpkt( "30:00:00:00:00:01", "30:00:00:00:00:02")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt,"eth7", testpkt, display=Ethernet), "after timeout: should flood to eth2-7")

    #case 6: updating topology should reset timer
    testpkt = mkpkt( "30:00:00:00:00:01", "10:00:00:00:00:01")      #send to switch to simply drop the packet
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet with dst 01 comes from eth1")
    s.expect(PacketInputTimeoutEvent(8), "wait for 8 sec")
    #update topology
    testpkt = mkpkt( "30:00:00:00:00:01", "10:00:00:00:00:01")      #send to switch to simply drop the packet
    s.expect(PacketInputEvent("eth3", testpkt, display=Ethernet), "packet with dst 01 now comes from eth3")
    s.expect(PacketInputTimeoutEvent(5), "wait for 5 sec")
    #should not timeout
    testpkt = mkpkt( "30:00:00:00:00:02", "30:00:00:00:00:01")      #send to switch to simply drop the packet
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "packet for 01")
    s.expect(PacketOutputEvent("eth3", testpkt, display=Ethernet), "map for 01->eth3 shuold not timeout (should not flood but only send to eth3)")



    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
