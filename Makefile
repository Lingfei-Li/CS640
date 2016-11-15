
TESTDIR=mytests/

c:
	python3 srpy.py -c -s $(TESTDIR)icmp_test.py
	python3 srpy.py -c -s $(TESTDIR)fwd_test.py
	#python3 srpy.py -c -s $(TESTDIR)tr2_3.py
	python3 srpy.py -c -s $(TESTDIR)tr2_4.py
	python3 srpy.py -c -s $(TESTDIR)tr2_5.py


t:
	#python3 srpy.py -t -s $(TESTDIR)tr2_3.srpy myrouter.py
	python3 srpy.py -t -s $(TESTDIR)tr2_4.srpy myrouter.py
	python3 srpy.py -t -s $(TESTDIR)tr2_5.srpy myrouter.py
	python3 srpy.py -t -s $(TESTDIR)fwd_test.srpy myrouter.py
	python3 srpy.py -t -s $(TESTDIR)icmp_test.srpy myrouter.py

ta:
	#python3 srpy.py -t -s test_router.srpy myrouter.py
	#python3 srpy.py -t -s p2/routertest1.srpy myrouter.py
	#python3 srpy.py -t -s p2/routertest2.srpy myrouter.py
	python3 srpy.py -t -s p2/routertest3.srpy myrouter.py
	python3 srpy.py -t -s p2/routertest4.srpy myrouter.py
	python3 srpy.py -t -s p2/routertest5.srpy myrouter.py
	python3 srpy.py -t -s p2/routertest6.srpy myrouter.py
	python3 srpy.py -t -s icmp_tests.srpy myrouter.py
	python3 srpy.py -t -s more_tests.srpy myrouter.py

r:
	sudo python3 srpy.py myrouter.py

mn:
	sudo python start_mininet.py

ct:
	rm $(TESTDIR)tr*.srpy

ws:
	wireshark &
