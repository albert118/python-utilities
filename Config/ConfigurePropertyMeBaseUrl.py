from .ConfigureUrl import ConfigureUrl

def ConfigurePropertyMeBaseUrl():
    defaultBaseUrl = "http://localhost:8080"
    
    otherShortcutOptions = {
        "dev1": "https://app-dev1.sandbox.propertyme.com",
        "dev2": "https://app-dev2.sandbox.propertyme.com",
        "master": "https://master-app.propertyme.com",
        "uat": "https://uat-app.propertyme.com",
        "stage": "https://stage.propertyme.com"
    }
        
    url = ConfigureUrl(defaultBaseUrl, otherShortcutOptions);
    
    return url