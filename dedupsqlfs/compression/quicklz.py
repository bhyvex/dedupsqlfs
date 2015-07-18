# -*- coding: utf8 -*-

__author__ = 'sergey'

"""
Class for QuickLz compression helper
"""

from dedupsqlfs.compression import BaseCompression

class QuickLzCompression(BaseCompression):

    _method_name = "quicklz"

    _minimal_size = 17

    _has_comp_level_options = False

    pass
