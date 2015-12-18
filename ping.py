import os
import time

def ping(hostname):
	ret = os.system("ping -c 1 -w 2 " + hostname + " >/dev/null 2>&1")
	return ret

def ping_counted(hostname, count=10, sleeptime=1):
	n = 0;
	for i in range(0, count):
		ret = ping(hostname)
		if ret == 0:
			n += 1
		time.sleep(sleeptime)
	return n

		
