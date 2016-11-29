#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from threading import *
import time
import struct

def switchy_main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]

    params_filename = "blastee_params.txt"
    with open(params_filename) as f:
        content = f.readlines()
    params = content[0].split()
    if len(params) != 4:
        log_failure("wrong number of params")
        return 1

    if params[0] != "-b" or params[2] != "-n":
        log_failure("wrong params")
        return 1

    blaster_ip = params[1]
    num_pkt = int(params[3])

    #initialization done


    while True:
        gotpkt = True
        try:
            dev,pkt = net.recv_packet()
            log_info("Device is {}".format(dev))
        except NoPackets:
            log_info("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_info("Got shutdown signal")
            break

        if gotpkt:
            log_debug("I got a packet from {}".format(dev))
            log_debug("Pkt: {}".format(pkt))
            del pkt[Ethernet]
            del pkt[IPv4]
            del pkt[UDP]
            seq_num_bytes = pkt.to_bytes()[:4]
            seq_num = struct.unpack(">I", seq_num_bytes)[0]
            log_info("Pkt #{}".format(seq_num))

            len_payload_bytes = pkt.to_bytes()[4:4+2]
            len_payload = struct.unpack(">H", len_payload_bytes)[0]
            payload_bytes = pkt.to_bytes()[6:6+len_payload]

            ack = Ethernet() + IPv4() + UDP()
            ack[1].protocol = IPProtocol.UDP

            ack[Ethernet].src = "20:00:00:00:00:01"
            ack[Ethernet].dst = "40:00:00:00:00:02"
            ack[IPv4].src = "192.168.200.1"
            ack[IPv4].dst = blaster_ip
            seq_num_bytes = struct.pack('>I', seq_num)
            ack.add_payload(seq_num_bytes)
            ack.add_payload(payload_bytes[:8])

            net.send_packet("blastee-eth0", ack)





    net.shutdown()
