"""
Dynamically generate the test cases based on input and
output files in `cases/`

The files in `cases/` ought to be named using the following pattern:

    in-<some description>[.<ext>]
    out-<some description>(.yml|.json)

See the directory for examples.

Each `in-` file will be parsed and compared to each `out-` file.

"""
from unittest import TestCase
import os
import re
import json
import yaml
from collections import defaultdict
from ppo import parse

r_notalpha = re.compile(r'[^a-zA-Z0-9]', re.S | re.M)


thisdir = os.path.abspath(os.path.dirname(__file__))
sample_dir = os.path.join(thisdir, 'cases')

all_files = os.listdir(sample_dir)
in_files = []
out_files = []
pairs = defaultdict(lambda:{'in':None,'out':None})
for f in all_files:
    direction, rest = f.split('-', 1)
    body = rest.rsplit('.', 1)[0]
    pairs[body][direction] = os.path.join(sample_dir, f)



class TestEverything(TestCase):
    pass


def makeTestFunc(name, infile, outfile):
    def func(self):
        fh_i = open(infile, 'rb')
        parsed = parse(fh_i)
        
        expected_output = None
        fh_o = open(outfile, 'rb')
        if outfile.endswith('yml'):
            expected_output = yaml.load(fh_o)
        elif outfile.endswith('json'):
            expected_output = json.load(fh_o)
        else:
            # plain text
            expected_output = open(outfile, 'rb').read()

        self.assertEqual(parsed, expected_output)
    return func

for name, files in pairs.items():
    test_name = 'test_' + r_notalpha.sub('', name)
    setattr(TestEverything, test_name,
        makeTestFunc(test_name, files['in'], files['out']))
    