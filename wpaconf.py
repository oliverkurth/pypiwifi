#!/usr/bin/python

import os
import json

def parse(file):
	mainconf = {}
	conf = mainconf
	with open(file) as f:
		for line in f:
			line = line.lstrip().rstrip()
			if line != '' and line[0] != '#':
				if line.endswith('{'):
					toks = line.split('=', 1)
					subname = toks[0]
					subconf = {}
					if subname in mainconf:
						mainconf[subname].append(subconf)
					else:
						mainconf[subname] = [subconf]
					conf = subconf
				elif line == '}':
					conf = mainconf
				else:
					toks = line.split('=', 1)
					if len(toks) == 2:
						conf[toks[0]] = toks[1]

	return mainconf

def unparsef(conf, f, level):
	for key, val in conf.iteritems():
		if type(val) == str or type(val) == unicode:
			f.write("{}{}={}\n".format("\t"*level, key, val))
		elif type(val) == list:
			for c in val:
				f.write("{}={{\n".format(key))
				unparsef(c, f, level+1)
				f.write("}\n")


def unparse(conf, file, level = 0, backup = True):
	if backup:
		if os.path.isfile(file):
			os.rename(file, file + ".saved")
	with open(file, "w+") as f:
		unparsef(conf, f, level)

def remove_network(conf, name):
	for n in conf['network']:
		if n['ssid'].strip('"') == name:
			conf['network'].remove(n)

def setnetwork(conf, name, password):
	remove_network(conf, name)

	if password != None:
		network = {
			"group":"CCMP TKIP WEP104 WEP40",
			"key_mgmt": "WPA-PSK",
			"pairwise": "CCMP TKIP",
			"priority": "5",
			"proto": "WPA RSN",
			"psk": '"' + password + '"',
			"ssid": '"' + name + '"'
		}
	else:
		network = {
			"key_mgmt": "NONE",
			"ssid": '"' + name + '"'
		}
	print type(name)
	conf['network'].append(network)

if __name__ == '__main__':
	conf = parse("/etc/wpa_supplicant/wpa_supplicant.conf")
#	print json.dumps(parse("/etc/wpa_supplicant/wpa_supplicant.conf"))
	unparse(conf, "/etc/wpa_supplicant/wpa_supplicant.conf")

