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
    testpkt[0].dst = "ff:ff:ff:ff:ff:ff"

    # expect that the packet should arrive on port eth1
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")

    # expect that the packet should be sent out ports eth0 and eth2 (but *not* eth1)
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")

    return s

# the name scenario here is required --- the Switchyard framework will
# explicitly look for an object named scenario in the test description file.
scenario = create_scenario()
