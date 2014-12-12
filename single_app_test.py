#!/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import random
import json

import do

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

  with do.deploy( do.DigitalOceanServer(domain, ssh_key, doyunohost_path, 'yomec') ) as test_server:
    test_server.setup()
    test_server.install_app(test_prop)

