# -*- coding: utf-8 -*-

import json
import os

configlist = {}

def init():
  thisdir = os.path.dirname(__file__)
  for json_filename in os.listdir(thisdir):
    (app, ext) = os.path.splitext(json_filename)
    if ext == ".json":
      test_prop = {}
      with open(os.path.join(thisdir, json_filename)) as json_file:
        configlist[app] = json.loads(str(json_file.read()))
  
  # temporary test
  configlist = { "baikal" : configlist["baikal"] }

init()
