# Copyright (c) The ppo team
# See LICENSE for details.

import codecs

from ppo import plugins

from structlog import get_logger


class IPTablesLParser(plugins.ParserPlugin):
    """
    I parse output from iptables -L
    """

    name = 'iptables'

    def readProbability(self, instream):
        first_part = instream.read(200)
        if first_part.startswith(b'Chain') and b'policy' in first_part:
            return 50

    def parse(self, instream):
        log = get_logger()
        instream = codecs.getreader('utf-8')(instream)
        ret = {}
        current = None
        spacing = []
        for line in instream:
            log.msg(line=line)
            if line.startswith('Chain'):
                # line = 'Chain INPUT (policy ACCEPT 47 packets, 4639 bytes)'
                parts = line.replace('(', '').replace(')', '').replace(',', '').split()
                ret[parts[1]] = current = {'items': []}
                policy = {}
                current[parts[3]] = policy

                try:
                    i = parts.index('packets')
                    policy['packets'] = parts[i-1]
                except ValueError:
                    pass

                try:
                    i = parts.index('bytes')
                    policy['bytes'] = parts[i-1]
                except ValueError:
                    pass
            elif not line.strip():
                continue
            elif line.count('target'):
                # line = ' pkts bytes target     prot opt in     out     source               destination         '
                parts = line.split()
                spacing = []
                for part in parts:
                    spacing.append({
                        'key': part,
                        'start': line.index(part),
                        'end': None,
                    })
                    if len(spacing) >= 2:
                        spacing[-2]['end'] = spacing[-1]['start']
            else:
                # line = '   20  1817 ACCEPT     all  --  *      *       192.168.13.206       0.0.0.0/0           '
                row = {}
                for space in spacing:
                    row[space['key']] = line[space['start']:space['end']].strip()
                current['items'].append(row)
        return ret
