#!/usr/bin/env python

import json
import sys
import ipaddress

HOSTNAME_FILE="/etc/hostname"
HOSTS_FILE="/etc/hosts"
NETWORK_FILE="/etc/systemd/network/ap0.network"
DNSMASQ_FILE="/etc/dnsmasq.conf"
HOSTAPD_FILE="/etc/hostapd/hostapd-ap0.conf"

def write_hosts(config):
    fout = sys.stdout
    with open(HOSTS_FILE) as f:
        for line in f:
            if line.startswith("127.0.1.1"):
                fout.write("127.0.1.1\t{}\n".format(config["hostname"]))
            else:
                fout.write(line)

def write_hostname(config):
    fout = sys.stdout
    fout.write("{}\n".format(config["hostname"]))

def write_network(config):
    fout = sys.stdout
    with open(NETWORK_FILE) as f:
        for line in f:
            if line.startswith("Address="):
                fout.write("Address={}\n".format(config["ip"]))
            else:
                fout.write(line)

def write_dnsmasq(config):
    fout = sys.stdout

    ip = ipaddress.ip_address(config["ip"])
    nw = ipaddress.ip_network((ip, 24), strict=False)
    ip_from = nw.network_address + 129
    ip_to = nw.network_address + 250

    with open(DNSMASQ_FILE) as f:
        for line in f:
            if line.startswith("dhcp-range=ap0"):
                fout.write("dhcp-range=ap0,{},{},12h\n".format(str(ip_from), str(ip_to)))
            else:
                fout.write(line)

def write_hostapd(config):
    fout = sys.stdout

    with open(HOSTAPD_FILE) as f:
        for line in f:
            if line.startswith("ssid="):
                fout.write("ssid={}\n".format(config["ssid"]))
            elif line.startswith("wpa_passphrase="):
                fout.write("wpa_passphrase={}\n".format(config["passphrase"]))
            else:
                fout.write(line)

if __name__ == '__main__':
    with open("customize.json") as f:
        config = json.load(f)
    write_hosts(config)
    write_hostname(config)
    write_network(config)
    write_dnsmasq(config)
    write_hostapd(config)

