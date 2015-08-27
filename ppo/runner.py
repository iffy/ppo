import argparse
import sys
import yaml
import json
import os

from StringIO import StringIO

from ppo.parser import parse, parser, NoWillingParsers

ap = argparse.ArgumentParser(
    description="Reads from stdin and produces YAML output "
    "if it's something `ppo` knows how to interpret. ")

ap.add_argument('-f', '--format',
    default=os.environ.get('PPO_OUTPUT_FORMAT', 'json'),
    choices=['json', 'yaml'],
    help='Output format.'
         '  You can also set this with the PPO_OUTPUT_FORMAT '
         'environment variable.'
         '  (default: %(default)s)')

ap.add_argument('-p', '--passthru-unknown', action='store_true',
    help="If given, then input that isn't able to be parsed will be "
         "returned unchanged.  Use this if you don't want "
         "NoWillingParsers exceptions for a format you know can't "
         "be processed.")

ap.add_argument('--ls', action='store_true',
    help='Print out list of parsing plugins and exit')

def run():
    args = ap.parse_args()

    if args.ls:
        print '\n'.join(parser.listPluginNames())
        sys.exit(0)

    infile = StringIO(sys.stdin.read())
    try:
        parsed = parse(infile)
    except NoWillingParsers:
        if args.passthru_unknown:
            infile.seek(0)
            sys.stdout.write(infile.read())
            sys.exit(0)
        else:
            raise

    if args.format == 'yaml':
        print yaml.dump(parsed, default_flow_style=False)
    elif args.format == 'json':
        print json.dumps(parsed)
