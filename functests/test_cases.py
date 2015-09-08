# Copyright (c) The ppo team
# See LICENSE for details.

"""
Dynamically generate the test cases based on input and
output files in `cases/`

The files in `cases/` ought to be named using the following pattern:

    in-<some description>[.<ext>]
    out-<some description>(.yml|.json)
    norm-<some description>(.yml|.json)

See the directory for examples.

Each `in-` file will be parsed and compared to each `out-` file.
Each `out-` file will be normalized and compared to each `norm-` file.

"""
from unittest import TestCase
import os
import re
import json
import yaml
import difflib
from collections import defaultdict
from ppo.parser import parse, normalize

r_notalpha = re.compile(r'[^a-zA-Z0-9]', re.S | re.M)


thisdir = os.path.abspath(os.path.dirname(__file__))
sample_dir = os.path.join(thisdir, 'cases')

all_files = os.listdir(sample_dir)
in_files = []
out_files = []
samples = defaultdict(lambda:{'in':None,'out':None,'norm':None})
for f in all_files:
    direction, rest = f.split('-', 1)
    body = rest.rsplit('.', 1)[0]
    samples[body][direction] = os.path.join(sample_dir, f)



class TestParse(TestCase):
    
    maxDiff = None


class TestNormalize(TestCase):

    maxDiff = None


def diffStrings(a, b, alabel=None, blabel=None):
    alines = [x+'\n' for x in a.split('\n')]
    blines = [x+'\n' for x in b.split('\n')]
    for line in difflib.unified_diff(alines, blines, alabel, blabel):
        yield line


def makeTestFunc(name, infile, outfile, func):
    def metafunc(self):
        fh_i = open(infile, 'rb')
        parsed = func(fh_i)
        
        expected_output = None
        if outfile is None:
            self.fail('No expected output file present')
        fh_o = open(outfile, 'rb')
        if outfile.endswith('yml'):
            expected_output = yaml.load(fh_o)
        elif outfile.endswith('json'):
            expected_output = json.load(fh_o)
        else:
            # plain text
            expected_output = open(outfile, 'rb').read()

        # seeing differences in YAML is easier than python dicts
        expected_yaml = yaml.dump(expected_output, default_flow_style=False)
        actual_yaml = yaml.dump(parsed, default_flow_style=False)
        diff = diffStrings(expected_yaml, actual_yaml, 'expected', 'actual')
        self.assertEqual(expected_yaml, actual_yaml, '\n' + ''.join(diff))
    return metafunc

for name, files in samples.items():
    test_name = 'test_' + r_notalpha.sub('', name)
    
    # in -> out
    setattr(TestParse, test_name,
        makeTestFunc(test_name, files['in'], files['out'], parse))

    # out -> norm
    setattr(TestNormalize, test_name,
        makeTestFunc(test_name, files['out'], files['norm'], normalize))

