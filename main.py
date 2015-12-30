#!/usr/bin/python

from flask import Flask, render_template, request
import netifaces
import iwlib
import sys
import httplib2
import socket

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

def get_pings(host='8.8.8.8'):
	ret = ping.ping_counted(host)
	return ret

def get_uptime():
	with open('/proc/uptime', 'r') as f:
		return float(f.readline().split()[0])

@app.route('/api/public_ip')
def api_public_ip():
	ip = get_public_ip();
	hostname = 'unresolved'
	try:
		byaddr = socket.gethostbyaddr(ip)
		hostname = byaddr[0]
	except socket.herror:
		pass

	return '{"public_ip": "' + ip + '", "public_hostname": "' + hostname + '"}'

@app.route('/api/client_ip')
def api_client_ip():
	return '{"client_ip": "' + request.remote_addr + '"}'

@app.route('/api/pings', methods=['GET'])
def api_pings():
	host = request.args.get('host')
	return '{"pings": "' + str(get_pings(host)) + '"}'

@app.route('/api/uptime')
def api_uptime():
	return '{"uptime":' + str(get_uptime()) + '}'

@app.route('/')
def show_netconfig():

	ifaces = netifaces.interfaces()
	addrs = {}
	for ni in ifaces:
		try:
			addrs[ni] = netifaces.ifaddresses(ni)[netifaces.AF_INET][0]['addr']
		except KeyError:
			addrs[ni] = 'None'
			pass

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

