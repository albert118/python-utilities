__author__ ="Albert Ferguson"
__all__ = ["DataGen"]

"""
.. module:: DataGeneration
    :platform: Unix, Windows
    :synopsis: Easy data generation for entities.

.. moduleauthor:: Albert Ferguson <albertferguson@propertyme.com>

Call a DataGen with an implementation of DataBuilder to create a custom generator.
"""

from .ContactBuilder import ContactBuilder
from .DataBuilder import DataBuilder
from .DataGen import DataGen
from .LotBuilder import LotBuilder
from .TenancyBuilder import TenancyBuilder
