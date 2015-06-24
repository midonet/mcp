# Copyright 2015 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import subprocess
import sys
import webob

import midonetclient
from midonetclient.api import MidonetApi

class Session(object):
    def __init__(self):
        self.api_url = None
        self.username = None
        self.password = None
        self.project_id = None
        self.tenant_id = None
        self.tenant_stack = []
        self.enable_alias_manager = True
        self.do_auth = False
        self.do_eval = False
        self.debug = False

    def print_current_tenant(self):
        print "tenant_id: %s" % (self.current_tenant())

    def push_tenant(self, tenant_id):
        if not self.do_eval:
            if (tenant_id is not None) and not is_valid_hex_uuid(tenant_id):
                print ("WARNING!: tenant_id=%s is not a 32-char hex string, "
                       "which is used in Keystone for project id format"
                       % tenant_id)

        self.tenant_stack.append(tenant_id)

    def pop_tenant(self):
        if self.tenant_stack:
            self.tenant_stack.pop()

    def current_tenant(self):
        if not self.tenant_stack:
            return self.tenant_id
        else:
            return self.tenant_stack[-1]

    def _load_from_config_file(self):
        import ConfigParser
        import os
        home = os.path.expanduser("~")
        try:
            cfg = ConfigParser.ConfigParser()
            cfgfile = "%s%s%s" % (home, os.path.sep, '.midonetrc')
            cfg.read(cfgfile)
        except:
            return
        if cfg.has_option('cli', 'api_url'):
            self.api_url = cfg.get('cli', 'api_url')
        if cfg.has_option('cli', 'username'):
            self.username = cfg.get('cli', 'username')
        if cfg.has_option('cli', 'password'):
            self.password = cfg.get('cli', 'password')
        if cfg.has_option('cli', 'project_id'):
            self.project_id = cfg.get('cli', 'project_id');
        if cfg.has_option('cli', 'tenant'):
            self.tenant_id = cfg.get('cli', 'tenant')
        else:
            self.tenant_id = ''

    def _load_from_env(self):
        import os
        if os.environ.has_key('MIDO_API_URL'):
            self.api_url = os.environ['MIDO_API_URL']
        if os.environ.has_key('MIDO_USER'):
            self.username = os.environ['MIDO_USER']
        if os.environ.has_key('MIDO_PASSWORD'):
            self.password = os.environ['MIDO_PASSWORD']
        if os.environ.has_key('MIDO_PROJECT_ID'):
            self.project_id = os.environ['MIDO_PROJECT_ID']
        if os.environ.has_key('MIDO_TENANT'):
            self.tenant_id = os.environ['MIDO_TENANT']

    def load(self):
        logging.basicConfig()
        logging.getLogger().setLevel(logging.CRITICAL)

        self._load_from_config_file()
        self._load_from_env()

        if self.api_url is None:
            raise Exception("Missing: Midonet API URL")
        if self.do_auth and self.username is None:
            raise Exception("Missing: username")
        if self.do_auth and self.project_id is None:
            raise Exception("Missing: Midonet Project ID")
        if self.do_auth and self.password is None:
            raise Exception("No password given (add it to ~/.midonetrc or "+
                            "get a prompt using the -p option)")

    def connect(self):
        auth = None
        return MidonetApi(self.api_url, self.username, self.password, self.project_id)

MM_DOCKER = "/usr/local/bin/mcp/mm-docker.sh"
MM_CTL="mm-ctl"

session = Session()
session.load()
client = session.connect()

def wire_container_to_midonet(container_id, bridge_id="78488c47-d1de-4d16-a27a-4e6419dc4f88"):
    try:
        bridge = client.get_bridge(bridge_id)
        vport = client.add_bridge_port(bridge)
        vport = vport.create()
        
        interface_name = "-veth"
        _add_if_to_dp(interface_name, container_id)
        
        generated_interface = container_id[0:8] + interface_name[0:5]
        _bind_if_to_vport(generated_interface, vport.get_id())
    except webob.exc.HTTPNotFound as err:
        sys.stderr.write(str(err) + "\n")
        raise
    except Exception as ex:
        sys.stderr.write(str(ex) + "\n")
        raise

def _add_if_to_dp(interface, container_id):
    cmd = ["sudo", "bash", MM_DOCKER, "add-if", interface, container_id]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = p.communicate()
    sys.stderr.write(stdout_data + "\n")
    if p.returncode != 0:
        sys.stderr.write(stderr_data + "\n")
        raise Exception(stderr_data)

def _bind_if_to_vport(interface, vport_id):
    with open("/etc/midonet_host_id.properties") as f:
        lines = f.readlines()
        host_id = lines[-1].split("=")[1].strip()
        try:
            host = client.get_host(host_id)
            host_interface_port = client.add_host_interface_port(
                host, vport_id, interface)
            host_interface_port.create()
        except Exception as e:
            sys.stderr.write(str(e) + "\n")
            raise
        
