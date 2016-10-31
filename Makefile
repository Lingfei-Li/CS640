c:
	python3 srpy.py -c -s tr1.py
	python3 srpy.py -c -s tr2.py

t:
	python3 srpy.py -t -s tr2.srpy myrouter.py

r:
	sudo python3 srpy.py myrouter.py

mn:
	sudo python start_mininet.py

cleanTest:
	rm test*.srpy
