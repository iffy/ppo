# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins

from functools import wraps
import re


def ignore(error_types):
    def deco(f):
        @wraps(f)
        def inner(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except error_types:
                pass
        return inner
    return deco


class Registry(object):

    def __init__(self, instance=None, data=None):
        self.data = data or {}
        self._instance = instance

    def __get__(self, obj, cls):
        return Registry(obj, self.data)

    def route(self, name):
        def deco(f):
            self.data[name] = f
            return f
        return deco

    def find(self, name):
        for pattern, func in self.data.items():
            if pattern in name:
                return func.__get__(self._instance, self._instance.__class__)


class snmpcheckParser(object):

    section = None

    sections = Registry()
    # sections = {
    #     'Connected to': 'connected_to',
    #     'Starting enumeration at': 'start_enum',
    #     'Enumerated': 'end_enum',
    # }

    r_kv = re.compile(r'(.*?)\s*:\s*(.*)')

    def __init__(self):
        self.result = {}
        self.state = {}


    def ignoreHeader(f):
        @wraps(f)
        def deco(instance, line):
            stripped = line.strip()
            if stripped.startswith('[*]') or stripped.startswith('-------------'):
                return
            return f(instance, line)
        return deco

    def ignoreEmpty(f):
        @wraps(f)
        def deco(instance, line):
            if not line.strip():
                return
            return f(instance, line)
        return deco        

    def dataReceived(self, data):
        if data.strip().startswith('[*] '):
            # new section
            self.section = self.sections.find(data)
            self.state = {}

        if self.section:
            self.section(data)

    @sections.route('Connected to')
    @ignore(AttributeError)
    def SEC_connected_to(self, line):
        self.result['target'] = re.search(r'Connected to (.*)', line).groups()[0]

    @sections.route('Starting enumeration at')
    @ignoreEmpty
    def SEC_start_enum(self, line):
        self.result.setdefault('meta', {})['starttime'] = \
            re.search(r'Starting enumeration at (.*)', line).groups()[0]

    @sections.route('Enumerated')
    @ignoreEmpty
    def SEC_end_enum(self, line):
        self.result.setdefault('meta', {})['runtime'] = \
            re.search(r'Enumerated .*? in (.*)', line).groups()[0]

    @sections.route('System information')
    @ignoreHeader
    @ignoreEmpty
    def SEC_system_info(self, line):
        k,v = self.r_kv.search(line).groups()
        sys_info = self.result.setdefault('system', {})
        actual_key = {
            'domain (nt)': 'domain',
            'uptime snmp daemon': 'uptime_snmp',
            'uptime system': 'uptime_system',
        }.get(k.lower(), k.lower())
        sys_info[actual_key] = v

    @sections.route('Web server information')
    @ignoreHeader
    @ignoreEmpty
    def webserver_info(self, line):
        k,v = self.r_kv.search(line).groups()
        info = self.result.setdefault('webserver_info', {})
        actual_key = {

        }.get(k.lower(), k.lower())
        try:
            v = int(v)
        except: pass
        info[actual_key] = v

    @sections.route('User accounts')
    @ignoreHeader
    @ignoreEmpty
    def user_accounts(self, line):
        stripped = line.strip()
        if stripped:
            self.result.setdefault('user_accounts', []).append(stripped)

    def maybeInt(self, x):
        try:
            return int(x)
        except:
            return x

    @sections.route('Listening UDP ports')
    @ignoreHeader
    @ignoreEmpty
    @ignore(AttributeError)
    def udp_ports(self, line):
        addr, port = re.search(r'^\s*(.+?)\s+(\d+)\s*$', line).groups()
        d = self.result.setdefault('udp_ports', [])
        d.append({
            'local_port': self.maybeInt(port),
            'local_address': addr,
        })

    @sections.route('Listening TCP ports')
    @ignoreHeader
    @ignoreEmpty
    @ignore(AttributeError)
    def tcp_ports(self, line):
        local, lport, remote, rport, state = re.search(
            r'^\s*([\.\d]+?)\s+([\d\-]+?)\s+([\.\d]+?)\s+([\d\-]+?)\s+(.*?)\s*$', line).groups()
        d = self.result.setdefault('tcp_ports', [])
        d.append({
            'local_address': local,
            'local_port': self.maybeInt(lport),
            'remote_address': remote,
            'remote_port': self.maybeInt(rport),
            'state': state,
        })


class snmpcheckPlugin(plugins.ParserPlugin):
    """
    I parse snmpcheck output
    """

    name = 'snmpcheck'

    def readProbability(self, instream):
        first_part = instream.read(200)
        if first_part.startswith('snmpcheck'):
            return 50

    def parse(self, instream):
        parser = snmpcheckParser()
        for line in instream:
            parser.dataReceived(line.strip())
        return parser.result
