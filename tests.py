# -*- coding: utf-8 -*-

import os

class YunoTest

  def attach_file( relative_path ):
    output_path = os.path.join(os.path.dirname(__file__), 'YunoTest')
    try:
      os.makedirs( output_path )
    except os.error:
      pass

    os.system('cp %s %s' % ( os.path.join(os.getcwd(), relative_path), output_path)

  def test1(self):
    print 'inside test1'
    self.attach_file('LICENSE')
#    print '[[ATTACHMENT|%s]]' % (os.path.join( os.path.dirname(__file__), ))
    assert( 1 == 1 )

  def test2(self):
    print 'inside test2'
    self.attach_file('single_app_test.py')
#    print '[[ATTACHMENT|%s]]' % (os.path.join( os.path.dirname(__file__), 'single_app_test.py'))
    assert( 1 == 2 )

  def test3(self):
    print 'inside test3'
    assert( 1 == 3 )
