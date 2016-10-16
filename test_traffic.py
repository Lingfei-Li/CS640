#!/usr/bin/env python3

import sys
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from switchyard.lib.testing import *

def mk_pkt(hwsrc, hwdst, ipsrc, ipdst, reply=False):
    ether = Ethernet()
    ether.src = EthAddr(hwsrc)
    ether.dst = EthAddr(hwdst)
    ether.ethertype = EtherType.IP

    ippkt = IPv4()
    ippkt.srcip = IPAddr(ipsrc)
    ippkt.dstip = IPAddr(ipdst)
    ippkt.protocol = IPProtocol.ICMP
    ippkt.ttl = 32

    icmppkt = ICMP()
    if reply:
        icmppkt.icmptype = ICMPType.EchoReply
    else:
        icmppkt.icmptype = ICMPType.EchoRequest

    return ether + ippkt + icmppkt

def test_traffic():
    s = Scenario("traffic volume-based switch tests")
    s.add_interface('eth0', '10:00:00:00:00:01')
    s.add_interface('eth1', '10:00:00:00:00:02')
    s.add_interface('eth2', '10:00:00:00:00:03')

    # test case 1: a frame with broadcast destination should get send out of all ports except the input port
    reqpkt = mk_pkt("20:00:00:00:00:02", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "20:00:00:00:00:02->ff:ff:ff:ff:ff:ff received on eth1")
    s.expect(PacketOutputEvent("eth0", reqpkt, "eth2", reqpkt, display=Ethernet), "add entry to table, flood out eth0 and eth2")        

    # test case 2: a frame with any unicast address except one assigned to hub interface should be sent out all ports except the input port
    reqpkt = mk_pkt("20:00:00:00:00:01", "30:00:00:00:00:02", '192.168.1.100', '172.16.42.2')
    s.expect(PacketInputEvent("eth0", reqpkt, display=Ethernet), "20:00:00:00:00:01->30:00:00:00:00:02 received on eth0") 
    s.expect(PacketOutputEvent("eth1", reqpkt, "eth2", reqpkt, display=Ethernet), "add entry to table, flood out eth1 and eth2")

    # test case 3: a frame with dest address of one of the interfaces should result in nothing happening
    reqpkt = mk_pkt("30:00:00:00:00:02", "10:00:00:00:00:03", "44.210.140.130", "113.140.116.102")
    s.expect(PacketInputEvent("eth0", reqpkt, display=Ethernet), "30:00:00:00:00:02->10:00:00:00:00:03 received on eth0")
    s.expect(PacketInputTimeoutEvent(1.0), "add entry to table, ignore since intended for itself")

    # test case 4: packet forward to a destination stored in the table
    reqpkt = mk_pkt("20:00:00:00:00:03", "20:00:00:00:00:01", "172.16.42.2", "192.168.1.100")
    s.expect(PacketInputEvent("eth2", reqpkt, display=Ethernet), "20:00:00:00:00:03->20:00:00:00:00:01 received on eth2")
    s.expect(PacketOutputEvent("eth0", reqpkt, display=Ethernet), "increase traffic volume, forward to eth0")

    # test case 5: incoming port for packet is different from the port info in the table
    reqpkt = mk_pkt("30:00:00:00:00:02", "20:00:00:00:00:02", "44.210.140.130", "172.16.42.2")
    s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "30:00:00:00:00:02->20:00:00:00:00:02 received on eth1")
    s.expect(PacketOutputEvent("eth1", reqpkt, display=Ethernet), "update port info, increase traffic volume, forward to eth1")

    reqpkt = mk_pkt("30:00:00:00:00:03", "30:00:00:00:00:02", "35.2.227.21", "44.210.140.130")
    s.expect(PacketInputEvent("eth2", reqpkt, display=Ethernet), "30:00:00:00:00:03->30:00:00:00:00:02 received on eth2")
    s.expect(PacketOutputEvent("eth1", reqpkt, display=Ethernet), "port info succesfully updated, increase traffic volume, forward to eth1")
    
    # test case 5: remove an entry when table is full
    reqpkt = mk_pkt("30:00:00:00:00:02", "30:00:00:00:00:03", "44.210.140.130", "35.2.227.21")
    s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "30:00:00:00:00:02->30:00:00:00:00:03 received on eth1") 
    s.expect(PacketOutputEvent("eth2", reqpkt, display=Ethernet), "add entry to table, forward to eth2")

    reqpkt = mk_pkt("30:00:00:00:00:01", "20:00:00:00:00:03", "160.101.23.179", "172.16.42.2")
    s.expect(PacketInputEvent("eth0", reqpkt, display=Ethernet), "30:00:00:00:00:01->20:00:00:00:00:03 received on eth0")
    s.expect(PacketOutputEvent("eth1", reqpkt, "eth2", reqpkt, display=Ethernet), "remove an entry and add new entry to table, flood out eth1 and eth2")

    return s

scenario = test_traffic()
