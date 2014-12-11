#!/bin/python

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
from contextlib import contextmanager

# http://preshing.com/20110920/the-python-with-statement-by-example/
class DigitalOceanServer():
  def __init__(self, domain, ssh_key, doyunohost_path, admin_password):
    self.domain = domain
    self.ssh_key = ssh_key
    self.doyunohost_path = doyunohost_path
    self.admin_password = admin_password

  def deploy(self):
    print('Starting to deploy DigitalOcean server %s' % (self.domain))
    command = "python %s/deploy.py --domain %s --ssh-key-name julaptop --password %s" \
       % (self.doyunohost_path, self.domain, self.admin_password)
    os.system(command)
    print('Successfully deployed DigitalOcean server %s' % (self.domain))

  def remove(self):
    print('Removing DigitalOcean server %s' % (self.domain))
    command = "python %s/remove.py --domain %s" % (self.doyunohost_path, self.domain)
    os.system(command)
    print('Successfully removed DigitalOcean server %s' % (self.domain))

  def run_remote_cmd(self, command):
    print('Running command : %s' % (command))
    ssh_wrapper = 'ssh -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "root@%s" "export TERM=linux; %s"' \
      % (self.ip, command)
    (command_output, exitstatus) = pexpect.run(ssh_wrapper, withexitstatus=True, \
      events={'Administration password:':'%s\n' % (self.admin_password)})
    print command_output
    if not exitstatus:
      print('Command [%s] OK' % (command))
    else:
      print('Command [%s] NOT OK. Returned : %s' % (command, exitstatus))
    
  def setup(self):
    self.retrieve_ip()
    self.run_remote_cmd("yunohost user create -f Theodocle -l Chancremou -p grumpf -m 'theodocle.chancremou@%s' theodocle" \
      % (self.domain))

  def retrieve_ip(self):
    print('Retrieving IP for %s' % (self.domain))
    
    # wait for a maximum of 5 min
    timeout = 5 * 60
    start_time = time.time()
    current_time = 0
    while current_time < timeout and not hasattr(self, 'ip'):
      current_time = time.time()-start_time
      
      command = "dig +short @dynhost.yunohost.org %s" % (self.domain)
      proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
      output = str(proc.read())
      
      # http://glowingpython.blogspot.fr/2011/06/searching-for-ip-address-using-regular.html
      ip_re = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}'
                         +'(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
      match = ip_re.search(output)
      if match:
        self.ip = match.group()
      
      # sleep for 15s
      time.sleep(15)
      
    if current_time >= timeout:
      raise RuntimeError("Timeout expired when trying to get IP address for %s" % (self.domain))
    else:
      print('IP retrieved in %s s' % current_time)

  def install_app(self, test_prop):
    test_prop_resolved = {}
    for key, value in test_prop['install'].items():
      test_prop_resolved[key] = value.replace('${MAIN_DOMAIN}', self.domain)
    install_args = urllib.urlencode(test_prop_resolved)
    install_command = "yunohost app install '%s' -a '%s'" % (test_prop['git'], install_args)
    self.run_remote_cmd(install_command)

@contextmanager
def deploy(do_server):
  do_server.deploy()
  try:
    yield do_server
  finally:
    do_server.remove()

def load_test_prop( test_filename ):
  if not os.path.exists( test_filename ):
    print 'Provided test file does not exists : %' % (test_filename)
  test_prop = {}
  with open(test_filename) as test_file:
    test_prop.update( json.loads(str(test_file.read())) )
  return test_prop

def make_test_domain():
  prefix = 'yunotest-'
  suffix = '.nohost.me'
  id = random.randint(1, 100000)
  return '%s%06d%s' % (prefix, id, suffix)
  
def usage():
  print 'Usage : %s --test-file <testfile.json> --doyunohost <path> --ssh-key <ssh_key>' % (__file__)

if __name__ == '__main__':
  
  if '--test-file' not in sys.argv \
    or  '--doyunohost' not in sys.argv \
    or  '--ssh-key' not in sys.argv:
      usage()
      sys.exit(1)

  for key, arg in enumerate(sys.argv):
    if arg == '--test-file':
      test_file = sys.argv[key+1]
    if arg == '--doyunohost':
      doyunohost_path = sys.argv[key+1]
    if arg == '--ssh-key':
      ssh_key = sys.argv[key+1]

  test_prop = load_test_prop( test_file )
  domain = make_test_domain()

  with deploy( DigitalOceanServer(domain, ssh_key, doyunohost_path, 'yomec') ) as test_server:
    test_server.setup()
    test_server.install_app(test_prop)

