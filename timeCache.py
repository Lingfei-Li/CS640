from threading import Timer, Thread, Event
import time

class timeCache:

    dstMap = {}


    def __init__(self, refreshIntervalSeconds):
        self.refreshIntervalSeconds = refreshIntervalSeconds
        self.refreshThread = Timer(self.refreshIntervalSeconds, self.startRefreshTask)
        self.refreshThread.start()

    def startRefreshTask(self):
        self.refreshCache()
        self.refreshThread = Timer(self.refreshIntervalSeconds, self.startRefreshTask)
        self.refreshThread.start()

    def stopRefreshTask(self):
        print("stopping task...")
        self.refreshThread.cancel()
    
    def refreshCache(self):
        print("refreshing cache...")
        if len(self.dstMap) > 0:
            self.kickRandom()

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

    def kickRandom(self):
        if not len(self.dstMap) == 0:
            self.dstMap.popitem()

def testOperations():
    interval = 1
    cache = timeCache(interval)
    cache.set(1, 2)
    print(cache.get(1))
    print(cache.contains(1))
    cache.kickRandom()
    cache.dump()
    time.sleep(interval);
    cache.stopRefreshTask()
    print("operations test ok...")

def testLogic():
    #TODO: add more logic testing and comments
    interval = 1
    cache = timeCache(interval)
    cache.set(1, 11)
    cache.dump()
    time.sleep(2*interval)
    assert not cache.contains(1)    # after 2 seconds
    cache.stopRefreshTask()
    print("logic test ok...")

if __name__ == "__main__":
    print("testing operations")
    testOperations()
    print("testing logic")
    testLogic()

