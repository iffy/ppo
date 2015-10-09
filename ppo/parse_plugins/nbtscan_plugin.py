# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins


class nbtscanParser(object):

    def __init__(self):
        self.result = {}
        self.intable = False

    def lineReceived(self, line):
        if 'target' not in self.result:
            self.result['target'] = line.split()[-1]
        elif line.startswith('-------'):
            self.intable = True
        elif self.intable and line.strip():
            ip, name, server, user, mac = line.split()
            self.result.setdefault('results', []).append({
                'ip': ip,
                'name': name,
                'server': server,
                'user': user,
                'mac': mac,
            })


class nbtscanPlugin(plugins.ParserPlugin):
    """
    I parse nbtscan output
    """

    name = 'nbtscan'

    def readProbability(self, instream):
        firstline = instream.readline()
        if 'NBT name scan' in firstline:
            return 50

    def parse(self, instream):
        parser = nbtscanParser()
        for line in instream:
            parser.lineReceived(line)
        return parser.result
