
from operator import itemgetter

class lruCache:
    def __init__(self):
        self.dstMap = {}
        self.freshness = {}
        self.limit = 5
        self.cnt = 0

    def dumpSorted(self):
        if not self.dstMap:
            print("lruCache is empty")
        else:
            print("dst -> freshness")
            for dst, freshness in sorted(self.freshness.items(), key=itemgetter(1)):
                print(str(dst) + " -> " + str(freshness));

    def dump(self):
        if not self.dstMap:
            print("lruCache is empty")
        else:
            print("dumping dstMap in lruCache:")
            for dst in self.dstMap:
                print(str(dst) + " -> " + str(self.dstMap[dst]) + " fresh: " + str(self.freshness[dst]))
        print("")

    def contains(self, dst):
        return dst in self.dstMap

    def get(self, dst):
        if dst in self.dstMap:          #return mapped port and upadte to most recently used
            self.freshness[dst] = self.getFreshness()
            return self.dstMap[dst]
        else:
            raise KeyError("lruCache.get - given dst is not in cache")

    def set(self, dst, dev):
        if not self.contains(dst):      #DNE. insert
            while len(self.dstMap) >= self.limit:       #table full
                self.kickLRU() 
            self.freshness[dst] = self.getFreshness() #add (dst, dev) as most recently used
            self.dstMap[dst] = dev
        else:                           #exists. update
            if not dev == self.dstMap[dst]:
                self.dstMap[dst] = dev         #update port info w/o modifying LRU order

    def kickLRU(self):
        lruDst = None
        lruFreshness = -1
        for dst, fresh in self.freshness.items():
            if lruFreshness == -1 or lruFreshness > fresh:
                lruDst = dst
                lruFreshness = fresh
        if not lruFreshness == -1:
            self.remove(lruDst)

    def remove(self, dst):
        if dst in self.dstMap and dst in self.freshness:
            del self.dstMap[dst]
            del self.freshness[dst]
        else:
            raise KeyError("lruCache.remove - given dst is not in cache")

    def getFreshness(self):
        self.cnt += 1
        return self.cnt



def testOperations():
    cache = lruCache()
    cache.set(1, 2)
    cache.dump()
    print(cache.contains(1))
    cache.kickLRU()
    cache.set(2, 22)
    cache.set(3, 33)
    cache.set(1, 11)
    cache.get(2)
    cache.dumpSorted()
    print("logic test ok...")

def testLogic():
    cache = lruCache()

    #no kick
    cache.set(1, 11)
    cache.set(2, 22)
    cache.set(3, 33)
    cache.set(4, 44)
    cache.set(5, 55)
    cache.dump()

    #update w/o new freshness
    cache.set(1, 111)
    cache.dump()
    assert cache.freshness[1] == 1

    #same mapping, nothing happens
    cache.set(1, 111)
    cache.dump()
    assert cache.freshness[1] == 1

    #get() set new freshness. 1 becomes MRU, 2 becomes LRU
    cache.get(1)
    cache.dump()
    assert cache.freshness[1] == 6

    #table full, kick LRU (2)
    cache.set(6, 66)
    cache.dump()
    assert not cache.contains(2)
    assert cache.freshness[6] == 7

    #another test for get() and set()
    cache.get(3)
    cache.set(7, 77)
    cache.dump()
    assert cache.contains(3)
    assert not cache.contains(4)
    print("logic test ok...")


if __name__ == "__main__":
    print("testing operations")
    testOperations()
    #print("testing logic")
    #testLogic()

