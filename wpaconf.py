#!/usr/bin/python

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
		if type(val) == str:
			f.write("{}{}={}\n".format("\t"*level, key, val))
		elif type(val) == list:
			for c in val:
				f.write("{}={{\n".format(key))
				unparsef(c, f, level+1)
				f.write("}\n")


def unparse(conf, file, level = 0):
	with open(file, "w+") as f:
		unparsef(conf, f, level)

if __name__ == '__main__':
	conf = parse("/etc/wpa_supplicant/wpa_supplicant.conf")
#	print json.dumps(parse("/etc/wpa_supplicant/wpa_supplicant.conf"))
	unparse(conf, "/tmp/wpa_supplicant.conf")

