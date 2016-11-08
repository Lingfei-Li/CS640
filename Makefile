
TESTDIR=mytests/

c:
	python3 srpy.py -c -s $(TESTDIR)tr1.py
	python3 srpy.py -c -s $(TESTDIR)tr2_1.py
	python3 srpy.py -c -s $(TESTDIR)tr2_2.py
	python3 srpy.py -c -s $(TESTDIR)tr2_3.py
	python3 srpy.py -c -s $(TESTDIR)tr2_4.py
	python3 srpy.py -c -s $(TESTDIR)tr2_5.py

t:
	#python3 srpy.py -t -s $(TESTDIR)tr1.srpy myrouter.py
	#python3 srpy.py -t -s $(TESTDIR)tr2_1.srpy myrouter.py
	#python3 srpy.py -t -s $(TESTDIR)tr2_2.srpy myrouter.py
	#python3 srpy.py -t -s $(TESTDIR)tr2_3.srpy myrouter.py
	#python3 srpy.py -t -s $(TESTDIR)tr2_4.srpy myrouter.py
	python3 srpy.py -t -s $(TESTDIR)tr2_5.srpy myrouter.py

r:
	sudo python3 srpy.py myrouter.py

mn:
	sudo python start_mininet.py

ct:
	rm $(TESTDIR)tr*.srpy

ws:
	wireshark &
