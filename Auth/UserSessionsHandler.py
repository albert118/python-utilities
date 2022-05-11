__author__ = "Albert Ferguson, Jeffrey Huang"

"""
.. module:: UserSessionsHandler
    :platform: Unix, Windows
    :synopsis: User Session handler service.
.. moduleauthor:: Albert Ferguson <albertferguson@propertyme.com> 
.. moduleauthor:: Jeffrey Huang <jeffreyhuang@propertyme.com>
"""

from CommonLib.ListHelpers import FilterList
from .UserSession import UserSession


class UserSessionsHandler():
    """Session handler service."""

    def __init__(self, baseAddress=""):
        self._sessions = list()
        self._baseAddress = baseAddress

    def __repr__(self):
        return f'Handler for {self._baseAddress} with {len(self._sessions)} user sessions.'

    def AddUserSession(self, usr: str, pw: str, authenticateOnInit=False, customerId: str=None) -> UserSession:
        sess = UserSession(usr, pw, self._baseAddress, authenticateOnInit=authenticateOnInit, customerId=customerId)
        self._sessions.append(sess)
        return sess

    def AuthenticateSessions(self):
        for s in self._sessions:
            s.Authenticate()
    
    def GetCustomerUserSession(self, customerId: str) -> UserSession:
        return FilterList(self._sessions, lambda s: s.CustomerId == customerId)

    @property
    def Sessions(self):
        return self._sessions

    
