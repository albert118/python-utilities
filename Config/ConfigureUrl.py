__author__ = "Albert Ferguson, Jeffrey Huang"

"""
.. module:: ConfigureUrl
    :platform: Unix, Windows
    :synopsis: CLI setup and config script.
.. moduleauthor:: Albert Ferguson <albertferguson@propertyme.com>
.. moduleauthor:: Jeffrey Huang <jeffreyhuang@propertyme.com>
"""

def ConfigureUrl(defaultUrl: str, otherShortcutOptions: dict = {}) -> str:
    """
    Allow user to configure a url with unlimited confirmations and re-attempts. The selected url will be the return value.
    
    Parameters
    ----------
    defaultBaseUrl : str
        The default url to use if nothing is entered by the user
    otherShortcutOptions : dict, optional
        key is the shortcut the user may type in. Value for the key represent the url value
    """

    print("\n== CONFIGURING URL ==")
    
    while True:
        url = GetUserEnteredUrl(defaultUrl, otherShortcutOptions)
    
        if _proceedWithConfig():
            return url
            
        print("\n********************************************************************************")
        

def GetUserEnteredUrl(defaultUrl: str, otherShortcutOptions: dict) -> str:
    """Setup the user configuration for a test environment."""
    
    print(f'\nShortcut options:')
    print(f'- Entering no value will use default URL "{defaultUrl}"')
    for shortcut, shortcutUrl in otherShortcutOptions.items():
        print(f'- Enter "{shortcut}" to use "{shortcutUrl}"')

    inputUrl = input("\n\tEnter URL: ")
    
    url = defaultUrl if not inputUrl else otherShortcutOptions.get(inputUrl)
    if url is None:
        url = inputUrl
    
    print(f'\tSelected URL: {url}')
    
    return url

def _proceedWithConfig() -> bool:
    """Prompt the user for a retry event."""

    retryChar = 'n'
    instruction = f"(Enter '{retryChar}' to retry, else type any other character to continue): "

    return input(f'\nDo you want to proceed with this configuration? {instruction}') != retryChar
