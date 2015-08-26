import os
import inspect
from StringIO import StringIO

import sys

class ParseError(Exception): pass
class NoWillingParsers(Exception): pass


def log(*messages):
    sys.stderr.write(' '.join(map(str, messages)) + '\n')


class Parser(object):
    

    def __init__(self):
        self._plugins = []


    def addPlugin(self, plugin):
        self._plugins.append(plugin)


    def parse(self, infile):
        # XXX I don't love reading everything into memory.  It would be
        # better to wrap this file in an always seekable stream that
        # would let you seek to the beginning of stdin.

        guts = infile.read()
        seekable = StringIO(guts)

        chosen = []
        for plugin in self._plugins:
            seekable.seek(0)
            prob = plugin.readProbability(seekable)
            if prob > 0:
                chosen.append((prob, plugin))

        if not chosen:
            raise NoWillingParsers('No parsers could be found to parse the '
                'given input.')

        # highest numerical probability first
        chosen = sorted(chosen, key=lambda x:-x[0])
        first_exception = None
        parsed = None
        for plugin in chosen:
            seekable.seek(0)
            try:
                parsed = plugin.parse(seekable)
            except Exception as e:
                log('Error parsing with %r plugin:\n%s' % (plugin.__name__, e))
                if not first_exception:
                    first_exception = e

        if not parsed:
            raise Exception('Failed to parse using the following plugins: %s' % (
                ', '.join([x.__name__ for x in chosen])))
        return parsed



class ParserPlugin(object):
    """
    Base class for parser plugins.
    """

    def readProbability(self, instream):
        """
        Return a number between 0 and 100 indicating how confident
        this plugin is that it was made to read the given data.
        """
        NotImplemented


    def parse(self, instream):
        """
        Parse the given stream into a Python dict/list/string/integer
        """
        NotImplemented



def getPlugins(plugin_dir):
    """
    Given a directory, get all the plugins out of the python modules inside it.
    """
    files = os.listdir(plugin_dir)
    for fname in files:
        if fname.endswith('.py') and not(fname.startswith('_')):
            ldict = {}
            execfile(os.path.join(plugin_dir, fname), globals(), ldict)
            for value in ldict.values():
                if issubclass(value, ParserPlugin) and value != ParserPlugin:
                    yield value()


def createParser(plugin_dir):
    parser = Parser()
    for plugin in getPlugins(plugin_dir):
        parser.addPlugin(plugin)
    return parser


parser = createParser(os.path.join(os.path.dirname(__file__), 'parse_plugins'))
parse = parser.parse
