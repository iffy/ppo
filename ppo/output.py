
import re

r_ws = re.compile(r'\s+')


def _flattenThing(thing):
    if isinstance(thing, dict):
        keys = sorted(thing)
        simples = []
        multis = []
        for key in keys:
            value = thing[key]
            flattened = _flattenThing(value)
            if value and isinstance(value, (dict, list, tuple)):
                # multi
                multis.append((key, flattened))
            else:
                # simple
                simples.append((key, flattened))

        # do the single simple line first
        simple_line = []
        for k,v in simples:
            value = (list(v) or ['[]'])[0]
            simple_line.append('%s: %s' % (r_ws.sub('_', k), value))
        simple_line = ' '.join(simple_line)
        yield simple_line

        # do the combinations
        for k,v in multis:
            for item in v:
                part = '%s: %s' % (k, item)
                yield ' '.join([simple_line, part])

    elif isinstance(thing, (list, tuple)):
        for item in thing:
            for x in _flattenThing(item):
                yield x
    else:
        if isinstance(thing, unicode):
            thing = thing.encode('utf-8')
        elif not isinstance(thing, str):
            thing = str(thing)
        yield r_ws.sub('_', thing)

def giganticGrep(data, outstream):
    """
    Flatten data structures so that they're very greppable
    """
    for line in _flattenThing(data):
        outstream.write(line + '\n')
    outstream.flush()