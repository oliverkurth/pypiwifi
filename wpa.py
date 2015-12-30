#!/usr/bin/python

import subprocess
import os

class wpa_supplicant:

	def __init__(self, iface):
		self.interface = iface

	def wpa_cli(self, cmd, *args):
		co_args = ["./wpawrapper", "-i", self.interface, cmd]
		co_args.extend(args)
		return subprocess.check_output(co_args)

	def status(self):
		lines = self.wpa_cli('status').splitlines()
		status = {}
		for l in lines:
			key, val = l.split('=')
			status[key] = val
		return status

	def scan_results(self, do_scan=True):
		if do_scan:
			out = self.wpa_cli('scan')
		lines = self.wpa_cli('scan_results').splitlines()
		attrs = lines[0].split(' / ')
		bss_list = []
		for l in lines[1:]:
			vals = l.split("\t")
			bss = {}
			for i in range(0, len(attrs)):
				bss[attrs[i]] = vals[i]
			bss_list.append(bss)
		return bss_list

	def bss(self, id, do_scan=False):
		if do_scan:
			out = self.wpa_cli('scan')
		lines = self.wpa_cli('bss', id).splitlines()
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
			for i in range(0, len(attrs)):
				bss[attrs[i]] = vals[i]
			bss_list.append(bss)
		return bss_list


if __name__ == '__main__':
	wpa = wpa_supplicant('wlan0')
	print wpa.scan_results()

