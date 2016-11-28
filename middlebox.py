#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from threading import *
from random import randint
import time

def switchy_main(net):

    #initialization
    my_intf = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]
    my_intfbyname = {}
    for intf in my_intf:
        my_intfbyname[intf.name] = intf


    params_filename = "middlebox_params.txt"
    with open(params_filename) as f:
        content = f.readlines()
    params = content[0].split()
    if len(params) != 2:
        log_failure("wrong number of params")
        return 1
    if params[0] != "-d":
        log_failure("wrong flag. excepting -d as first flag")
        return 1

    mydroprate = float(params[1])

    if mydroprate < 0 or mydroprate > 1:
        log_failure("wrong drop rate. excepting drop rate within [0,1]")
        return 1

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
            log_info("I got a packet {}".format(pkt))

        if pkt.get_header(Arp) is not None:
            continue

        if dev == "middlebox-eth0":
            log_info("Received from blaster")
            rand = randint(0, 100)
            log_info("rand is " + str(rand))
            if rand > mydroprate*100:
                pkt[Ethernet].src = "40:00:00:00:00:02"
                pkt[Ethernet].dst = "20:00:00:00:00:01"
                pkt[IPv4].src = "192.168.200.2"
                pkt[IPv4].dst = "192.168.200.1"
                net.send_packet("middlebox-eth1", pkt)
                log_info("-> forward!")
            else:
                log_info("-> drop...")
        elif dev == "middlebox-eth1":
            log_info("ACK from blastee")
            log_info("-> forward!")
            pkt[Ethernet].src = "40:00:00:00:00:01"
            pkt[Ethernet].dst = "10:00:00:00:00:01"
            pkt[IPv4].src = "192.168.100.2"
            pkt[IPv4].dst = "192.168.100.1"
            net.send_packet("middlebox-eth0", pkt)
        else:
            log_info("Oops :))")

    net.shutdown()
