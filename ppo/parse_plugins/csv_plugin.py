# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins

from io import BytesIO
import csv
import codecs


class CSVParser(plugins.ParserPlugin):
    """
    I parse CSV files
    """

    name = 'csv'

    def readProbability(self, instream):
        d = BytesIO()
        commas = set()
        for i in range(4):
            line = instream.readline()
            if not line:
                break
            commas.add(line.count(b','))
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
        parsed = csv.DictReader(codecs.getreader('utf-8')(instream))
        return {
            'data': list(parsed),
        }

