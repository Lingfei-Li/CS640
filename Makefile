c:
	python3 srpy.py -c -s tr.py

t:
	python3 srpy.py -t -s tr.srpy myrouter.py

r:
	sudo python3 srpy.py myrouter.py

mn:
	sudo python start_mininet.py

cleanTest:
	rm test*.srpy
