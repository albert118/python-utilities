__author__ = "Albert Ferguson, Jeffrey Huang"

"""
.. module:: AuthenticatedUsers
    :platform: Unix, Windows
    :synopsis: CLI setup and config script.
.. moduleauthor:: Albert Ferguson <albertferguson@propertyme.com>
.. moduleauthor:: Jeffrey Huang <jeffreyhuang@propertyme.com>
"""

from .UserSessionsHandler import UserSessionsHandler
    
def AuthenticateUsers(customers: list, baseUrl: str, pauseOnCompletion=False) -> list:
    """
    Attempt to authenticate users and return a list of all sessions.
        
    Parameters
    ----------
    customers: list(list)
        A list of customer credentials. Expecting each inner list to have 1st three cols [customerId, username, password]
    baseUrl: str
        Url to authenticate with
    """

    print("\n== AUTHENTICATING CUSTOMER SESSIONS ==")
    print(f"\nAttempting authentication for {len(customers)} customer(s).")

    handler = UserSessionsHandler(baseAddress=baseUrl) 
    
    for customer in customers:
        handler.AddUserSession(customer[1], customer[2], True)
    
    if pauseOnCompletion:
        print("\n**VALIDATE YOUR CUSTOMER DATA IS AS EXPECTED**")
        _printResults(handler, len(customers))
        input('\nHit "Enter" to continue')
    else:
        _printResults(handler, len(customers))
    
    return handler.Sessions

def _printResults(handler: UserSessionsHandler, numOfCustomers):
    successes = sum([session.IsAuthenticated for session in handler.Sessions])
    print(f"\tObtained {successes} authenticated sessions from {numOfCustomers} customers.")
    print(f"\t{numOfCustomers - successes} attempted authentications failed.")
    