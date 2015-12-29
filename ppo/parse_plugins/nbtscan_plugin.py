# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins
import structlog

logger = structlog.get_logger()

class nbtscanParser(object):

    intable = False
    ranges = None
    labels = [
        ('IP address', 'ip'),
        ('NetBIOS Name', 'name'),
        ('Server', 'server'),
        ('User', 'user'),
        ('MAC address', 'mac'),
    ]

    def __init__(self):
        self.result = {}

    def lineReceived(self, line):
        logger.msg(line=line)
        if not line.strip():
            return
        if 'target' not in self.result:
            # get the target
            self.result['target'] = line.split()[-1]
        elif not self.ranges:
            # have to determine table ranges
            starts = []
            for label,key in self.labels:
                starts.append(line.index(label))
            self.ranges = []
            for i in range(len(starts)-1):
                self.ranges.append((starts[i], starts[i+1]))
            self.ranges.append((starts[-1],None))
        elif line.startswith('-------'):
            # what follows is data
            self.intable = True
        elif self.intable:
            item = {}
            for r,(label,key) in zip(self.ranges, self.labels):
                data = line[r[0]:r[1]].strip() or None
                item[key] = data
            self.result.setdefault('results', []).append(item)


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
