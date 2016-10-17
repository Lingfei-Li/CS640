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

    #case1: initial flooding
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "30:00:00:00:00:02"
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt,"eth7", testpkt, display=Ethernet), "initial: flood eth2-7")


    #case2: after learning
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:02"
    testpkt[0].dst = "30:00:00:00:00:01"
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "packet from eth2")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "After learning & before TO, only send to eth1")

    #case3: wait for timeout. Remember to sleep in switch code
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    #case3: wait for timeout
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    #case3: after timeout, should flood
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "20:00:00:00:00:02"
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "packet from eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, "eth4", testpkt, "eth5", testpkt,"eth6", testpkt,"eth7", testpkt, display=Ethernet), "timeout: flood eth2-7")

    #case3: update topology should reset timer
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "10:00:00:00:00:01"
    s.expect(PacketInputEvent("eth3", testpkt, display=Ethernet), "packet from eth3")



    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
