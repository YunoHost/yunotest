# -*- coding: utf-8 -*-
import unittest
import sys
import pkgutil
import os

import do
import configs

doyunohost = ''

# http://nose.readthedocs.org/en/latest/writing_tests.html#test-packages
def setup_package():
  pass

def teardown_package():
  pass

def _make_AppTest(appid):
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

      def test_install(self):
        self.attach_file('LICENSE.txt')
        print('Testing %s' % (appid))
        assert(False)

      def test_remove(self):
        pass

  cl = type("%s" % appid, (AppTest,), {})
  return cl

def load_doyunohost():
    global doyunohost
    doyunohost = os.getenv('DOYUNOHOST')
    if not doyunohost:
      raise RuntimeError('You need to set DOYUNOHOST env. var')
      
    if not os.path.exists( os.path.join(doyunohost, 'deploy.py') ) \
       or not os.path.exists( os.path.join(doyunohost, 'remove.py') ):
         raise ValueError('You need to set DOYUNOHOST env. var to a clone of https://github.com/YunoHost/doyunohost')
         
    if not os.path.exists( os.path.join(doyunohost, 'config.local') ):
      raise RuntimeError('$DOYUNOHOST/config.local is not set up')
      
    print 'Successfully loaded DOYUNOHOST'
    #return doyunohost

def init():
    #doyunohost = load_doyunohost()
    
    load_doyunohost()
    
    for key, config in configs.configlist.items():
      cl = _make_AppTest( str(config["id"]) )
      setattr(sys.modules[__name__], cl.__name__, cl)

init()
