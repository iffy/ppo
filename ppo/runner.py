# Copyright (c) The ppo team
# See LICENSE for details.

import argparse
import sys
import yaml
import json
import os

import structlog

from io import BytesIO

from ppo.parser import parse, parser, NoWillingParsers

ap = argparse.ArgumentParser(
    description="Reads from stdin and produces YAML output "
    "if it's something `ppo` knows how to interpret. ")

ap.add_argument('-f', '--format',
    default=os.environ.get('PPO_OUTPUT_FORMAT', 'json'),
    choices=['json', 'yaml', 'grep'],
    help='Output format.'
         '  You can also set this with the PPO_OUTPUT_FORMAT '
         'environment variable.'
         '  (current default: %(default)s)')

ap.add_argument('-s', '--strict', action='store_true',
    help="Without this option, unparseable input is returned unchanged. "
         "If --strict is supplied, then an error will be raised if there's "
         "unparseable input.")

ap.add_argument('-v', '--verbose', action='store_true',
    help="Show debug/logging output")

ap.add_argument('-x', '--exclude', action='append',
    default=[_f for _f in os.environ.get('PPO_EXCLUDE_PLUGINS', '').split(',') if _f],
    help='Exclude plugins from being used.  Can be specified multiple times.'
         '  Use --ls to get a list of plugin names.  You can also set this '
         'with a comma-delimited list in PPO_EXCLUDE_PLUGINS.'
         '  (current default: %(default)s)')

ap.add_argument('--ls', action='store_true',
    help='Print out list of parsing plugins and exit')

def run():
    args = ap.parse_args()

    if args.ls:
        print('\n'.join(parser.listPluginNames()))
        sys.exit(0)

    if args.verbose:
        structlog.configure(logger_factory=structlog.PrintLoggerFactory(sys.stderr))

    infile = BytesIO(sys.stdin.read())
    try:
        parsed = parse(infile, exclude=args.exclude)
    except NoWillingParsers:
        if args.strict:
            raise
        else:
            infile.seek(0)
            sys.stdout.write(infile.read())
            sys.exit(0)

    if args.format == 'yaml':
        print(yaml.safe_dump(parsed, default_flow_style=False))
    elif args.format == 'json':
        print(json.dumps(parsed))
    elif args.format == 'grep':
        from ppo.output import giganticGrep
        giganticGrep(parsed, sys.stdout)

