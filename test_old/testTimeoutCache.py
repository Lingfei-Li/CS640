import time
from myswitch_to import timeoutCache

def testOperations():
    interval = 1
    cache = timeoutCache(interval)
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
    cache = timeoutCache(timeout)
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

