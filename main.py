#!/usr/bin/python

from flask import Flask, render_template, request
import json
import netifaces
import sys
import httplib2
import socket

import ping
from wpa import wpa_supplicant

app = Flask(__name__)
config = {}

def read_config():
	global config
	f = open('config.json', 'r')
	config = json.load(f)
	f.close()

def get_public_ip():
	client = httplib2.Http()
	response, content = client.request(config['public_ip_url'])

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


@app.route('/api/wpa/status', methods=['GET'])
def api_wpa_status():
	iface = request.args.get('iface')
	wpa = wpa_supplicant(iface)
	return json.dumps(wpa.status())

@app.route('/api/wpa/scan_results', methods=['GET'])
def api_wpa_scan_results():
	iface = request.args.get('iface')
	wpa = wpa_supplicant(iface)
	result = wpa.scan_results()
	return json.dumps(result)


@app.route('/wpa_scan', methods=['GET'])
def show_wpa_scan():
	iface = request.args.get('iface')
	wpa = wpa_supplicant(iface)
	result = wpa.scan_results()
	return render_template('scan.html', bss_list=result)

@app.route('/wpa_status', methods=['GET'])
def show_wpa_status():
	iface = request.args.get('iface')
	wpa = wpa_supplicant(iface)
	result = wpa.status()
	if result['wpa_state'] == 'COMPLETED':
		bss = {}
		if 'bssid' in result:
			bss = wpa.bss(result['bssid'])
		return render_template('status_complete.html', name=iface, status=result, bss=bss)
	else:
		return render_template('status_other.html', name=iface, status=result)

@app.route('/')
def show_netconfig():

	ifaces = netifaces.interfaces()
	config_ifaces = config['interfaces']
	addrs = {}
	for ni in ifaces:
		try:
			addrs[ni] = netifaces.ifaddresses(ni)[netifaces.AF_INET][0]['addr']
		except KeyError:
			addrs[ni] = 'None'
			pass

	gateway = 'None'
	gws = netifaces.gateways()
	if 'default' in gws and netifaces.AF_INET in gws['default']:
		gateway = gws['default'][netifaces.AF_INET][0]

	essids = {}
	for ni in ifaces:
		essids[ni] = ''
		if ni in config_ifaces:
			if config_ifaces[ni] == 'wpa':
				wpa = wpa_supplicant(ni)
				status = wpa.status()
				if status['wpa_state'] == 'COMPLETED':
					essids[ni] = status['ssid']

	dnslist = get_dns()

	return render_template('netconfig.html',
		ifaces=ifaces, addrs=addrs, gateway=gateway,
		essids=essids, dns=dnslist[0], config_ifaces=config_ifaces)

if __name__ == '__main__':
	app.debug = True
	read_config()
	app.run(host='0.0.0.0')

