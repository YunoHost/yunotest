# -*- coding: utf-8 -*-

import sys
import os
import random
import json
import subprocess
import re
import urllib
import copy
import time
import pexpect
import string
import time

from contextlib import contextmanager

def make_test_domain():
  prefix = 'yunotest-'
  suffix = '.nohost.me'
  id = random.randint(1, 100000)
  return '%s%06d%s' % (prefix, id, suffix)

def make_random_password(length=32):
  choices = string.ascii_uppercase + string.ascii_lowercase + string.digits
  return ''.join(random.choice(choices) for _ in range(length))

class DigitalOceanServer:
  def __init__(self, domain, admin_password, doyunohost_path):
    self.domain = domain
    self.admin_password = admin_password
    self.doyunohost_path = doyunohost_path

  def deploy(self):
    print('Starting to deploy DigitalOcean server %s' % (self.domain))
    command = "python %s/deploy.py --domain %s --password %s" \
       % (self.doyunohost_path, self.domain, self.admin_password)
    self.run_local_cmd(command)
    print('Successfully deployed DigitalOcean server %s' % (self.domain))

  def remove(self):
    print('Removing DigitalOcean server %s' % (self.domain))
    command = "python %s/remove.py --domain %s" % (self.doyunohost_path, self.domain)
    self.run_local_cmd(command)
    print('Successfully removed DigitalOcean server %s' % (self.domain))

  def run_local_cmd(self, command, withoutput = False):
    print('> %s' % (command))
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    full_output = []
    while 1:
      line = process.stdout.readline()
      if not line:
        break
      if withoutput:
        full_output.append(line)
      if line.endswith('\n'):
        line = line[:-1]
      print line
    exit_code = process.returncode
    print('< exit code : %s' % (exit_code))
    
    if withoutput:
      ret = (''.join(full_output), exit_code)
    else:
      ret = exit_code
    return ret

  def run_remote_cmd(self, command, user='root'):
    ssh_command = 'ssh -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "%s@%s" "export TERM=linux; %s"' \
      % (user, self.ip, command)
    print('> %s' % (ssh_command))
    (output, exit_code) = pexpect.run(ssh_command, withexitstatus=True, timeout= 10*60, \
      events={'Administration password:':'%s\n' % (self.admin_password)})
    print(output)
    print('< exit code: %s' % (exit_code))
    return (output, exit_code)

  def setup(self):
    self.retrieve_ip()
    self.init_admin_account()
    self.deploy_scripts()
    self.run_remote_cmd("sudo yunohost user create -f Theodocle -l Chancremou -p grumpf -m 'theodocle.chancremou@%s' theodocle" \
      % (self.domain), 'admin')
      
  def retrieve_ip(self):
    print('Retrieving IP for %s' % (self.domain))
    command = "python %s/ip.py +short --domain %s" % (self.doyunohost_path, self.domain)
    (output, exitcode) = self.run_local_cmd(command, True)
    
    # http://glowingpython.blogspot.fr/2011/06/searching-for-ip-address-using-regular.html
    ip_re = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}'
                       +'(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
    match = ip_re.search(output)
    if match:
      self.ip = match.group()
 
    print('IP retrieved : %s' % self.ip)

  def init_admin_account(self):
    # init account creation
    self.run_remote_cmd("su - admin")
    
    # copy ssh keys
    self.run_remote_cmd("cp -r /root/.ssh /home/admin")
    self.run_remote_cmd("chown -R admin: /home/admin/.ssh")
    
    # try to connect as admin via ssh
    self.run_remote_cmd("pwd", 'admin')

  def deploy_scripts(self):
    scp_command = 'scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no %s "%s@%s:"' \
      % (os.path.join(os.path.dirname(__file__), 'install_app_wrapper.sh'), 'admin', self.ip)
    print('> %s' % (scp_command))
    (output, exit_code) = pexpect.run(scp_command, withexitstatus=True, timeout= 60)
    print('< exit code: %s' % (exit_code))
    
    self.run_remote_cmd('chmod +x /home/admin/install_app_wrapper.sh')

  def install_app(self, test_prop):
    test_prop_resolved = {}
    for key, value in test_prop['install'].items():
      test_prop_resolved[key] = value \
         .replace('${MAIN_DOMAIN}', self.domain) \
         .replace('${USER}', 'theodocle') \
         .replace('${RANDOM_PASSWORD}', make_random_password())
    install_args = urllib.urlencode(test_prop_resolved)
    #install_command = "sudo yunohost app install '%s' -a '%s'" % (test_prop['git'], install_args)
    install_command = "/home/admin/install_app_wrapper.sh '%s' '%s' /tmp/%s.installed_files.txt"  % (test_prop['git'], install_args, test_prop['id'])
    (install_logs, exitcode) = self.run_remote_cmd(install_command, 'admin')
    (installed_files, exitcode2) = self.run_remote_cmd("cat /tmp/%s.installed_files.txt" % (test_prop['git']))
    return (install_logs, exitcode, installed_files)
    
  def remove_app(self, test_prop):
    remove_command = "sudo yunohost app remove %s" % (test_prop['id'])
    return self.run_remote_cmd(remove_command, 'admin')

# http://preshing.com/20110920/the-python-with-statement-by-example/
@contextmanager
def deploy(do_server):
  do_server.deploy()
  try:
    yield do_server
  finally:
    do_server.remove()
