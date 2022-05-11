__all__ = ["GetTableData", "ProcessStatements", "UpdateTableDataForCustomers"]
__author__ = "Albert Ferguson, Jeffrey Huang"

"""
.. module:: Database
    :platform: Unix, Windows
    :synopsis: Database communication
.. moduleauthor:: Albert Ferguson <albertferguson@propertyme.com>
.. moduleauthor:: Jeffrey Huang <jeffreyhuang@propertyme.com>
"""

from .ReadDb import GetTableData
from .WriteDb import ProcessStatements, UpdateTableDataForCustomers
from .ParsingHelpers import *
from .ContextBox import *
