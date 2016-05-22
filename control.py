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
		return self.config['services'].values()

	def list_services_names(self):
		return self.config['services'].keys()

	def service_status(self, service):
		if not service in self.config['services'].values():
			if service in self.config['services'].keys():
				service = self.config['services'][service]
			else:
				return 'unknown service ' + service
		args = ['systemctl', 'is-failed', service ]
		if self.sudo_method == 'sudo':
			args = ['sudo'] + args
		p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output, error = p.communicate()
		return output.rstrip()

	def service(self, service, action):
		if action in ['start', 'stop', 'restart']:
			if service in self.list_services():
				return self.do_call(['systemctl', action, service])
			elif service in self.list_services_names():
				return self.do_call(['systemctl', action, self.config['services'][service]])

	FW_RULES_DIR = '/etc/fw-rules.d/'
	FW_CURRENT_RULE = '/etc/fw-rules.d/current.rules'

	def select_firewall(self, fw_name):
		self.do_call(['ln', '-fs', '{}/{}.rules'.format(self.FW_RULES_DIR, fw_name), self.FW_CURRENT_RULE])
		self.service('iptables', 'restart')

	def get_current_fw(self):
		return os.path.basename(os.path.realpath(self.FW_CURRENT_RULE))
