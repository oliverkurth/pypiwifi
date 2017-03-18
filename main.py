#!/usr/bin/python

from flask import Flask, render_template, request
import json
import netifaces
import sys
import os
import httplib2
import socket
import copy

import ping
from wpa import wpa_supplicant
from control import Control
from hostapd import hostapd
import wpaconf

app = Flask(__name__)
config = {}

main_menu = [
        {"name" : "main", "link" : "/", "label" : "Main"},
        {"name" : "control", "link" : "/control", "label" : "Control"},
	{"name" : "firewall", "link" : "/firewall", "label" : "Firewall"}
]

wpa_menu = [
        {"name" : "main", "link" : "/", "label" : "Main"},
        {"name" : "status", "link" : "/wpa_status", "label" : "Status"},
        {"name" : "networks", "link" : "/wpaconf/networks", "label" : "Networks"},
        {"name" : "scan", "link" : "/wpa_scan", "label" : "Scan"}
]

hostapd_menu = [
        {"name" : "main", "link" : "/", "label" : "Main"},
        {"name" : "ap", "link" : "/hostapd", "label" : "AP"},
        {"name" : "stations", "link" : "/hostapd_stations", "label" : "Connected Stations"}
]

def menu_add_params(orig_menu, params):
	# copy orig_menu to menu
	menu = copy.deepcopy(orig_menu)
	for item in menu:
		for i, k in enumerate(params.keys()):
			if i == 0:
				item["link"] += '?' + k + '=' + params[k]
			else:
				item["link"] += '&' + k + '=' + params[k]
	return menu

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

	return content.strip()

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

def _net_addr(iface):
	addrs = []
	inet_addrs = []

	try:
		addrs = netifaces.ifaddresses(iface)
	except (ValueError):
		return json.dumps({"message": "no interface"}), 503

	try:
		inet_addrs = addrs[netifaces.AF_INET]
	except (KeyError):
		pass

	return inet_addrs

@app.route('/api/net/addr', methods=['GET'])
def api_net_addr():
	iface = request.args.get('iface')
	addrs = _net_addr(iface)
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
	getbss = request.args.get('getbss')
	getaddrs = request.args.get('getaddrs')
	wpa = wpa_supplicant(iface)
	status = wpa.status()
	if getbss != None and 'bssid' in status:
		status['bss'] = wpa.bss(status['bssid'])
	if getaddrs != None:
		status['addrs'] = _net_addr(iface)

	return json.dumps(status)

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

@app.route('/api/wpa/disconnect', methods=['GET'])
def api_wpa_disconnect():
	iface = request.args.get('iface')
	wpa = wpa_supplicant(iface)
	wpa.disconnect(iface)
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

def _wpa_scan_list(iface):
	wpa = wpa_supplicant(iface)
	scan_list = wpa.scan_results()

	nwlist = wpa.list_networks()
	nwdict = {}
	for nw in nwlist:
		nwdict[nw['ssid']] = nw

	for bss in scan_list:
		ssid = bss['ssid']
		if ssid in nwdict and ( nwdict[ssid]['bssid'] == 'any' or nwdict[ssid]['bssid'] == bss['bssid'] ):
			bss['nwid'] = nwdict[ssid]['id']

		level = int(bss['level'])
		# different drivers report different ranges - attempt to make it consistent
		if level < 0:
			level += 110
		bss['color'] = _range2color(level, 20, 80)

	return scan_list

@app.route('/api/wpa/scan_list', methods=['GET'])
def api_wpa_scan_list():
	iface = request.args.get('iface')
	return json.dumps(_wpa_scan_list(iface))

def wpaconf_networks(conf):
	names = []
	try:
		networks = conf['network']
		names = [ n['ssid'].strip('"') for n in networks ]
	except KeyError:
		pass
	return names

@app.route('/api/wpaconf/networks', methods=['GET'])
def api_wpaconf_networks():
	conf = wpaconf.parse('/etc/wpa_supplicant/wpa_supplicant.conf')
	return json.dumps(wpaconf_networks(conf))

