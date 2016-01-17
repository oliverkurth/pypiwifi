#!/usr/bin/python

import subprocess
import os
import time

class wpa_supplicant:

	def __init__(self, iface):
		self.use_wrapper = False
		self.interface = iface

	def f2c(self, f):
		return int((f-2407)/5)

	def wpa_cli(self, cmd, *args):
		if self.use_wrapper:
			cli = './wpawrapper'
		else:
			cli = '/sbin/wpa_cli'
		co_args = [cli, '-i', self.interface, cmd]
		co_args.extend(args)
		return subprocess.check_output(co_args)

	def status(self):
		lines = self.wpa_cli('status').splitlines()
		status = {}
		for l in lines:
			key, val = l.split('=')
			status[key] = val
		if 'freq' in status:
			status['channel'] = self.f2c(int(status['freq']))
		return status

	def scan_results(self, do_scan=True):
		if do_scan:
			out = self.wpa_cli('scan')
			time.sleep(1)
		lines = self.wpa_cli('scan_results').splitlines()
		attrs = ('bssid', 'frequency', 'level', 'flags', 'ssid')
		bss_list = []
		for l in lines[1:]:
			vals = l.split("\t")
			bss = {}
			for i in range(0, len(attrs)):
				bss[attrs[i]] = vals[i]
			bss_list.append(bss)
		return bss_list

	def bss(self, nwid, do_scan=False):
		if do_scan:
			out = self.wpa_cli('scan')
		lines = self.wpa_cli('bss', nwid).splitlines()
		bss = {}
		for l in lines:
			key, val = l.split('=')
			bss[key] = val
		return bss

	# network id / ssid / bssid / flags
	def list_networks(self):
		lines = self.wpa_cli('list_networks').splitlines()
		attrs = ('id', 'ssid', 'bssid', 'flags')
		bss_list = []
		for l in lines[1:]:
			vals = l.split()
			bss = {}
			for i in range(0, len(attrs)-1):
				bss[attrs[i]] = vals[i]
			bss_list.append(bss)
		return bss_list

	def disconnect(self, nwid):
		self.wpa_cli('disconnect')
		return

	def select_network(self, nwid):
		self.wpa_cli('select_network', nwid)
		return

if __name__ == '__main__':
	wpa = wpa_supplicant('wlan0')
	print wpa.scan_results()

