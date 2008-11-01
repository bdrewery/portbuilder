"""
The Port module.  This module contains all classes and utilities needed for
managing port information.
"""
from dependhandler import DependHandler
from port import Port
from portcache import PortCache

__all__ = ['cache', 'get', 'Port', 'DependHandler']

#: A cache of ports available with auto creation features
cache = PortCache()
get = cache.get  #: Alias for port_cache.get
