#!/usr/bin/env python3

import time


class QueuedPkt:
    def __init__(self, pkt, nextIP, nextDev):
        self.pkt = pkt
        self.retry = 0
        self.arpSentTime = -1
        self.nextIP = nextIP
        self.nextDev = nextDev

    def outdated(self):
        return time.time() > self.arpSentTime + 1

    def arpSent(self):
        self.retry += 1
        self.arpSentTime = time.time()

    def retryLimitReached(self):
        return self.retry >= 5
