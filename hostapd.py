#!/usr/bin/python

import subprocess
import re

class hostapd:

	def __init__(self, iface):
		self.use_wrapper = False
		self.interface = iface

	def hostapd_cli(self, cmd, *args):
		if self.use_wrapper:
			cli = './wpawrapper'
		else:
			cli = '/usr/sbin/hostapd_cli'
		co_args = [cli, '-i', self.interface, cmd]
		co_args.extend(args)
		return subprocess.check_output(co_args)

	def get_config(self):
		config = {}
		try:
			lines = self.hostapd_cli('get_config').splitlines()
			for l in lines:
				key, val = l.split('=')
				config[key] = val
		except subprocess.CalledProcessError:
			pass
		return config

	# TODO: move to its own module
	LEASES_FILE = '/var/lib/misc/dnsmasq.leases'
	def dnsmasq_leases(self):
		clients = {}
		with open(self.LEASES_FILE, 'r') as f:
			for line in f:
				list = line.rstrip().split(' ')
				if len(list) == 5:
					mac = list[1]
					clients[mac] = {'lease_expires':list[0], 'ip':list[2], 'name':list[3], 'uuid': list[4]}
		return clients

	def station(self, bssid, get_lease=True):
		lines = self.hostapd_cli('sta', bssid).splitlines()

		station = {}
		for l in lines:
			if re.match('([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2})', l):
				if bssid != l:
					return None
			else:
				key, val = l.split('=')
				station[key] = val

		if get_lease:
			clients = self.dnsmasq_leases()
			if bssid in clients:
				station.update(clients[bssid])

		return station

	def all_sta(self, get_leases=True):
		try:
			lines = self.hostapd_cli('all_sta').splitlines()
		except subprocess.CalledProcessError:
			return {}

		stations = {}
		sta_id = None
		for l in lines:
			if re.match('([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2})', l):
				sta_id = l
				stations[sta_id] = {}
			elif sta_id != None:
				key, val = l.split('=')
				stations[sta_id][key] = val
			else:
				return {}

		if get_leases:
			clients = self.dnsmasq_leases()
			for id, sta in stations.iteritems():
				if id in clients:
					sta.update(clients[id])

		return stations

if __name__ == '__main__':
	ha = hostapd('alpha0')
	print ha.get_config()
	print ha.all_sta()

