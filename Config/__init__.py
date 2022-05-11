__author__ = "Albert Ferguson, Jeffrey Huang"
__all__ = ["ConfigureUrl", "ConfigurePropertyMeBaseUrl", "ConfigureMySqlConnectionString", "ConfigureDbTableName", "ConfigureCsvFilename"]

"""
.. module:: Config
    :platform: Unix, Windows
    :synopsis: Configuration of variables
.. moduleauthor:: Albert Ferguson <albertferguson@propertyme.com>
.. moduleauthor:: Jeffrey Huang <jeffreyhuang@propertyme.com>
"""

from .ConfigureCsvFilename import ConfigureCsvFilename
from .ConfigureDbTableName import ConfigureDbTableName
from .ConfigureMySqlConnectionString import ConfigureMySqlConnectionString
from .ConfigurePropertyMeBaseUrl import ConfigurePropertyMeBaseUrl
from .ConfigureUrl import ConfigureUrl
