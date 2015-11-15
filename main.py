#!/usr/bin/python

from flask import Flask, render_template
import netifaces

app = Flask(__name__)

@app.route('/iface/<name>')
def show_iface(name):
	addrs = netifaces.ifaddresses(name)

	address = addrs[netifaces.AF_INET][0]['addr']

	gws = netifaces.gateways()

	gateway = gws['default'][netifaces.AF_INET][0]

	return render_template('interface.html', name=name, address=address, gateway=gateway)

@app.route('/')
def show_iface_main():
	return show_iface('eth0')

if __name__ == '__main__':
	app.run(host='0.0.0.0')

