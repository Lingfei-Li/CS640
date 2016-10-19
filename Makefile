c:			#compile switchyard test scenarios
	~/switchyard-master/srpy.py -c -s test_lru.py
	~/switchyard-master/srpy.py -c -s test_to.py
	~/switchyard-master/srpy.py -c -s test_traffic.py

t:
	~/switchyard-master/srpy.py -t -s test_lru.srpy myswitch_lru.py
	~/switchyard-master/srpy.py -t -s test_to.srpy myswitch_to.py
	~/switchyard-master/srpy.py -t -s test_traffic.srpy myswitch_traffic.py

tt:
	~/switchyard-master/srpy.py -t -s test_traffic.srpy myswitch_traffic.py

taTest:
	~/switchyard-master/srpy.py -t -s lrutest.srpy myswitch_lru.py
	~/switchyard-master/srpy.py -t -s timeouttest.srpy myswitch_to.py
	~/switchyard-master/srpy.py -t -s traffictest.srpy myswitch_traffic.py


mn:			#start Mininet
	sudo python switchtopo.py

swLRU:		#start a LRU switch in Mininet xterm switch
	python3 srpy.py myswitch_lru.py

swTO:		#start a timeout switch
	python3 srpy.py myswitch_to.py

cacheTest:	#run tests for caches
	python3 testLRUCache.py
	python3 testTimeoutCache.py
	python3 testTrafficCache.py

cleanTest:
	rm test*.srpy
