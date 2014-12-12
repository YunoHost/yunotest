# -*- coding: utf-8 -*-

import os

class TestYunoapps:
  def attach_file(self, relative_path):
    #output_path = os.path.join(os.path.dirname(__file__), self.__class__.__name__)
    output_path = os.path.join(os.path.dirname(__file__), "tests.TestYunoapps")
    try:
      os.makedirs( output_path )
    except os.error:
      pass

    command = 'cp %s %s' % ( os.path.join(os.getcwd(), relative_path), output_path)
    print command
    os.system( command )

  def test_1(self):
    print 'inside test1'
    self.attach_file('LICENSE')
    assert( 1 == 1 )

  def test_2(self):
    print 'inside test2'
    self.attach_file('single_app_test.py')
    assert( 1 == 2 )

  def test_3(self):
    print 'inside test3'
    assert( 1 == 3 )
