# -*- coding: utf-8 -*-
import unittest
import sys
import pkgutil
import os
import re
import requests
import json
import jsonschema

import do
import configs

class PackageContext:
  def __init__(self):
    self.doyunohost = self.get_doyunohost()
    self.domain = do.make_test_domain()
    self.admin_password = do.make_random_password()
    self.server = None

  def get_doyunohost(self):
      doyunohost = os.getenv('DOYUNOHOST')
      if not doyunohost:
        raise RuntimeError('You need to set DOYUNOHOST env. var')
        
      if not os.path.exists( os.path.join(doyunohost, 'deploy.py') ) \
         or not os.path.exists( os.path.join(doyunohost, 'remove.py') ):
           raise ValueError('You need to set DOYUNOHOST env. var to a clone of https://github.com/YunoHost/doyunohost')
           
      if not os.path.exists( os.path.join(doyunohost, 'config.local') ):
        raise RuntimeError('$DOYUNOHOST/config.local is not set up')
      
      return doyunohost
  
  def setup_server(self):
    self.server = do.DigitalOceanServer(self.domain, self.admin_password, self.doyunohost)
    try:
      self.server.deploy()
      self.server.setup()
    except:
      self.teardown_server()
 
  def teardown_server(self):
    self.server.remove()

context = PackageContext()

# http://nose.readthedocs.org/en/latest/writing_tests.html#test-packages
def setup_package():
  global context
  context.setup_server()

def teardown_package():
  global context
  context.teardown_server()

def _make_AppTest(config):
  class AppTest(unittest.TestCase):
      """ Classe de base, elle peut faire un setUp, un tearDown
          et avoir des méthodes spécifique, comme "parse" dans notre
          cas...
      """
      @classmethod
      def setUpClass(cls):
        # called once for the class, before all tests
        pass
        
      @classmethod
      def tearDownClass(cls):
        # called once for the class, after all tests
        pass

      def setUp(self):
        # called before each test of this class
        pass
      
      def tearDown(self):
        # called after each test of this class
        pass
      
      def attach_file(self, relative_path):
        # https://wiki.jenkins-ci.org/display/JENKINS/JUnit+Attachments+Plugin
        # Jenkins attachment plugin looks for files in a directory named after module.class
        # I did not manage to make it work with logging [ATTACHMENT] snippet
        output_path = os.path.join(os.path.dirname(__file__), "..", "%s.%s" % (__name__,self.__class__.__name__))
        try:
          os.makedirs( output_path )
        except os.error:
          pass
        command = 'cp %s %s' % ( os.path.join(os.getcwd(), relative_path), output_path)
        os.system( command )
        
      def attach_data(self, data, filename):
        output_path = os.path.join(os.path.dirname(__file__), "..", "%s.%s" % (__name__,self.__class__.__name__))
        try:
          os.makedirs( output_path )
        except os.error:
          pass
        with open(os.path.join(output_path, filename), "w") as f:
          f.write(data)

      def test_install(self):
        global context
        if 'install_depends' in config:
          for depends in config["install_depends"]:
            (command_output_dep, exitstatus_dep) = context.server.install_app(configs.configlist[depends])
            assert exitstatus_dep == 0
        (install_logs, exitstatus, installed_files) = context.server.install_app(config)
        self.attach_data(install_logs, "install.txt")
        self.attach_data(installed_files, "installed_files.txt")
        assert exitstatus == 0, "install exited with non-zero code"

      def test_remove(self):
        global context
        (command_output, exitstatus) = context.server.remove_app(config)
        self.attach_data(command_output, "remove.txt")
        if 'install_depends' in config:
          for depends in config["install_depends"]:
            (command_output_dep, exitstatus_dep) = context.server.remove_app(configs.configlist[depends])
        assert exitstatus == 0, "remove exited with non-zero code"

      def test_manifest_schema(self):
        m = re.search('https:\/\/github.com\/(.+)\/(.+)', config["git"])
        assert len(m.groups()) == 2, "unable to parse github url %s" % (config["git"])
        manifest_uri = 'https://raw.githubusercontent.com/{owner}/{repo}/master/manifest.json' \
          .format( owner = m.group(1), repo = m.group(2) )
        r = requests.get(manifest_uri)
        assert r.status_code == 200, "unable to retrieve manifest.json at %s" % (manifest_uri)
        manifest_content = json.loads(r.content)
        with open(os.path.join(os.path.dirname(__file__), "manifest_schema.json")) as schemaf:
          schema = json.loads(str(schemaf.read()))
        jsonschema.validate(manifest_content, schema)

  cl = type("%s" % str(config["id"]), (AppTest,), {})
  return cl

def init():
    for key, config in configs.configlist.items():
      cl = _make_AppTest( config )
      setattr(sys.modules[__name__], cl.__name__, cl)

init()
