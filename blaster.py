#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from random import randint
import time
import struct

def draw_progress(num_pkt, acked_seq, LHS, RHS):
    upper = ""
    lower = ""
    for i in range(1, num_pkt+1):
        if i in acked_seq:
            upper += "o"
        else:
            upper += "_"
        if LHS == i and RHS == i:
            lower += "="
        elif LHS == i:
            lower += "["
        elif RHS == i:
            lower += ")"
        else:
            lower += " "
    if RHS == num_pkt+1:
        lower += ")"
    print("Packet sending progress:")
    print(upper)
    print(lower)
    print("LHS: {}, RHS: {}".format(LHS, RHS))

def printStat(totalTXTime, numReTX, numCoarseTO, throughput, goodput):
    log_info("Total TX time: {}".format(totalTXTime))
    log_info("Number of reTX: {}".format(numReTX))
    log_info("Number of coarse TOs: {}".format(numCoarseTO))
    log_info("Throughput: {}".format(throughput))
    log_info("Goodput: {}".format(goodput))


def switchy_main(net):
    #initialization
    my_intf = net.interfaces()
    myintfnames = [intf.ethaddr for intf in my_intf]
    mymacs = [intf.ethaddr for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]
    pktBySeq = {}       #hashtable of packets with seq# as key
    startTime = time.time()
    numReTX = 0
    numCoarseTO = 0
    totalByteSent = 0
    goodByteSent = 0

    print(myintfnames)

    params_filename = "blaster_params.txt"
    with open(params_filename) as f:
        content = f.readlines()
    params = content[0].split()
    if len(params) != 12:
        log_failure("wrong number of params")
        return 1

    if params[0] != "-b" or params[2] != "-n" or params[4] != "-l" or params[6] != "-w" \
            or params[8] != "-t" or params[10] != "-r":
        log_failure("wrong params")
        return 1

    blastee_ip = params[1]
    num_pkt = int(params[3])
    len_payload = int(params[5])
    SW = sender_window = int(params[7])
    timeout_millis = float(params[9])
    recv_timeout = float(params[11])

    if len_payload < 0 or len_payload > 65535:
        log_failure("length should be in range [0,65535]")
        return 1

    LHS = RHS = 1
    LHS_lastmove = 0
    acked_seq = []

    #initialization done

    while True:
        draw_progress(num_pkt, acked_seq, LHS, RHS)
        if LHS == num_pkt+1:
            log_info("All packets sent! Exit the program")
            totalTXTime = time.time() - startTime
            throughput = totalByteSent/totalTXTime
            goodput = goodByteSent/totalTXTime
            printStat(totalTXTime, numReTX, numCoarseTO, throughput, goodput)
            break;

        gotpkt = True
        try:
            dev,pkt = net.recv_packet(timeout=recv_timeout)
        except NoPackets:
            log_debug("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_info("Got shutdown signal")
            break

        if gotpkt:
            del pkt[Ethernet]
            del pkt[IPv4]
            del pkt[UDP]

            seq_num_bytes = pkt.to_bytes()[:4]
            seq_num = struct.unpack(">I", seq_num_bytes)[0]

            payload_bytes = pkt.to_bytes()[4:4+len_payload]

            log_debug("Seq# {}, payload: {}".format(seq_num, payload_bytes))
            acked_seq.append(seq_num)
            print("del seq num {} from queue".format(seq_num))
            del pktBySeq[seq_num]   #remove the packet from buffer

            log_info("ACK #{}".format(seq_num))
            if LHS in acked_seq:
                LHS_lastmove = time.time()  #update the LHS last move time
            while LHS in acked_seq:     #move LHS to the rightmost position without ACK
                LHS += 1
        else:
            if RHS != num_pkt+1 and RHS-LHS+1 < SW:
                log_info("Extending RHS (Sending new data)")
                while RHS - LHS + 1 < SW and RHS <= num_pkt:
                    pkt = Ethernet() + IPv4() + UDP()
                    pkt[1].protocol = IPProtocol.UDP

                    pkt[Ethernet].src = "10:00:00:00:00:01"
                    pkt[Ethernet].dst = "40:00:00:00:00:01"
                    pkt[IPv4].src = "192.168.100.1"
                    pkt[IPv4].dst = blastee_ip
                    seq_num = RHS
                    seq_num_bytes = struct.pack('>I', seq_num)
                    pkt.add_payload(seq_num_bytes)

                    len_payload_bytes = struct.pack('>H', len_payload)
                    pkt.add_payload(len_payload_bytes)

                    
                    payload_int_arr = []
                    while len(payload_int_arr) < len_payload:
                        payload_int_arr.append(randint(0, 255)) #appending random bytes to payload
                    payload_bytes = bytes(payload_int_arr)
                    pkt.add_payload(payload_bytes)
                    log_debug("payload: {}".format(payload_bytes))


                    pktBySeq[seq_num] = pkt
                    print("Add seq num {} to queue".format(seq_num))
                    net.send_packet("blaster-eth0", pkt)

                    totalByteSent += len_payload
                    goodByteSent += len_payload
                    RHS += 1
            elif 1000*(time.time() - LHS_lastmove) > timeout_millis:        #coarse timeout
                log_info("Coarse timeout effective")
                numCoarseTO += 1
                LHS_lastmove = time.time()
                for seq in range(LHS, min(1+num_pkt, RHS)):
                    if not seq in acked_seq:
                        log_info("Resending seq# {}".format(seq))

                        pkt = pktBySeq[seq]
                        
                        net.send_packet("blaster-eth0", pkt)
                        numReTX += 1
                        totalByteSent += len_payload

    net.shutdown()


