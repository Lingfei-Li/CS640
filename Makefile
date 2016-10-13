c:			#compile switchyard test scenarios
	~/switchyard-master/srpy.py -c -s test.py
	~/switchyard-master/srpy.py -c -s test2.py

t:			#run compiled switchyard test scenario1
	~/switchyard-master/srpy.py -t -s test.srpy myswitch_lru.py

t2:			#run compiled switchyard test scenario2
	~/switchyard-master/srpy.py -t -s test2.srpy myswitch_lru.py

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
