from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent
from switchyard.lib.packet import *

def create_scenario():
    s = Scenario("LRU switch basic test")
    s.add_interface('eth1', '10:00:00:00:00:01')
    s.add_interface('eth2', '10:00:00:00:00:02')
    s.add_interface('eth3', '10:00:00:00:00:03')
    s.add_interface('eth4', '10:00:00:00:00:04')
    s.add_interface('eth5', '10:00:00:00:00:05')
    s.add_interface('eth6', '10:00:00:00:00:06')
    s.add_interface('eth7', '10:00:00:00:00:07')

#case 1
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "30:00:00:00:00:04"
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt,"eth7", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth2-7")


#case2
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:02"
    testpkt[0].dst = "30:00:00:00:00:01"
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth2")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "After learning of test 1, switch should only send to port eth1")

#case3
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:03"
    testpkt[0].dst = "30:00:00:00:00:01"
    s.expect(PacketInputEvent("eth3", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth3")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "After learning of test 1, switch should only send to port eth1")

#case4
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:04"
    testpkt[0].dst = "30:00:00:00:00:01"
    s.expect(PacketInputEvent("eth4", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth4")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "After learning of test 1, switch should only send to port eth1")

#case5
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:05"
    testpkt[0].dst = "30:00:00:00:00:01"
    s.expect(PacketInputEvent("eth5", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth5")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "After learning of test 1, switch should only send to port eth1")

#case6
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:06"
    testpkt[0].dst = "30:00:00:00:00:07"
    s.expect(PacketInputEvent("eth6", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth6")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth1", testpkt,"eth7", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth1-5 and eth7")

#case7
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:04"
    testpkt[0].dst = "30:00:00:00:00:05"
    s.expect(PacketInputEvent("eth4", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth4")
    s.expect(PacketOutputEvent("eth5", testpkt, display=Ethernet), "After learning of test 1, switch should only send to port eth5")



    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
