# Copyright (c) The ppo team
# See LICENSE for details.

import os
import inspect
import sys
import importlib
import traceback
from StringIO import StringIO

from ppo import plugins

class ParseError(Exception): pass
class NoWillingParsers(Exception): pass


def log(*messages):
    sys.stderr.write(' '.join(map(str, messages)) + '\n')


class Parser(object):
    

    def __init__(self):
        self._plugins = {}


    def addPlugin(self, plugin):
        self._plugins[plugin.name] = plugin


    def listPluginNames(self):
        return list(self._plugins)


    def parse(self, infile):
        # XXX I don't love reading everything into memory.  It would be
        # better to wrap this file in an always seekable stream that
        # would let you seek to the beginning of stdin.

        guts = infile.read()
        seekable = StringIO(guts)

        chosen = []
        for plugin in self._plugins.values():
            seekable.seek(0)
            try:
                prob = plugin.readProbability(seekable)
            except Exception:
                log('Misbehaving parser: %r' % (plugin.name,))
                traceback.print_exc()
                prob = 0
            if prob > 0:
                chosen.append((prob, plugin))

        if not chosen:
            raise NoWillingParsers('No parsers could be found to parse the '
                'given input.')

        # highest numerical probability first
        chosen = [x[1] for x in sorted(chosen, key=lambda x:-x[0])]
        errors = []
        parsed = None
        for plugin in chosen:
            seekable.seek(0)
            try:
                parsed = plugin.parse(seekable)
                # add ppo metadata
                if '_ppo' not in parsed:
                    parsed['_ppo'] = {}

                if 'parser' not in parsed['_ppo']:
                    parsed['_ppo']['parser'] = plugin.name
                break
            except Exception:
                err_string = traceback.format_exc()
                errors.append((plugin.name, err_string))

        if parsed is None:
            for plugin_name, err_string in errors:
                log('# Error in %s plugin:\n%s' % (plugin_name, err_string))
            raise Exception('Failed to parse using these plugins: %s' % (
                ', '.join([x.name for x in chosen])))
        return parsed


    def normalize(self, data):
        """
        Normalize already-parsed data.
        """
        plugin_name = data['_ppo']['parser']
        plugin = self._plugins[plugin_name]
        normalized = plugin.normalize(data)
        normalized['_ppo'] = data['_ppo'].copy()
        normalized['_ppo']['normalized'] = True
        return normalized


def getPlugins(package):
    """
    Given a directory, get all the plugins out of the python modules inside it.
    """
    if package in sys.modules:
        imported = sys.modules[package]
    elif package not in sys.modules:
        imported = __import__(package, globals(), locals())
    item = getattr(imported, package.split('.')[-1])
    path = os.path.abspath(os.path.dirname(item.__file__))
    
    files = os.listdir(path)
    for fname in files:
        if fname.endswith('.py') and not(fname.startswith('_')):
            module_name = '.'.join([package, os.path.basename(fname).split('.')[0]])
            imported = importlib.import_module(module_name)
            for name in dir(imported):
                item = getattr(imported, name)
                if inspect.isclass(item) and \
                        issubclass(item, plugins.ParserPlugin) and \
                        item != plugins.ParserPlugin:
                    yield item()


def createParser(package):
    parser = Parser()
    for plugin in getPlugins(package):
        parser.addPlugin(plugin)
    return parser


parser = createParser('ppo.parse_plugins')
parse = parser.parse
normalize = parser.normalize
