#!/usr/bin/env python3

'''
Ethernet learning switch in Python: HW3.

Note that this file currently has the code to implement a "hub"
in it, not a learning switch.  (I.e., it's currently a switch
that doesn't learn.)
'''
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *

def switchy_main(net):
    my_interfaces = net.interfaces() 
    mymacs = [intf.ethaddr for intf in my_interfaces]
    # create tables to hold <dst, dev> and traffic volume
    dst_table = {}
    traffic_table = {}
    LIMIT = 5
    
    while True:
        try:
            dev, packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return


        pkt_dst = packet[0].dst
        pkt_src = packet[0].src

        # check if the <dst, dev> pair is in the table
        # if in the table: update dst if necessary 
        # if not in the table: add new entry (remove one entry if exceeds limit)
        if pkt_src in dst_table:
            if dst_table[pkt_src] != dev:
                dst_table[pkt_src] = dev
        else:
            if len(dst_table) == LIMIT:
                # remove the entry that has the least traffic volume from all tables
                rm_dst = None
                rm_traffic = -1
                for dst in traffic_table:
                    if rm_traffic == -1 or rm_traffic > traffic_table[dst]:
                        rm_dst = dst
                        rm_traffic = traffic_table[dst]
                if not rm_traffic == -1:
                    del dst_table[rm_dst]
                    del traffic_table[rm_dst]
            dst_table[pkt_src] = dev
            traffic_table[pkt_src] = 0
        for dst in dst_table:
            log_debug(str(dst) + " -> " + str(dst_table[dst]) + " traffic: " + str(traffic_table[dst]))
        log_debug("")
        
        log_debug ("In {} received packet {} on {}".format(net.name, packet, dev))
        if pkt_dst in mymacs:
            log_debug ("Packet intended for me")
        else:
            if pkt_dst in dst_table:
                traffic_table[pkt_dst] += 1
                net.send_packet(dst_table[pkt_dst], packet)
            else:
                for intf in my_interfaces:
                    if dev != intf.name:
                        log_debug ("Flooding packet {} to {}".format(packet, intf.name))
                        net.send_packet(intf.name, packet)
    net.shutdown()
