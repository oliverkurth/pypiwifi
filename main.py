#!/usr/bin/python

from flask import Flask, render_template, request
import json
import netifaces
import sys
import os
import httplib2
import socket

import ping
from wpa import wpa_supplicant
from control import Control
from hostapd import hostapd
import wpaconf

app = Flask(__name__)
config = {}

def read_config():
	global config
	config_file = '/etc/pypiwifi/config.json'
	if not os.path.exists(config_file):
		config_file = 'config.json'
	print "reading config from {}".format(config_file)
	with open(config_file) as f:
		config = json.load(f)

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

@app.route('/api/net/ifaces')
def api_net_ifaces():
	ifaces = netifaces.interfaces()
	return json.dumps(ifaces)

@app.route('/api/net/addr', methods=['GET'])
def api_net_addr():
	iface = request.args.get('iface')
	addrs = []

	try:
		addrs = netifaces.ifaddresses(iface)
	except (ValueError):
		return json.dumps({"message": "no interface"}), 503

	try:
		inet_addrs = addrs[netifaces.AF_INET]
	except (KeyError):
		pass

	return json.dumps(addrs)

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

@app.route('/api/wpa/select_network', methods=['GET'])
def api_wpa_select_network():
	iface = request.args.get('iface')
	nwid = request.args.get('id')
	wpa = wpa_supplicant(iface)
	wpa.select_network(nwid)
	return json.dumps('OK')

@app.route('/api/wpa/bss', methods=['GET'])
def api_wpa_bss():
	iface = request.args.get('iface')
	id = request.args.get('id')
	wpa = wpa_supplicant(iface)
	return json.dumps(wpa.bss(id))

@app.route('/api/wpaconf/getconf', methods=['GET'])
def api_wpaconf_getconf():
	conf = wpaconf.parse('/etc/wpa_supplicant/wpa_supplicant.conf')
	return json.dumps(conf)

@app.route('/api/hostapd/sta', methods=['GET'])
def api_hostapd_sta():
	iface = request.args.get('iface')
	sta = request.args.get('sta')
	ha = hostapd(iface)
	if sta:
		result = ha.station(sta)
	else:
		result = ha.all_sta()
	return json.dumps(result)

@app.route('/api/control/power', methods=['GET'])
def api_control_power():
	action = request.args.get('action')
	control = Control(config['control'])
	if action == 'halt':
		control.halt()
	elif action == 'reboot':
		control.reboot()
	return json.dumps('OK')

@app.route('/api/control/service', methods=['GET'])
def api_control_service():
	action = request.args.get('action')
	service = request.args.get('service')
	control = Control(config['control'])
	control.service(service, action)
	return json.dumps('OK')

@app.route('/api/control/service_status', methods=['GET'])
def api_control_service_status():
	service = request.args.get('service')
	control = Control(config['control'])
	return json.dumps(control.service_status(service))

@app.route('/api/fw/select', methods=['GET'])
def api_fw_select():
	name = request.args.get('name')
	control = Control(config['control'])
	control.select_firewall(name)
	return json.dumps('OK')

def _range2color(value, min, max):
	green = (value - min) * 255 / (max - min)
	if green > 255:
		green = 255
	elif green < 0:
		green = 0
	red = 255 - green
	blue = 0
	return "%0.2x%0.2x%0.2x" % (red,green,blue)

@app.route('/wpa_scan', methods=['GET'])
def show_wpa_scan():
	iface = request.args.get('iface')
	wpa = wpa_supplicant(iface)
	result = wpa.scan_results()

	nwlist = wpa.list_networks()
	nwdict = {}
	for i in range(0, len(nwlist)-1):
		nwdict[nwlist[i]['ssid']] = nwlist[i]

	for i in range(0, len(result)):
		ssid = result[i]['ssid']
		if ssid in nwdict and ( nwdict[ssid]['bssid'] == 'any' or nwdict[ssid]['bssid'] == result[i]['bssid'] ):
			result[i]['nwid'] = nwdict[ssid]['id']

		level = int(result[i]['level'])
		# different drivers report different ranges - attempt to make it consistent
		if level < 0:
			level += 110
		result[i]['color'] = _range2color(level, 20, 80)

	return render_template('scan.html', iface=iface, bss_list=result)

def _wpa_status(wpa, iface):
	result = wpa.status()
	if result['wpa_state'] == 'COMPLETED':
		bss = {}
		if 'bssid' in result:
			bss = wpa.bss(result['bssid'])
		return render_template('status_complete.html', iface=iface, status=result, bss=bss)
	else:
		return render_template('status_other.html', iface=iface, status=result)

@app.route('/wpa_status', methods=['GET'])
def show_wpa_status():
	iface = request.args.get('iface')
	wpa = wpa_supplicant(iface)
	return _wpa_status(wpa, iface)

@app.route('/wpa_disconnect', methods=['GET'])
def show_wpa_disconnect():
	iface = request.args.get('iface')
	wpa = wpa_supplicant(iface)
	wpa.disconnect(iface)
	return _wpa_status(wpa, iface)

@app.route('/wpa_select', methods=['GET'])
def show_wpa_select():
	iface = request.args.get('iface')
	nwid = request.args.get('id')
	wpa = wpa_supplicant(iface)
	wpa.select_network(nwid)
	return _wpa_status(wpa, iface)

@app.route('/hostapd', methods=['GET'])
def show_hostapd():
	iface = request.args.get('iface')
	ha = hostapd(iface)
	return render_template('hostapd.html', iface=iface, ha=ha.get_config())

@app.route('/hostapd_stations', methods=['GET'])
def show_hostapd_stations():
	iface = request.args.get('iface')
	ha = hostapd(iface)
	return render_template('ha_stations.html', iface=iface, stations = ha.all_sta())

@app.route('/control')
def show_control():
	control = Control(config['control'])
	return render_template('control.html', services = control.list_services_names())

@app.route('/firewall')
def show_firewall():
	control = Control(config['control'])
	firewalls = config['firewalls']
	return render_template('firewall.html', firewalls=firewalls, current_fw=control.get_current_fw())

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
			if config_ifaces[ni].lower() == 'wpa':
				wpa = wpa_supplicant(ni)
				status = wpa.status()
				if status['wpa_state'] == 'COMPLETED':
					essids[ni] = status['ssid']
			elif config_ifaces[ni].upper() == 'AP':
				ha = hostapd(ni)
				ha_config = ha.get_config()
				essids[ni] = ha_config['ssid']

	dnslist = get_dns()

	return render_template('netconfig.html',
		ifaces=ifaces, addrs=addrs, gateway=gateway,
		essids=essids, dns=dnslist[0], config_ifaces=config_ifaces)

_js_escapes = {
        '\\': '\\u005C',
        '\'': '\\u0027',
        '"': '\\u0022',
        '>': '\\u003E',
        '<': '\\u003C',
        '&': '\\u0026',
        '=': '\\u003D',
        '-': '\\u002D',
        ';': '\\u003B',
        u'\u2028': '\\u2028',
        u'\u2029': '\\u2029'
}
# Escape every ASCII character with a value less than 32.
_js_escapes.update(('%c' % z, '\\u%04X' % z) for z in xrange(32))
def jinja2_escapejs_filter(value):
        retval = []
        for letter in value:
                if _js_escapes.has_key(letter):
                        retval.append(_js_escapes[letter])
                else:
                        retval.append(letter)

        return "".join(retval)
app.jinja_env.filters['escapejs'] = jinja2_escapejs_filter

read_config()
if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')

