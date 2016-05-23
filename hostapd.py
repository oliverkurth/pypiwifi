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
		lines = self.hostapd_cli('get_config').splitlines()
		config = {}
		for l in lines:
			key, val = l.split('=')
			config[key] = val
		return config

	def all_sta(self):
		lines = self.hostapd_cli('all_sta').splitlines()

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
				return None
		return stations

if __name__ == '__main__':
	ha = hostapd('alpha0')
	print ha.get_config()
	print ha.all_sta()

