# Copyright (c) The ppo team
# See LICENSE for details.

class ParserPlugin(object):
    """
    Base class for parser plugins.
    """

    @property
    def name(self):
        return self.__class__.__name__

    def readProbability(self, instream):
        """
        Return a number between 0 and 100 indicating how confident
        this plugin is that it was made to read the given data.
        """
        NotImplemented


    def parse(self, instream):
        """
        Parse the given stream into a Python dict/list/string/integer
        """
        NotImplemented
