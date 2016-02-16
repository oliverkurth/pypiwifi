#!/usr/bin/python

import subprocess
import os

class Control:

	def __init__(self, config):
		self.config = config
		self.sudo_method = self.config['sudo_method']

	def do_call(self, args):
		cmdargs = []
		if self.sudo_method == 'sudo':
			cmdargs = ['sudo']
		cmd = cmdargs + args
		return subprocess.call(cmd)

	def halt(self):
		self.do_call([self.config['halt']] )

	def reboot(self):
		self.do_call([self.config['reboot']] )

	def list_services(self):
		return self.config['services'].keys()

	def service_status(self, service):
		if service in self.config['services'].keys():
			args = ['systemctl', 'is-failed', self.config['services'][service] ]
			if self.sudo_method == 'sudo':
				args = ['sudo'] + args
			p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			output, error = p.communicate()
			return output.rstrip()
		else:
			return 'unknown service ' + service

	def service(self, service, action):
		if service in self.list_services():
			if action in ['start', 'stop', 'restart']:
				return self.do_call(['systemctl', action, self.config['services'][service]])

