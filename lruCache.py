
class lruCache:

    dstMap = {}

    freshness = {}

    limit = 5

    cnt = 0

    def dump(self):
        if(not self.dstMap):
            print("lruCache is empty")
        else:
            print("dumping dstMap in lruCache:")
            for dst in self.dstMap:
                print(str(dst) + " -> " + str(self.dstMap[dst]) + " fresh: " + str(self.freshness[dst]))
        print("")

    def contains(self, dst):
        return dst in self.dstMap

    def get(self, dst):
        if dst in self.dstMap:
            self.cnt += 1
            self.freshness[dst] = self.cnt
            return self.dstMap[dst]
        else:
            raise KeyError("lruCache.get - given dst is not in cache")

    def set(self, dst, dev):
        if not self.contains(dst):
            while len(self.dstMap) >= self.limit:
                self.kickLRU()
        self.cnt += 1
        self.freshness[dst] = self.cnt
        self.dstMap[dst] = dev

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
        if dst in self.dstMap:
            del self.dstMap[dst]
            del self.freshness[dst]
        else:
            raise KeyError("lruCache.remove - given dst is not in cache")


def testOperations():
    cache = lruCache()
    cache.set(1, 2)

    cache.dump()

    print(cache.contains(1))

    cache.kickLRU()

    cache.dump()

def testLRUNature():
    cache = lruCache()
    cache.set(1, 11)
    cache.set(2, 22)
    cache.set(3, 33)
    cache.set(4, 44)
    cache.set(5, 55)
    cache.dump()

    cache.set(1, 111)
    cache.dump()
    cache.set(1, 1111)
    cache.dump()
    cache.set(6, 66)
    cache.dump()
    assert not cache.contains(2)

    cache.get(3)
    cache.set(7, 77)
    cache.dump()
    assert cache.contains(3)
    assert not cache.contains(4)


if __name__ == "__main__":
    print("testing operations")
    testOperations()
    print("testing LRU nature")
    testLRUNature()

