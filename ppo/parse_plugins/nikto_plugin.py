# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins
from ppo.state import Registry

import re




class NiktoParser(object):

    sections = Registry()
    state = None

    def __init__(self):
        self.result = {
            'meta': {
                'version': None,
            },
            'targets': [],
        }
        self.targ = None

    def dataReceived(self, data):
        section = self.sections.find(data)
        if section:
            section[0](data)
        else:
            self.dataLine(data)

    @sections.route('- Nikto v')
    def version(self, line):
        self.result['meta']['version'] = line.split('v', 1)[1].strip()

    @sections.route('host(s) tested')
    def hosts_tested(self, line):
        self.result['hosts_tested'] = int(line.split()[1])

    @sections.route('-------------')
    def divider(self, line):
        self.state = {
            None: 'header',
            'header': 'body',
            # body changes state to footer
            'footer': 'header',
        }[self.state]
        if self.state == 'header':
            self.targ = None

    def dataLine(self, line):
        if not self.state:
            return
        getattr(self, 'state_' + self.state)(line)

    r_starttime = re.compile(r'^(.*?)\s\((.*?)\)$')

    def state_header(self, line):
        if not line.strip():
            return
        if not self.targ:
            self.targ = {
                'findings': [],
            }
            self.result['targets'].append(self.targ)
        k, v = line[2:].split(':', 1)
        v = v.strip()
        if k == 'Target IP':
            self.targ['ip'] = v
        elif k == 'Target Hostname':
            self.targ['hostname'] = v
        elif k == 'Target Port':
            self.targ['port'] = int(v)
        elif k == 'Start Time':
            m = self.r_starttime.match(v)
            ts, tz = m.groups()
            self.targ['start'] = ts
            self.targ['timezone'] = tz


    r_summary = re.compile(r'''
        ([0-9]+)\srequests:
        \s([0-9]+)\serror\(s\)
        .*?
        ([0-9]+)\sitem\(s\)
    ''', re.X)

    r_error_summary = re.compile(r'''
        Scan\sterminated:
        \s+([0-9]+)\serror\(s\)
        .*?
        ([0-9]+)\sitem\(s\)
    ''', re.X)

    r_endtime = re.compile(r'''
        ^(.*?)\s\((.*?)\)\s\(([0-9]+)\sseconds\)$
        ''', re.X)

    def state_footer(self, line):
        line = line.lstrip('+ ')
        meta = self.targ.setdefault('meta', {})
        if line.startswith('ERROR:'):
            meta.update({
                'error_message': line,
            })
            return

        errm = self.r_error_summary.match(line)
        if errm:
            errors, items = map(int, errm.groups())
            meta.update({
                'errors': errors,
                'terminated': True,
                'items_reported': items,
                'total_requests': None,
            })
            return

        m = self.r_summary.match(line)
        if m:
            requests, errors, items = map(int, m.groups())
            meta.update({
                'errors': errors,
                'total_requests': requests,
                'items_reported': items,
            })
        elif line.count('End Time'):
            _,v = line.split(':', 1)
            v = v.strip()
            m = self.r_endtime.match(v)
            ts, tz, seconds = m.groups()
            self.targ['end'] = ts
            self.targ['seconds'] = int(seconds)

    known_bodies = [
        r'^Server:\s+(?P<server>.*?)$',
        r'''
            ^OSVDB-(?P<osvdb>\d+):
            \s
            (?P<path>/.*?):
            \s
            (?P<description>.*?)
            $
        ''',
        r'''
            ^
            OSVDB-(?P<osvdb>\d+):\s+
            (?P<description>.*?)
            $
        ''',
        r'''
            ^\s*
            (?P<description>
                (?P<outdated>.*?)\s
                appears\sto\sbe\soutdated\s
                .*?
            )
            $
        ''',
    ]
    known_bodies = [re.compile(x, re.X) for x in known_bodies]

    def state_body(self, line):
        line = line[2:].strip()
        if line.startswith('ERROR:') or line.count('item(s) reported on remote host'):
            self.state = 'footer'
            self.state_footer(line)
            return
        finding = {}
        self.targ['findings'].append(finding)
        for pattern in self.known_bodies:
            m = pattern.match(line)
            if m:
                finding.update(m.groupdict())
                finding.update(self.findLinksAndStuff(finding.get('description', '')))
                return
        finding['description'] = line
        finding.update(self.findLinksAndStuff(finding.get('description', '')))

    things_to_find = {
        'cve': r'(CVE-\d+-\d+)',
        'bid': r'(BID-\d+)',
        'can': r'(CAN-\d+-\d+)',
        'links': r'''
            (https?://[^\s]+)
        ''',
    }
    for k in things_to_find:
        things_to_find[k] = re.compile(things_to_find[k], re.X | re.I)

    def findLinksAndStuff(self, description):
        ret = {}
        for k,v in self.things_to_find.items():
            found = v.findall(description)
            if found:
                if k == 'links':
                    found = [x.rstrip('.,') for x in found]
                ret[k] = found
        return ret



class NiktoPlugin(plugins.ParserPlugin):
    """
    I parse nikto output
    """

    name = 'nikto'

    def readProbability(self, instream):
        first_part = instream.read(200)
        if first_part.strip().startswith('- Nikto v'):
            return 50

    def parse(self, instream):
        parser = NiktoParser()
        for line in instream:
            parser.dataReceived(line)
        return parser.result
