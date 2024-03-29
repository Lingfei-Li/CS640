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

    ''' LHS is the left boundary of sent packets (included). RHS is the EXCLUSIVE right boundary '''
    LHS = RHS = 1       
    LHS_lastmove = time.time()
    acked_seq = []
    pktBySeq = {}       #hashtable of packets with seq# as key

    ''' reTxFinished marks whether a round of retransmission has finished '''
    reTxFinished = True
    ''' lastReTxPos marks the last handled position of ongoing retransmission '''
    lastReTxPos = -1

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
            dev,pkt = net.recv_packet(timeout=recv_timeout/1000)
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
            #payload_bytes = pkt.to_bytes()[4:4+len_payload]

            if seq_num not in acked_seq:
                #log_debug("Seq# {}, payload: {}".format(seq_num, payload_bytes))
                acked_seq.append(seq_num)

                del pktBySeq[seq_num]   #remove the packet from buffer

                log_info("ACK #{}".format(seq_num))

                # Move LHS if possible
                while LHS in acked_seq:     #move LHS to the leftmost unACK'ed position
                    LHS += 1
                    LHS_lastmove = time.time()  #update the LHS last move time

        else:   #no packet to receive

            ''' Assume that all retransmissions are handled before sending new packets '''

            #coarse timeout
            if LHS < RHS and 1000*(time.time() - LHS_lastmove) >= timeout_millis:        
                if reTxFinished == True:
                    #new corase timeout
                    log_info("Coarse timeout effective")
                    numCoarseTO += 1
                    reTxFinished = False

                if lastReTxPos == -1 or lastReTxPos < LHS:
                    #retransmission position start from LHS
                    lastReTxPos = LHS

                ''' Checking lastReTxPos before re-sending, because ACK may arrive between two reTx '''
                while lastReTxPos in acked_seq and lastReTxPos < min(1+num_pkt, RHS):
                    lastReTxPos += 1

                if lastReTxPos == min(1+num_pkt, RHS): #right boundary of window, marks the end of reTx
                    reTxFinished = True             #finishing current round of reTx
                    lastReTxPos = -1                #reset reTx position
                    LHS_lastmove = time.time()      #reset coarse timer
                    continue


                #Re-transmission
                log_info("Resend #{}".format(lastReTxPos))

                pkt = pktBySeq[lastReTxPos]
                
                net.send_packet("blaster-eth0", pkt)
                numReTX += 1
                totalByteSent += len_payload
                lastReTxPos += 1

                while lastReTxPos in acked_seq and lastReTxPos < min(1+num_pkt, RHS):
                    lastReTxPos += 1

                if lastReTxPos == min(1+num_pkt, RHS): #right boundary of window, marks the end of reTx
                    reTxFinished = True             #finishing current round of reTx
                    lastReTxPos = -1                #reset reTx position
                    LHS_lastmove = time.time()      #reset coarse timer
                    continue

            #send new packets
            elif RHS != num_pkt+1 and RHS-LHS+1 < SW:
                log_info("Extending RHS (Sending new data)")
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
                log_info("Send #{}".format(seq_num))
                net.send_packet("blaster-eth0", pkt)

                totalByteSent += len_payload
                goodByteSent += len_payload
                RHS += 1

    net.shutdown()


