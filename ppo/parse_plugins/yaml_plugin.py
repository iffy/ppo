# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins

from StringIO import StringIO
import yaml
import re
import traceback


class YAMLParser(plugins.ParserPlugin):
    """
    I parse YAML
    """

    name = 'yaml'

    def readProbability(self, instream):
        first_part = instream.read(200)
        try:
            yaml.safe_load(StringIO(first_part))
            return 10
        except yaml.scanner.ScannerError:
            return 1

    def parse(self, instream):
        return yaml.safe_load(instream)



class EqualDelimitedPlugin(plugins.ParserPlugin):
    """
    I parse lists of variables delimited by equal signs.
    """

    name = 'equal-delimited'

    r_candidate = re.compile(r'''
        [^=]+?=[.\s]*
        ''', re.X)

    r_sub = re.compile(r'\n[ \t]*', re.S | re.M)

    def readProbability(self, instream):
        # try about 10 lines
        found_match = False
        for i in xrange(10):
            line = instream.readline()
            if not line:
                break
            if not line.strip():
                continue
            if not self.r_candidate.match(line):
                return 0
            else:
                found_match = True
        if found_match:
            return 20

    def parse(self, instream):
        guts = instream.read()
        guts = guts.replace('=', ': ')
        guts = self.r_sub.sub('\n', guts)
        try:
            result = yaml.safe_load(StringIO(guts))
        except Exception as e:
            traceback.print_exc()
            raise
        return result
        