from ppo import plugins

from collections import defaultdict
from functools import wraps
import re


class enum4LinuxParser(object):

    state = 'init'
    substate = None

    sections = {
        'Target Information': 'target_information',
        'Getting domain SID': 'domain',
        'Nbtstat': 'nbtstat',
        'OS information': 'osinfo',
        'Groups on': 'groups',
        'Password Policy': 'password',
        'Users on': 'users',
        'Getting printer info': 'printers',
        'via RID cycling': 'rid_users',
        'Share Enumeration': 'shares',
    }

    def __init__(self):
        self.result = {}
        self.scratch = {}
        self.sections = self.sections.copy()


    _inside_section = False
    _line_number = 0
    def section(f):
        """
        Make the given state handler only receive the lines
        in between the leading and trailing bar:

            =======================
        """
        @wraps(f)
        def deco(self, line):
            if line.count('======'):
                if self._inside_section:
                    self._inside_section = False
                    self._line_number = -1
                    return 'init'
                else:
                    self._inside_section = True
                    self._line_number = -1
                    return
            self._line_number += 1
            return f(self, line)
        return deco

    def dataReceived(self, data):
        handler = getattr(self, 'state_' + self.state)
        new_state = handler(data) or self.state
        if new_state != self.state:
            self.substate = None
        self.state = new_state

    def state_init(self, line):
        if line.startswith('|'):
            title = line.split('|')[1].strip()
            for key, state in self.sections.items():
                if title.count(key):
                    self.sections.pop(key)
                    return state
            return 'init'

    @section
    def state_target_information(self, line):
        if line.startswith('Target'):
            self.result['ipv4'] = line.split(' ')[-1]
        elif line.startswith('Username'):
            self.result['username'] = line.split(' ')[-1].strip("'")
        elif line.startswith('Password'):
            self.result['password'] = line.split(' ')[-1].strip("'")
        elif line.startswith('Known Usernames'):
            m = re.match(r'Known\sUsernames[\s\.]+(.*)', line)
            self.result['known_usernames'] = m.groups()[0].split(', ')

    @section
    def state_domain(self, line):
        if line.count(': '):
            key, value = line.split(': ')
            if value.startswith('(NULL'):
                value = None
            self.result.setdefault(key.lower(), value)

    r_nbstat = re.compile(r'''
        \s*(?P<name>.*?)
        \s*<(?P<suffix>.*?)>
        \s-\s*
        (?P<group><.*?>)?\s*
        (?P<node_type>.)\s*
        <(?P<status>.*?)>\s*
        (?P<description>.*)
        ''', re.M | re.X | re.S)

    @section
    def state_nbtstat(self, line):
        results = self.result.setdefault('nbtstat', [])
        m = self.r_nbstat.search(line)
        if m:
            d = m.groupdict()
            results.append({
                'name': d['name'],
                'suffix': d['suffix'],
                'group': d['group'] == '<GROUP>',
                'node_type': d['node_type'],
                'description': d['description'],
                'status': d['status'],
            })
        elif line.count('MAC Address'):
            m = re.search(r'MAC Address\s*=\s*(.*)', line.strip())
            self.result['mac_address'] = m.groups()[0]

    @section
    def state_osinfo(self, line):
        result = self.result.setdefault('os', {})
        if line.count('smbclient'):
            m = re.search(r'OS=\[(.*?)\] Server=\[(.*?)\]', line)
            result['name'] = m.groups()[0]
            result['server'] = m.groups()[1]
        elif line.strip().startswith(self.result['ipv4']):
            result['srvinfo'] = line.strip().split(' ', 1)[1]
        elif line.count(':') and not line.startswith('[+]'):
            k,v = re.search(r'(.*?)\s*:\s*(.*)', line).groups()
            result[k] = v

    r_group = re.compile(
        r'group:\[(.*?)\]\srid:\[(.*?)\]')
    r_membership = re.compile(r'''
        Group\s'(?P<group>.*?)'
        \s*\(RID:.*?\)
        \s*has\s*member:\s*(?P<member>.*)
    ''', re.X | re.S)

    @section
    def state_groups(self, line):
        groups = self.result.setdefault('groups', [])
        groups_by_name = self.scratch.setdefault('groups', {})
        if '[+] Getting' in line:
            what = line.split(' ')
            self.group_type = what[2]
            if what[-1] == 'memberships:':
                self.substate = 'memberships'
            else:
                self.substate = 'groups'
        elif not line.strip():
            pass
        elif self.substate == 'groups':
            m = self.r_group.match(line)
            d = m.groups()
            group = {
                'name': d[0],
                'rid': d[1],
                'type': self.group_type,
            }
            groups_by_name[d[0]] = group
            groups.append(group)
        elif self.substate == 'memberships':
            m = self.r_membership.match(line)
            d = m.groupdict()
            group = groups_by_name[d['group']]
            members = group.setdefault('members', [])
            members.append(d['member'])


    password_mapping = {
        'Minimum password length': 'min_length',
        'Password history length': 'history_length',
        'Maximum password age': 'max_age',
        'Password Complexity Flags': 'complexity_flags',
        'Domain Refuse Password Change': 'refuse_change',
        'Domain Password Store Cleartext': 'store_cleartext',
        'Domain Password Lockout Admins': 'lockout_admins',
        'Domain Password No Clear Change': 'no_clear_change',
        'Domain Password No Anon Change': 'no_anon_change',
        'Domain Password Complex': 'complex',
        'Minimum password age': 'min_age',
        'Reset Account Lockout Counter': 'reset_lockout_counter',
        'Locked Account Duration: 30 minutes': 'locked_account_duration',
        'Account Lockout Threshold': 'lockout_threshold',
        'Forced Log off Time': 'forced_log_off_time',
    }

    @section
    def state_password(self, line):
        pwpol = self.result.setdefault('password_policy', [])
        if line.count('Password Info for Domain:'):
            domain = line.split(':')[-1].strip()
            self.tofind = self.password_mapping.copy()
            self.current = {'name': domain}
            pwpol.append(self.current)
        elif getattr(self, 'current', None):
            for srckey,dstkey in self.tofind.items():
                if line.count(srckey):
                    value = line.split(':')[-1].strip()
                    if value.lower() in ('none', 'not set'):
                        value = None
                    try:
                        intval = int(value)
                        assert str(intval) == value
                        value = intval
                    except: pass
                    self.tofind.pop(srckey)
                    self.current[dstkey] = value
                    break



    r_user = re.compile(r'''
        index:\s*(?P<index>.*?)\s*
        RID:\s*(?P<rid>.*?)\s*
        acb:\s*(?P<acb>.*?)\s*
        Account:\s*(?P<account>.*?)\s*
        Name:\s*(?P<name>.*?)\s*
        Desc:\s*(?P<desc>.*)
    ''', re.X)

    @section
    def state_users(self, line):
        users = self.result.setdefault('users', [])
        m = self.r_user.match(line)
        if m:
            d = m.groupdict()
            for k,v in d.items():
                if v == '(null)':
                    d[k] = None
            users.append(d)

    @section
    def state_printers(self, line):
        self.result.setdefault('printers', [])

    r_rid_sid_header = re.compile(r'''
        .*?using\sSID\s*(?P<sid>[^\s]+).*?
        username\s*(?P<username>.*?),\s*
        password\s*(?P<password>.*)
    ''', re.X | re.S)

    r_rid_user = re.compile(r'''
        (?P<sid>.*?)\s+
        (?P<name>.*?)\s*
        \((?P<description>.*?)\)
    ''', re.X)

    @section
    def state_rid_users(self, line):
        rid_users = self.result.setdefault('rid_users', [])
        if 'using SID' in line:
            m = self.r_rid_sid_header.search(line)
            d = m.groupdict()
            d['username'] = d['username'].strip("'")
            d['password'] = d['password'].strip("'")
            d['users'] = []
            rid_users.append(d)
        elif '*unknown*\\*unknown*' not in line:
            m = self.r_rid_user.match(line)
            if m:
                current = rid_users[-1]
                d = m.groupdict()
                current['users'].append(d)

    r_share_mapping = re.compile(r'''
        (?P<server>.*?)\s*?
        Mapping:\s*(?P<mapping>.*?),?\s*
        Listing:\s*(?P<listing>.*)
    ''', re.X)
    
    @section
    def state_shares(self, line):
        if self.substate is None:
            if 'Sharename' in line:
                self.substate = 'shares'
            elif 'Server   ' in line:
                self.substate = 'servers'
                self.result.setdefault('servers', [])
            elif 'Workgroup' in line:
                self.substate = 'workgroups'
                self.result.setdefault('workgroups', [])
            elif 'Attempting to map' in line:
                self.substate = 'mapping'
        elif not line.strip():
            # end of subsection
            self.substate = None
        elif line.count('---'):
            # dividing line
            parts = re.split(r'(-+)', line)[1:]
            self._fields = defaultdict(lambda:0)
            for i,part in enumerate(parts):
                self._fields[i/2] += len(part)
        elif self.substate == 'shares':
            shares = self.result.setdefault('shares', [])
            share = {
                'name': line.strip()[:self._fields[0]].strip(),
                'type': line.strip()[self._fields[0]:self._fields[1]+self._fields[0]].strip(),
                'comment': line.strip()[self._fields[1]+self._fields[0]:].strip(),
            }
            shares.append(share)
        elif self.substate == 'servers':
            self.result.setdefault('servers', []).append({
                'name': line.strip()[:self._fields[0]].strip(),
                'comment': line.strip()[self._fields[0]:].strip(),
            })
        elif self.substate == 'workgroups':
            self.result.setdefault('workgroups', []).append({
                'name': line.strip()[:self._fields[0]].strip(),
                'master': line.strip()[self._fields[0]:].strip(),
            })
        elif self.substate == 'mapping':
            m = self.r_share_mapping.search(line)
            if m:
                g = m.groupdict()
                g['server'] = g['server'].split('/')[-1]
                for share in self.result['shares']:
                    if share['name'] == g['server']:
                        share['mapping'] = g['mapping']
                        share['listing'] = g['listing']

            





class enum4linuxPlugin(plugins.ParserPlugin):
    """
    I parse enum4linux output
    """

    state = 'init'

    def readProbability(self, instream):
        first_part = instream.read(200)
        if 'Starting enum4linux' in first_part:
            return 50

    def parse(self, instream):
        parser = enum4LinuxParser()
        for line in instream:
            parser.dataReceived(line.strip())
        return parser.result
