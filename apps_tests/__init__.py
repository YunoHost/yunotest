# -*- coding: utf-8 -*-
import unittest
import sys
import pkgutil
import os

import do
import configs

# http://nose.readthedocs.org/en/latest/writing_tests.html#test-packages
def setup_package():
  print 'Setup package %s' % (__name__)

def teardown_package():
  print 'Teardown package %s' % (__name__)

def _make_AppTest(appid):
  class AppTest(unittest.TestCase):
      """ Classe de base, elle peut faire un setUp, un tearDown
          et avoir des méthodes spécifique, comme "parse" dans notre
          cas...
      """
      @classmethod
      def setUpClass(cls):
        # called once for the class, before all tests
        print 'setUpClass %s' % (cls.__name__)
        
      @classmethod
      def tearDownClass(cls):
        # called once for the class, after all tests
        print 'tearDownClass %s' % (cls.__name__)

      def setUp(self):
        # called before each test of this class
        print 'setUp class %s' % (self.__class__.__name__)
      
      def tearDown(self):
        # called after each test of this class
        print 'tearDown class %s' % (self.__class__.__name__)
      
      def attach_file(self, relative_path):
        # jenkins attachment plugin looks for files in a directory named after module.class
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

def init():
    """ Initialise les classes de test """
    
    for key, config in configs.configlist.items():
      cl = _make_AppTest( str(config["id"]) )
      setattr(sys.modules[__name__], cl.__name__, cl)

# initialisation
init()
