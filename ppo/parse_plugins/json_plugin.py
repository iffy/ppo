# Copyright (c) The ppo team
# See LICENSE for details.

from ppo import plugins

import json


class JSONParser(plugins.ParserPlugin):
    """
    I parse JSON
    """

    name = 'json'

    def readProbability(self, instream):
        first_part = instream.read(200)
        prob = 1
        if first_part.startswith('"'):
            prob = 5
        elif first_part.startswith('['):
            prob = 15
        elif first_part.startswith('{'):
            prob = 20
        return prob

    def parse(self, instream):
        return json.load(instream)
