# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins
from ppo.state import Registry


class theharvesterParser(object):

    reg = Registry()
    handler = None
    handler_data = None

    def __init__(self):
        self.result = {}

    def lineReceived(self, line):
        found = self.reg.find(line)
        if found:
            self.handler, self.handler_data = found
        if self.handler:
            self.handler(line)
            if self.handler_data.get('once', False):
                self.handler = None
                self.handler_data = None


    @reg.route('TheHarvester Ver', once=True)
    def version(self, line):
        parts = line.strip().split()
        version = parts[3]
        self.result.setdefault('theharvester', {})['version'] = version

    @reg.route('Searching in ', once=True)
    def searching_in(self, line):
        place = line.strip().split()[3].strip(':')
        self.result.setdefault('resources', []).append(place)

    @reg.route('Emails found:')
    def emails_found(self, line):
        if line.count('@'):
            self.result.setdefault('emails', []).append(line.strip())

    @reg.route('Hosts found in search engines:')
    def hosts_found(self, line):
        line = line.strip()
        if line[:-1].count(':'):
            ip, hostname = line.split(':')
            self.result.setdefault('hosts', []).append({
                'ip': ip,
                'domain': hostname,
            })





class theharvesterPlugin(plugins.ParserPlugin):
    """
    I parse theharvester output
    """

    name = 'theharvester'

    def readProbability(self, instream):
        preamble = instream.read(560)
        if 'TheHarvester Ver' in preamble:
            return 50

    def parse(self, instream):
        parser = theharvesterParser()
        for line in instream:
            parser.lineReceived(line)
        return parser.result
