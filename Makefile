c:			#compile switchyard test scenarios
	~/switchyard-master/srpy.py -c -s test.py
	~/switchyard-master/srpy.py -c -s test2.py
	~/switchyard-master/srpy.py -c -s testLRUSwitch1.py
	~/switchyard-master/srpy.py -c -s testLRUSwitch2.py
	~/switchyard-master/srpy.py -c -s testTOSwitch1.py

t:			#run compiled switchyard test scenario
	~/switchyard-master/srpy.py -t -s testLRUSwitch1.srpy myswitch_lru.py

t2:			#run compiled switchyard test scenario
	~/switchyard-master/srpy.py -t -s testLRUSwitch2.srpy myswitch_lru.py

t3:			#run compiled switchyard test scenario
	~/switchyard-master/srpy.py -t -s testTOSwitch1.srpy myswitch_to.py

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
