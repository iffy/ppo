# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins

from StringIO import StringIO
import csv


class CSVParser(plugins.ParserPlugin):
    """
    I parse CSV files
    """

    name = 'csv'

    def readProbability(self, instream):
        d = StringIO()
        commas = set()
        for i in xrange(4):
            line = instream.readline()
            if not line:
                break
            commas.add(line.count(','))
            d.write(line)
        try:
            list(csv.DictReader(d))
            if min(commas) > 0:
                if len(commas) == 1:
                    return 20
                else:
                    return 15
            return 0
        except Exception:
            pass

    def parse(self, instream):
        parsed = csv.DictReader(instream)
        return {
            'data': list(parsed),
        }

