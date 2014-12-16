# -*- coding: utf-8 -*-
import unittest
import sys
import pkgutil
import os

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
            (command_output, exitstatus) = context.server.install_app(configs.configlist[depends])
            assert exitstatus == 0
        (command_output, exitstatus) = context.server.install_app(config)
        self.attach_data(command_output, "install.txt")
        assert exitstatus == 0

      def test_remove(self):
        global context
        (command_output, exitstatus) = context.server.remove_app(config)
        self.attach_data(command_output, "remove.txt")
        assert exitstatus == 0

      def test_manifest(self):
        pass

  cl = type("%s" % str(config["id"]), (AppTest,), {})
  return cl

def init():
    for key, config in configs.configlist.items():
      cl = _make_AppTest( config )
      setattr(sys.modules[__name__], cl.__name__, cl)

init()