@app.route('/api/wpaconf/setnetwork', methods=['GET'])
def api_wpaconf_setnetwork():
	name = request.args.get('name')
	passwd = request.args.get('password')
	conf = wpaconf.parse('/etc/wpa_supplicant/wpa_supplicant.conf')
	wpaconf.setnetwork(conf, name, passwd)
	wpaconf.unparse(conf, '/etc/wpa_supplicant/wpa_supplicant.conf')
	return json.dumps('OK')

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
	scan_list = _wpa_scan_list(iface)
	return render_template('scan.html', iface=iface, bss_list=scan_list,
		menu = menu_add_params(wpa_menu, {"iface" : iface}), active_name="scan")

@app.route('/wpa_status', methods=['GET'])
def show_wpa_status():
	iface = request.args.get('iface')
	return render_template('wpa_status.html',
		iface=iface,
		menu = menu_add_params(wpa_menu, {"iface" : iface}), active_name="status")

@app.route('/wpa_select', methods=['GET'])
def show_wpa_select():
	iface = request.args.get('iface')
	nwid = request.args.get('id')
	wpa = wpa_supplicant(iface)
	wpa.select_network(nwid)
	return render_template('wpa_status.html',
		iface=iface,
		menu = menu_add_params(wpa_menu, {"iface" : iface}), active_name="status")

@app.route('/hostapd', methods=['GET'])
def show_hostapd():
	iface = request.args.get('iface')
	ha = hostapd(iface)
	return render_template('hostapd.html',
		iface=iface, ha=ha.get_config(),
		menu = menu_add_params(hostapd_menu, {"iface" : iface}), active_name="ap")

@app.route('/wpaconf/networks')
def show_wpaconf_networks():
	iface = request.args.get('iface')
	conf = wpaconf.parse('/etc/wpa_supplicant/wpa_supplicant.conf')
	names = wpaconf_networks(conf)
	return render_template('networks.html', networks=names, iface=iface,
		menu = menu_add_params(wpa_menu, {"iface" : iface}), active_name="networks")

@app.route('/wpaconf/edit_network')
def show_wpa_edit_network():
	iface = request.args.get('iface')
	ssid = request.args.get('ssid', '')
	password = request.args.get('password', '')
	return render_template('wpa_network.html', ssid=ssid, password=password, iface=iface,
		menu = menu_add_params(wpa_menu, {"iface" : iface}), active_name="networks")

@app.route('/hostapd_stations', methods=['GET'])
def show_hostapd_stations():
	iface = request.args.get('iface')
	ha = hostapd(iface)
	return render_template('ha_stations.html',
		iface=iface, stations = ha.all_sta(),
		menu = menu_add_params(hostapd_menu, {"iface" : iface}), active_name="stations")

@app.route('/control')
def show_control():
	control = Control(config['control'])
	return render_template('control.html',
		services = control.list_services_names(),
		menu=main_menu, active_name="control")

@app.route('/firewall')
def show_firewall():
	control = Control(config['control'])
	firewalls = config['firewalls']
	return render_template('firewall.html',
		firewalls=firewalls, current_fw=control.get_current_fw(),
		menu=main_menu, active_name="firewall")

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
				try:
					wpa = wpa_supplicant(ni)
					status = wpa.status()
					if status['wpa_state'] == 'COMPLETED':
						essids[ni] = status['ssid']
				except:
					pass
			elif config_ifaces[ni].upper() == 'AP':
				ha = hostapd(ni)
				ha_config = ha.get_config()
				try:
					essids[ni] = ha_config['ssid']
				except KeyError:
					pass

	dnslist = get_dns()

	return render_template('netconfig.html',
		ifaces=ifaces, addrs=addrs, gateway=gateway,
		essids=essids, dns=dnslist[0], config_ifaces=config_ifaces,
		menu=main_menu, active_name="main")

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

