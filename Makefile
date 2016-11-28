
TESTDIR=mytests/

m:
	sudo python3 srpy.py middlebox.py
e:
	sudo python3 srpy.py blastee.py
r:
	sudo python3 srpy.py blaster.py

mn:
	sudo python start_mininet.py

ws:
	wireshark &
