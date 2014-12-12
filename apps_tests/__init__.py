# -*- coding: utf-8 -*-
import unittest
import sys
import pkgutil
import os

def _make_AppTest(appid):
  class AppTest(unittest.TestCase):
      """ Classe de base, elle peut faire un setUp, un tearDown
          et avoir des méthodes spécifique, comme "parse" dans notre
          cas...
      """
      def attach_file(self, relative_path):
        output_path = os.path.join(os.path.dirname(__file__), "..", "%s.%s" % (__name__,self.__class__.__name__))
        try:
          os.makedirs( output_path )
        except os.error:
          pass
        command = 'cp %s %s' % ( os.path.join(os.getcwd(), relative_path), output_path)
        print command
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
    
    for appid in ["roundcube", "jirafeau"]:
      cl = _make_AppTest(appid)
      setattr(sys.modules[__name__], cl.__name__, cl)

# initialisation
init()
