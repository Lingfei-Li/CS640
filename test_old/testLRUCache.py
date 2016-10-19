from myswitch_lru import lruCache

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
    print("operations test ok...")

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
    print("testing logic")
    testLogic()

