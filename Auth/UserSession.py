__author__ = "Albert Ferguson, Jeffrey Huang"

"""
.. module:: UserSession
    :platform: Unix, Windows
    :synopsis: User session instance creation service.
.. moduleauthor:: Albert Ferguson <albertferguson@propertyme.com>
.. moduleauthor:: Jeffrey Huang <jeffreyhuang@propertyme.com>
"""

import requests as r
from CommonLib.ResponseDecorators import PropertyMeHttpRequestExceptionHandler

DEFAULT_BASE_ADDR =  "https://stage.propertyme.com"

class UserSession():
    """Common PME session creation process.

    Configures:
    * session,
    * headers,
    * cookies.
    """

    def __init__(self, usr: str, pwd: str, baseAddress="", authenticateOnInit=False, customerId: str=None):
        global DEFAULT_BASE_ADDR

        self._usr = usr
        self._pwd = pwd
        self._customerId = customerId

        self._session = r.Session()

        self._baseAddr = DEFAULT_BASE_ADDR if len(baseAddress) == 0 else baseAddress
        self._authUrl = f'{self._baseAddr}/api/auth/credentials'

        if authenticateOnInit:
            self.Authenticate()

    def __repr__(self):
        return f'Login: {self._usr} | IsAuthenticated: {self.IsAuthenticated}'

    def __str__(self):
        return f'Login: {self._usr} | IsAuthenticated: {self.IsAuthenticated}'

    def Authenticate(self):
        authResp = self._PostCredentials()
        
        if authResp is not None:
            sessID = authResp.cookies.get_dict()['ss-id']
            self._session.headers.update({ "ss-id": sessID })

    @PropertyMeHttpRequestExceptionHandler(False)
    def _PostCredentials(self):
        creds = { "UserName": self._usr, "Password": self._pwd, "RememberMe": 'false' }
        self._session.headers.update({ "Accept": "application/json" })
        
        print(f'Authenticating for {self._usr}')
        return self._session.post(self._authUrl, data=creds)

    @property
    def IsAuthenticated(self):
        return self._session.headers.get("ss-id") is not None

    @property
    def Current(self):
        return self._session
    
    @property
    def Username(self):
        return self._usr

    @property
    def CustomerId(self):
        return self._customerId
