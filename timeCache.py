from threading import Timer, Thread, Event
import time

class timeCache:
    def __init__(self, timeoutSeconds):
        self.dstMap = {}
        self.dstElapsedTime = {}
        self.timeoutSeconds = timeoutSeconds
        self.refreshIntervalSeconds = 1
        self.startRefreshTask()

    def startRefreshTask(self):
        self.refreshCache()
        self.refreshThread = Timer(self.refreshIntervalSeconds, self.startRefreshTask)
        self.refreshThread.start()

    def stopRefreshTask(self):
        self.refreshThread.cancel()
    
    def refreshCache(self):
        self.dump()
        for dst, t in list(self.dstElapsedTime.items()):
            t += 1
            if t >= self.timeoutSeconds:
                self.remove(dst)
            else:
                self.dstElapsedTime[dst] = t

    def dump(self):
        if(not self.dstMap):
            print("timeCache is empty")
        else:
            print("dumping dstMap in timeCache:")
            for dst in self.dstMap:
                print(str(dst) + " -> " + str(self.dstMap[dst]))
        print("")

    def contains(self, dst):
        return dst in self.dstMap

    def get(self, dst):
        if dst in self.dstMap:
            return self.dstMap[dst]
        else:
            raise KeyError("timeCache.get - given dst is not in cache")

    def set(self, dst, dev):
        self.dstMap[dst] = dev
        self.dstElapsedTime[dst] = 0

    def remove(self, dst):
        if dst in self.dstMap and dst in self.dstElapsedTime:
            del self.dstMap[dst]
            del self.dstElapsedTime[dst]
        else:
            raise KeyError("remove - given dst is not in dstMap or dstElaspedTime")

def testOperations():
    interval = 1
    cache = timeCache(interval)
    cache.set(1, 2)
    print(cache.get(1))
    print(cache.contains(1))
    cache.dump()
    try:
        cache.get(-1)
        cache.remove(-1)
    except KeyError:
        pass
    try:
        cache.get(-1)
        cache.remove(-1)
    except KeyError:
        pass
    cache.stopRefreshTask()
    print("operations test ok...")

def testLogic():
    timeout = 2
    cache = timeCache(timeout)
    cache.set(1, 11)
    time.sleep(1+timeout)
    assert not cache.contains(1)    # after timeout

    cache.set(2, 22)
    time.sleep(1+timeout)
    assert not cache.contains(2)    # after timeout

    cache.set(1, 11)
    cache.set(2, 22)
    cache.set(3, 33)
    assert cache.contains(1)
    assert cache.contains(2)
    assert cache.contains(3)
    time.sleep(1+timeout)
    assert not cache.contains(1)
    assert not cache.contains(2)
    assert not cache.contains(3)

    cache.stopRefreshTask()
    print("logic test ok...")


if __name__ == "__main__":
    print("testing operations")
    testOperations()
    print("testing logic")
    testLogic()

