# Copyright (c) The ppo team
# See LICENSE for details.

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
import io
import json
import yaml
import difflib
from collections import defaultdict
from ppo.parser import parse

import structlog


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
    
    maxDiff = None


def diffStrings(a, b, alabel=None, blabel=None):
    alines = [x+'\n' for x in a.split('\n')]
    blines = [x+'\n' for x in b.split('\n')]
    for line in difflib.unified_diff(alines, blines, alabel, blabel):
        yield line


def makeTestFunc(name, infile, outfile):
    def func(self):
        structlog.get_logger().msg(testcase=name)
        with io.open(infile, 'rb') as fh_i:
            parsed = parse(fh_i)
        
        expected_output = None
        if outfile is None:
            self.fail('No expected output file present')
        with io.open(outfile, 'rb') as fh_o:
            if outfile.endswith('yml'):
                expected_output = yaml.load(fh_o)
            elif outfile.endswith('json'):
                expected_output = json.load(fh_o)
            else:
                # plain text
                expected_output = fh_o.read()

        # seeing differences in YAML is easier than python dicts
        expected_yaml = yaml.safe_dump(expected_output, default_flow_style=False)
        actual_yaml = yaml.safe_dump(parsed, default_flow_style=False)
        diff = diffStrings(expected_yaml, actual_yaml, 'expected', 'actual')
        self.assertEqual(expected_yaml, actual_yaml, '\n' + ''.join(diff))
    return func

for name, files in pairs.items():
    test_name = 'test_' + r_notalpha.sub('', name)
    setattr(TestEverything, test_name,
        makeTestFunc(test_name, files['in'], files['out']))
    