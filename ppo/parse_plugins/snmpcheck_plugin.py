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
        self.result['target'] = \
            re.search(r'Connected to (.*)', line.strip()).groups()[0]

    @sections.route('Starting enumeration at')
    @ignoreEmpty
    def SEC_start_enum(self, line):
        self.result.setdefault('meta', {})['starttime'] = \
            re.search(r'Starting enumeration at (.*)', line.strip()).groups()[0]

    @sections.route('Enumerated')
    @ignoreEmpty
    def SEC_end_enum(self, line):
        self.result.setdefault('meta', {})['runtime'] = \
            re.search(r'Enumerated .*? in (.*)', line.strip()).groups()[0]

    @sections.route('System information')
    @ignoreHeader
    @ignoreEmpty
    def SEC_system_info(self, line):
        k,v = self.r_kv.search(line.strip()).groups()
        actual_key = {
            'domain (nt)': 'domain',
            'uptime snmp daemon': 'uptime_snmp',
            'uptime system': 'uptime_system',
        }.get(k.lower(), k.lower())
        sys_info = self.result.setdefault('system', {})
        sys_info[actual_key] = v

    @sections.route('Web server information')
    @ignoreHeader
    @ignoreEmpty
    def webserver_info(self, line):
        k,v = self.r_kv.search(line.strip()).groups()
        actual_key = {

        }.get(k.lower(), k.lower())
        try:
            v = int(v)
        except: pass
        info = self.result.setdefault('webserver_info', {})
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
        addr, port = re.search(r'^\s*(.+?)\s+(\d+)\s*$', line.strip()).groups()
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
            r'^\s*([\.\d]+?)\s+([\d\-]+?)\s+([\.\d]+?)\s+([\d\-]+?)\s+(.*?)\s*$',
            line.strip()).groups()
        d = self.result.setdefault('tcp_ports', [])
        d.append({
            'local_address': local,
            'local_port': self.maybeInt(lport),
            'remote_address': remote,
            'remote_port': self.maybeInt(rport),
            'state': state,
        })

    @sections.route('Storage information')
    @ignoreHeader
    def storage_info(self, line):
        stripped = line.strip()
        current_state = self.state.get('parse_state', 'init')
        if current_state == 'init':
            if line.strip():
                # we have found a piece of storage
                parts = re.match(r'''
                    ^(?P<name>.+?)
                    (?:
                        \s+Label:\s*(?P<label>.*)
                    )?$
                    ''', stripped, re.X).groupdict()
                self.state['current_item'] = {
                    'name': parts['name'],
                }
                if parts['label']:
                    self.state['current_item']['label'] = parts['label']
                self.state['parse_state'] = 'attrs'
        elif current_state == 'attrs':
            # looking for attributes
            if not stripped:
                # end of this item
                self.result.setdefault('storage', []).append(self.state['current_item'])
                self.state['parse_state'] = 'init'
            else:
                k,v = self.r_kv.search(line.strip()).groups()
                actual_key = {
                }.get(k.lower(), k.lower().replace(' ', '_'))
                try:
                    v = int(v)
                except:
                    pass
                self.state['current_item'][actual_key] = v

    @sections.route('Software components')
    @ignoreHeader
    @ignoreEmpty
    def software_components(self, line):
        if line.strip():
            self.result.setdefault('software_components', []).append(line.strip())


    @sections.route('Routing information')
    @ignoreHeader
    @ignore(AttributeError)
    def routing_info(self, line):
        line = line.strip()
        data = re.match(r'''
            ^(?P<destination>.+?)\s+
            (?P<next_hop>.+?)\s+
            (?P<mask>.+?)\s+
            (?P<metric>.+?)$
            ''', line, re.X).groupdict()
        if data['destination'] == 'Destination':
            # it's the header
            return
        self.result.setdefault('routing', []).append(data)

    @sections.route('Processes')
    @ignore(AttributeError)
    def processes(self, line):
        line = line.strip()
        parse_state = self.state.get('parse_state', 'init')
        if parse_state == 'init':
            # looking for header stuff
            def parseMapping(line):
                ret = {}
                parts = line.split(':')[1].strip().split(', ')
                for item in parts:
                    k,v = item.split(' ', 1)
                    ret[k] = v
                return ret

            if line.startswith('Process type'):
                self.state['type_map'] = parseMapping(line)
            elif line.startswith('Process status'):
                self.state['status_map'] = parseMapping(line)
            elif line.startswith('Process id'):
                self.state['parse_state'] = 'rows'
        elif parse_state == 'rows':
            # looking for rows
            data = re.search(r'''
                ^
                (?P<pid>\d+?)\s+
                (?P<name>.+?)\s+
                (?P<type>\d*?)\s+
                (?P<status>\d*?)\s*
                $
            ''', line, re.X).groupdict()
            data['pid'] = int(data['pid'])
            data['type'] = self.state['type_map'][data['type']]
            data['status'] = self.state['status_map'][data['status']]
            self.result.setdefault('processes', []).append(data)

    @sections.route('Network services')
    @ignoreHeader
    @ignoreEmpty
    def net_services(self, line):
        self.result.setdefault('network_services', []).append(line.strip())

    @sections.route('Network interfaces')
    @ignoreHeader
    @ignore(AttributeError)
    def net_interfaces(self, line):
        parse_state = self.state.get('parse_state', 'init')
        line = line.strip()
        if parse_state == 'init':
            if line.startswith('Interface'):
                data = re.search(r'''
                    :\s*
                    \[\s*(.*?)\s*\]
                    \s*
                    (.*)
                ''', line, re.X).groups()
                self.state['current_item'] = item = {
                    'status': data[0],
                    'name': data[1],
                }
                self.result.setdefault('network_interfaces', []).append(item)
                self.state['parse_state'] = 'skip_attrs'
        elif parse_state == 'skip_attrs':
            self.state['parse_state'] = 'attrs'
        elif parse_state == 'attrs':
            if not line:
                self.state['parse_state'] = 'init'
                return
            k,v = self.r_kv.search(line.strip()).groups()
            actual_key = {

            }.get(k.lower(), k.lower().replace(' ','_'))
            if actual_key in ('bytes_in', 'bytes_out'):
                v = v.split()[0]
            try:
                v = int(v)
            except: pass
            self.state['current_item'][actual_key] = v

    @sections.route('Network information')
    @ignoreHeader
    @ignoreEmpty
    def net_info(self, line):
        k,v = self.r_kv.search(line.strip()).groups()
        actual_key = {
        }.get(k.lower(), k.lower().replace(' ','_'))
        try:
            v = int(v)
        except: pass
        self.result.setdefault('network_info', {})[actual_key] = v

    @sections.route('Devices information')
    @ignoreHeader
    @ignoreEmpty
    def devices(self, line):
        line = line.strip()
        reg = re.sub(r'\s\s+', '  ', line)
        parts = reg.split('  ', 3)
        if parts[0] == 'Id':
            # ignore header
            return
        self.result.setdefault('devices', []).append({
            'id': int(parts[0]),
            'type': parts[1],
            'status': parts[2],
            'description': parts[3],
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
            parser.dataReceived(line)
        return parser.result
