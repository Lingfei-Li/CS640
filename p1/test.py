from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent
from switchyard.lib.packet import *

def create_scenario():
    s = Scenario("hub tests")
    s.add_interface('eth0', '10:00:00:00:00:01')
    s.add_interface('eth1', '10:00:00:00:00:02')
    s.add_interface('eth2', '10:00:00:00:00:03')

    # test case 1: a frame with broadcast destination should get sent out all ports except ingress
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = "30:00:00:00:00:01"
    testpkt[0].dst = "30:00:00:00:00:02"
    testpkt[1].src = "172.16.42.2"
    testpkt[1].dst = "255.255.255.255"

    # arrives on eth1
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")

    # expect that the packet should be flooded to all ports except ingress
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")


    # test case 2: after learning, packet should not be flooded
    testpkt2 = Ethernet() + IPv4() + ICMP()
    testpkt2[0].src = "30:00:00:00:00:02"
    testpkt2[0].dst = "30:00:00:00:00:01"
    testpkt2[1].src = "255.255.255.255"
    testpkt2[1].dst = "172.16.42.2"

    # arrives on eth2
    s.expect(PacketInputEvent("eth2", testpkt2, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth2")

    # expect that the packet should be sent out ports eth1
    s.expect(PacketOutputEvent("eth1", testpkt2, display=Ethernet), "After learning of test 1, switch should only send to port eth1")
    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
