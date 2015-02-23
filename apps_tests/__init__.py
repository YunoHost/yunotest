# -*- coding: utf-8 -*-
import unittest
import sys
import pkgutil
import os
import re
import requests
import json
import jsonschema
import pexpect
import base64

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
    except e:
      self.teardown_server()
      raise e

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
        
      def get_tmp_dir(self):
        # a dir in the jenkins workspace, so it get cleaned up automatically at each build
        path = os.path.join(os.path.dirname(__file__), "..", "tmp")
        try:
          os.makedirs( path )
        except os.error:
          pass
        return path
        
      def get_attachments_dir(self):
        # https://wiki.jenkins-ci.org/display/JENKINS/JUnit+Attachments+Plugin
        # Jenkins attachment plugin looks for files in a directory named after module.class
        # I did not manage to make it work with logging [ATTACHMENT] snippet
        path = os.path.join(os.path.dirname(__file__), "..", "%s.%s" % (__name__,self.__class__.__name__))
        try:
          os.makedirs( path )
        except os.error:
          pass
        return path
      
      def attach_file(self, relative_path):
        command = 'cp %s %s' % ( os.path.join(os.getcwd(), relative_path), self.get_attachments_dir())
        os.system( command )
        
      def attach_data(self, data, filename):
        with open(os.path.join(self.get_attachments_dir(), filename), "w") as f:
          f.write(data)

      def test_install(self):
        global context
        if 'install_depends' in config:
          for depends in config["install_depends"]:
            (command_output_dep, exitstatus_dep) = context.server.install_app(configs.configlist[depends])
            assert exitstatus_dep == 0
        (install_logs, exitstatus) = context.server.install_app(config)
        self.attach_data(install_logs, "install.txt")
        #self.attach_data(installed_files, "installed_files.txt")
        context.server.get_remote_file("/tmp/%s.installed_files.txt" % config["id"], self.get_attachments_dir())
        assert exitstatus == 0, "install exited with non-zero code"

        screenshot = True
        if "screenshot" in config and config["screenshot"] == "no":
          screenshot = False
        
        if screenshot:
          with open( os.path.join(os.path.dirname(__file__), "screenshot.js.tpl") ) as tplf:
            tpl = str(tplf.read())
            script = tpl \
              .replace("YNH_BASIC_AUTH", base64.b64encode('%s:%s' % (context.server.user,context.server.user_password))) \
              .replace("YNH_APP_URL", "https://%s%s" % (context.server.domain, config["install"]["path"])) \
              .replace("YNH_SCREENSHOT_DIR", self.get_attachments_dir()) \
              .replace("YNH_SCREENSHOT_FILENAME", "%s.png" % (config["id"]) )
          script_location = "%s/%s.js" % (self.get_tmp_dir(), config["id"])
          with open( script_location , "w" ) as scriptf:
            scriptf.write(script)
          (output, exitstatus) = pexpect.run("casperjs --ignore-ssl-errors=true %s" % (script_location), withexitstatus=True, timeout= 60)
          print output
          assert exitstatus == 0, "test_screenshot exited with non-zero code"
          
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
