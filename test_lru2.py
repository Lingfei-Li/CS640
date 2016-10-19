from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent
from switchyard.lib.packet import *

def create_scenario():
    s = Scenario("LRU switch topology update test")
    s.add_interface('eth1', '10:00:00:00:00:01')
    s.add_interface('eth2', '10:00:00:00:00:02')
    s.add_interface('eth3', '10:00:00:00:00:03')
    s.add_interface('eth4', '10:00:00:00:00:04')
    s.add_interface('eth5', '10:00:00:00:00:05')
    s.add_interface('eth6', '10:00:00:00:00:06')
    s.add_interface('eth7', '10:00:00:00:00:07')

#test: updating cache entry doesn't change freshness (changed topology)

#case 1
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "10:00:00:00:00:01"    #for the swtich. will be dropped
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "send the packet from eth1")

    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:02"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "send the packet from eth2")

    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:03"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth3", testpkt, display=Ethernet), "send the packet from eth3")

    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:04"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth4", testpkt, display=Ethernet), "send the packet from eth4")

    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:05"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth5", testpkt, display=Ethernet), "send the packet from eth5")

    #cache shuold be full now, and eth1 is the LRU

    #updating the topology (now address :01 maps to eth5)
    #but :01 should still be LRU
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth6", testpkt, display=Ethernet), "send the packet from eth6")

    #new entry added to the table, :01 shuold be kicked
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:07"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth7", testpkt, display=Ethernet), "send the packet from eth7")

    #packet with dst=eth1 shuold be flooded now
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:07"
    testpkt[0].dst = "30:00:00:00:00:01"
    s.expect(PacketInputEvent("eth7", testpkt, display=Ethernet), "send the packet from eth7")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, "eth3", testpkt, "eth4", testpkt,"eth5", testpkt,"eth6", testpkt, display=Ethernet), "eth1 should be out. flood to ports eth1-5 and eth7")

    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
