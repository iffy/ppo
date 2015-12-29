# Copyright (c) The ppo team
# See LICENSE for details.

import os
import inspect
import sys
import importlib
import traceback
from io import BytesIO

import structlog

logger = structlog.get_logger()

# silent by default
structlog.configure(logger_factory=structlog.ReturnLoggerFactory())


from ppo import plugins

class ParseError(Exception): pass
class NoWillingParsers(Exception): pass



class Parser(object):
    

    def __init__(self):
        self._plugins = []


    def addPlugin(self, plugin):
        self._plugins.append(plugin)


    def listPluginNames(self):
        return [x.name for x in self._plugins]


    def parse(self, infile, exclude=None):
        log = logger.bind(action='parse')
        exclude = exclude or []
        if exclude:
            log.msg(excluding=exclude)

        guts = infile.read()
        # XXX I don't love reading everything into memory.  It would be
        # better to wrap this file in an always seekable stream that
        # would let you seek to the beginning of stdin.
        seekable = BytesIO(guts)

        chosen = []
        log.msg('Finding candidate plugins...')
        for plugin in self._plugins:
            l = log.bind(plugin=plugin.name)

            if plugin.name in exclude:
                l.msg('excluded')
                continue

            seekable.seek(0)
            try:
                prob = plugin.readProbability(seekable)
                l.msg(reported_prob=prob)
            except Exception:
                l.msg(exc_info=True)
                prob = 0
            if prob is not None and prob > 0:
                chosen.append((prob, plugin))

        if not chosen:
            raise NoWillingParsers('No parsers could be found to parse the '
                'given input.')

        # highest numerical probability first
        chosen = [x[1] for x in sorted(chosen, key=lambda x:-x[0])]
        errors = []
        parsed = None
        log.msg('Attempting to parse...')
        for plugin in chosen:
            l = log.bind(plugin=plugin.name)
            seekable.seek(0)
            try:
                parsed = plugin.parse(seekable)
                if parsed is not None:
                    l.msg('success')
                    # add ppo metadata
                    parsed['_ppo'] = {
                        'parser': plugin.name,
                    }
                    break
                else:
                    l.msg('no output')
            except Exception:
                err_string = traceback.format_exc()
                errors.append((plugin.name, err_string))
                l.msg('failure', traceback=err_string)

        if parsed is None:
            log.msg('no parsed data')
            for plugin_name, err_string in errors:
                log.msg(plugin=plugin.name, traceback=err_string)
            raise Exception('Failed to parse using these plugins: %s '
                            '(excluded plugins: %s)' % (
                    ', '.join([x.name for x in chosen]),
                    ', '.join(exclude)))
        return parsed


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
