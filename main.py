#!/usr/bin/python

from flask import Flask, render_template
import netifaces
import iwlib
import sys
import httplib2

import ping

app = Flask(__name__)

def get_public_ip():
	client = httplib2.Http()
	response, content = client.request('http://whatismyip.akamai.com')

	return content

def get_dns():
	dnslist = []
	lines = open("/etc/resolv.conf").read().split('\n')
	for l in lines:
		items = l.split()
		if len(items) > 0:
			if items[0] == 'nameserver':
				dnslist.append(items[1])
	return dnslist

def get_pings():
	ret = ping.ping_counted('8.8.8.8')
	return ret

@app.route('/api/public_ip')
def api_public_ip():
	return '{"public_ip": "' + get_public_ip() + '"}'

@app.route('/api/pings')
def api_pings():
	return '{"pings": "' + str(get_pings()) + '"}'

@app.route('/')
def show_netconfig():

	ifaces = netifaces.interfaces()
	addrs = {}
	for ni in ifaces:
		addrs[ni] = netifaces.ifaddresses(ni)[netifaces.AF_INET][0]['addr']

	gws = netifaces.gateways()

	gateway = gws['default'][netifaces.AF_INET][0]

	essids = {}
	for ni in ifaces:
		try:
			iwconfig = iwlib.get_iwconfig(ni)
			essids[ni] = iwconfig['ESSID']
		except IOError:
			essids[ni] = ''
			pass

	dnslist = get_dns()

	return render_template('netconfig.html',
		ifaces=ifaces, addrs=addrs, gateway=gateway,
		essids=essids, dns=dnslist[0])

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')

