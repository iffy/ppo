
import itertools
import re

r_ws = re.compile(r'\s+')


def _flattenThing(thing):
    if isinstance(thing, dict):
        keys = sorted(thing)
        simples = []
        multi_keys = []
        multi_vals = []
        for key in keys:
            value = list(_flattenThing(thing[key]))
            if not value or len(value) == 1:
                # simple
                simples.append((key, value or ['']))
            else:
                # multi
                multi_keys.append(key)
                multi_vals.append(value)

        # do the single simple line first
        simple_line = []
        for k,v in simples:
            value = (list(v) or [''])[0]
            simple_line.append('%s:\t%s' % (k, value))
        simple_line = '\t'.join(simple_line)
        yield simple_line

        p = itertools.product(*multi_vals)
        if multi_vals:
            for value_set in (zip(multi_keys,value_set) for value_set in p):
                parts = []
                for k,v in value_set:
                    parts.append('%s:\t%s' % (k,v))
                if simple_line:
                    parts = [simple_line] + parts
                yield '\t'.join(parts)

    elif isinstance(thing, (list, tuple)):
        for item in thing:
            for x in _flattenThing(item):
                yield x
    else:
        if isinstance(thing, unicode):
            thing = thing.encode('utf-8')
        elif not isinstance(thing, str):
            thing = str(thing)
        for line in thing.split('\n'):
            yield line

def giganticGrep(data, outstream):
    """
    Flatten data structures so that they're very greppable
    """
    for line in _flattenThing(data):
        outstream.write(line + '\n')
    outstream.flush()