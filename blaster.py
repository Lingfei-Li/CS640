#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from random import randint
import time
import struct


def switchy_main(net):
    #initialization
    my_intf = net.interfaces()
    myintfnames = [intf.ethaddr for intf in my_intf]
    mymacs = [intf.ethaddr for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]

    print(myintfnames)

    params_filename = "blaster_params.txt"
    with open(params_filename) as f:
        content = f.readlines()
    params = content[0].split()
    if len(params) != 12:
        log_failure("wrong number of params")
        return 1

    if params[0] != "-b" or params[2] != "-n" or params[4] != "-l" or params[6] != "-w" or params[8] != "-t" or params[10] != "-r":
        log_failure("wrong params")
        return 1

    blastee_ip = params[1]
    num_pkt = int(params[3])
    length_payload = int(params[5])
    sender_window = int(params[7])
    timeout_millis = float(params[9])
    recv_timeout = float(params[11])

    if length_payload < 0 or length_payload > 65535:
        log_failure("length should be in range [0,65535]")
        return 1

    #initialization done

    cnt = 0
    while True:
        gotpkt = True
        try:
            dev,pkt = net.recv_packet(timeout=recv_timeout)
        except NoPackets:
            log_info("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_info("Got shutdown signal")
            break

        if gotpkt:
            log_info("I got a packet")
        else:
            log_info("Didn't receive anything")

            '''
            Creating the headers for the packet
            '''
            pkt = Ethernet() + IPv4() + UDP()
            pkt[1].protocol = IPProtocol.UDP

            pkt[Ethernet].src = "10:00:00:00:00:01"
            pkt[Ethernet].dst = "40:00:00:00:00:01"
            pkt[IPv4].src = "192.168.100.1"
            pkt[IPv4].dst = blastee_ip
            seq_num = 65536
            seq_num_byte = struct.pack('>I', seq_num)
            print(seq_num_byte)
            pkt.add_payload(seq_num_byte)

            net.send_packet("blaster-eth0", pkt)
            log_info("blaster sends a packet!")
            log_info("shutdown for now")
            break;

    net.shutdown()


