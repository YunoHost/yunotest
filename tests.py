# -*- coding: utf-8 -*-

import os

def test1():
  print 'inside test1'
  print '[[ATTACHMENT|%s]]' % (os.path.join( os.path.basename(__file__), 'LICENSE'))
  assert( 1 == 1 )

def test2():
  print 'inside test2'
  print '[[ATTACHMENT|%s]]' % (os.path.join( os.path.basename(__file__), 'single_app_test.py'))
  assert( 1 == 2 )

def test3():
  print 'inside test3'
  assert( 1 == 3 )

