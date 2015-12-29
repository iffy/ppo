import six
import re

r_ws = re.compile(six.u(r'\s+'))


def yieldText(f):
    """
    Make sure text is returned (py3:str, py2:unicode)
    """
    @six.wraps(f)
    def func(*args, **kwargs):
        for x in f(*args, **kwargs):
            if isinstance(x, six.binary_type):
                yield x.decode('utf-8')
            elif not isinstance(x, six.text_type):
                yield six.text_type(x)
            else:
                yield x
    return func


@yieldText
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
            simple_line.append('{0}: {1}'.format(r_ws.sub('_', k), value))
        simple_line = ' '.join(simple_line)
        yield simple_line

        # do the combinations
        for k,v in multis:
            for item in v:
                part = '{0}: {1}'.format(k, item)
                yield ' '.join([simple_line, part])

    elif isinstance(thing, (list, tuple)):
        for item in thing:
            for x in _flattenThing(item):
                yield x
    else:
        if isinstance(thing, six.binary_type):
            thing = thing.decode('utf-8')
        elif not isinstance(thing, six.text_type):
            thing = six.text_type(thing)
        yield r_ws.sub(six.u('_'), thing)

def giganticGrep(data, outstream):
    """
    Flatten data structures so that they're very greppable
    """
    for line in _flattenThing(data):
        outstream.write(line + '\n')
    outstream.flush()
