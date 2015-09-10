# Copyright (c) The ppo team
# See LICENSE for details.


class Registry(object):
    """
    This is a descriptor that can be used to match patterns to functions
    that will handle the pattern.

    See parse_plugins/snmpcheck_plugin.py for example usage.
    """

    def __init__(self, instance=None, data=None):
        self.data = data or {}
        self._instance = instance

    def __get__(self, obj, cls):
        return Registry(obj, self.data)

    def route(self, name, **data):
        data = data.copy()
        def deco(f):
            self.data[name] = data
            self.data[name]['func'] = f
            return f
        return deco


    def find(self, name):
        """
        Find a matching handler.

        @return: A 2-tuple of bound handler and any associated handler data
        """
        for pattern, data in self.data.items():
            if pattern in name:
                bound = data['func'].__get__(
                    self._instance, self._instance.__class__)
                return bound, data
