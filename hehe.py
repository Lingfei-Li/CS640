#!/usr/bin/env python3

import lruCache as cache

a = cache.lruCache()

a.set(1, 2)

print(a.get(1))

a.dump()

print(a.contains(1))

a.kick(1)

print(a.getCnt())

a.dump()
