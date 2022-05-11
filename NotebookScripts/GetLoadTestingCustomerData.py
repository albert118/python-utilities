#!/usr/bin/env python
# coding: utf-8

# # Get Load Testing Customer Data
# 
# Initialise the testing data inputs from the database. This data is used in further testing scripts as an input csv. The output of this script should not be modified and considered readonly.
# 
# ## Prerequisites:
# --------------------
# 
# **THIS IS THE PRERQUISITE!**
# 
# ## Workflow:
# --------------------
# 
# 1. Configure a db connection and filenames.
# 2. Login as an existing user.
# 3. Create a new portfolio (Customer)
#  * This creates a "blank slate" to copy from
# 4. Remove Existing Lots, Tenancies, and Folios (Blank Slate)
# 5. Clone the Default User
#   * This allows setting a custom username + password for testing logins.
# 6. Save to an ouput csv.

# In[ ]:


from pprint import PrettyPrinter

import pandas as pd
from Auth import UserSession, UserSessionsHandler
from CommonLib import ConsoleHelpers, NotebookHelper
from CommonLib.ResponseDecorators import PropertyMeHttpRequestExceptionHandler
from Config import (ConfigureCsvFilename, ConfigureMySqlConnectionString,
                    ConfigurePropertyMeBaseUrl)
from Database import ContextBox


# ## 1. Configure a db connection and filenames
# --------------------

# In[ ]:


fullFilenameDefault = 'deep-aa-load-test-customer-data'

baseUrl = None
fullFilename = None
dbString = None

csvPreamble = """A csv will be generated from this db read."""
csvExplanation = """
        The csv will set columns titled: 
        {}
        
        If these values are missing, then subsequent operations may fail
        unexpectedly. Check once done that these columns look correct!
        """

adminEmail = "dev@propertyme.com"
adminPassword = "es3mb9kwk0"

testEmail = "new_aaloadtestinguser@propertyme.com"
testPassword = "abcde1235" 

# Get message template id
defaultMessageTemplateId = '70c4f725-a0e1-11e8-b126-a08cfde6627b'


# In[ ]:


# Retrieve the load testing customer data
print("********************************************************************************")
print("\n== CONFIGURING PME URL BASE ==")
if not baseUrl:
    baseUrl = ConfigurePropertyMeBaseUrl()

print("\n== CONFIGURING DB CONN ==")
if not dbString:
    dbString = ConfigureMySqlConnectionString()
    
print("\n== CONFIGURING CSV ==")
if not fullFilename:
    fullFilename = ConfigureCsvFilename(fullFilenameDefault)
    
print("\n== CONFIGURING LOGIN TO CLONE FROM ==")
useSpecialLogin = input("Use the default dev@propertyme.com account? ('n' to input new credentials)").lower().strip() == 'n'
if useSpecialLogin:
    _adminEmail = None
    _adminPassword = None
    
    while not _adminEmail or len(adminEmail) == 0:
        _adminEmail = input("Email: ")
    
    adminEmail = _adminEmail
    
    while not _adminPassword or len(_adminPassword) == 0:
        _adminPassword = input("Password: ")
    
    adminEmail = _adminPassword

print(f"Using email: {adminEmail} and password: {adminPassword} herein.")
print("\n********************************************************************************")


# ## 2. Login as the default user
# --------------------

# In[ ]:


# Configure the default admin authentication session.
print("********************************************************************************")
print("\n== AUTH DEFAULT USER ==")

pmeHandler = UserSessionsHandler(baseUrl)
pmeHandler.AddUserSession(adminEmail, adminPassword)
pmeHandler.AuthenticateSessions()

print('\n\n**CHECK CUSTOMER DATA IS ALL EXPECTED**')
print(f"{len(pmeHandler.Sessions)} sessions were created.")
print(f"Session summary:\t{pmeHandler.Sessions[:5]}")
endSectionMessage = "To re-execute the script and start again, close the program."
ConsoleHelpers.PreventImmediateConsoleClose(endSectionMessage)

print("\n********************************************************************************")


# ## 3. Create a New Portfolio (Customer)
# --------------------

# In[ ]:


# Clone the test portfolio
print("********************************************************************************")
print("\n== CLONING TEST PORTFOLIO ==")

newPortfolio = baseUrl + "/api/billing/portfolio/new"
print(f"POSTs for cloning the portfolio will be made to {newPortfolio}.")

@PropertyMeHttpRequestExceptionHandler(True)
def NewPortfolioRequest(requestSession: UserSession, data: dict):
    global newPortfolio
    return requestSession.Current.post(newPortfolio, data=data)

def NewTestPortfolio() -> dict:
    return {
        "CompanyName": "BLANK SLATE Co.",
        "RegionCode": "AU_NSW",
        "IsForPortalTest": False
    }

newRes = NewPortfolioRequest(pmeHandler.Sessions[0], NewTestPortfolio())
customerId = newRes.json().get("CustomerId") if newRes else 'NaN'

print(f'new customerId {customerId}')
print("\n********************************************************************************")


# ## 4. Remove Existing Lots, Tenancies, and Folios
# --------------------

# In[ ]:


print("********************************************************************************")
print("\n== CLEANING EXISTING DATA ==\n")

@ContextBox.DatabaseConnection()
def WipeOutData():
    conn = ContextBox.GetConnection(dbString)
    
    sqlString1= f"""SET SQL_SAFE_UPDATES = 0; """
    sqlString2= f"""DELETE FROM lot WHERE CustomerId='{customerId}';"""
    sqlString3= f"""DELETE FROM folio WHERE CustomerId='{customerId}';"""
    sqlString4= f"""DELETE FROM tenancy WHERE CustomerId='{customerId}';"""
    sqlString5= f"""SET SQL_SAFE_UPDATES = 1;"""
    
    conn.execute(sqlString1)
    conn.execute(sqlString2)
    conn.execute(sqlString3)
    conn.execute(sqlString4)
    conn.execute(sqlString5)
    
    return

WipeOutData()
print("\n********************************************************************************")


# ## 5. Clone the Current User
# --------------------

# In[ ]:


# Clone the current user
print("********************************************************************************")
print("\n== CLONING CURRENT USER ==")

cloneUrl = baseUrl + '/api/billing/customers/clone'
print(f"POSTs for cloning the customer will be made to {cloneUrl}.")

@PropertyMeHttpRequestExceptionHandler(False)
def CloneUserRequest(requestSession: UserSession, data: dict):
    global cloneUrl
    return requestSession.Current.post(cloneUrl, data=data)

def CloneCustomer(newEmail: str, newPassword: str) -> dict:
    global adminEmail
    global adminPassword
    
    return {
        "Email": adminEmail,
        "Password": adminPassword,
        "NewEmail": newEmail,
        "NewPassword": newPassword,
        "IsForPortalTest": False
    }

pp = PrettyPrinter(indent=4)
cloneRes = CloneUserRequest(pmeHandler.Sessions[0], CloneCustomer(testEmail, testPassword))
pp.pprint(cloneRes.json())
memberId = cloneRes.json().get("MemberId") if cloneRes else 'NaN'
customerId = cloneRes.json().get("CustomerId") if cloneRes else 'NaN'
input("** Check the result! ** 'Enter' to continue...")
print("\n********************************************************************************")


# ## 6. Save to an ouput csv
# --------------------

# In[ ]:


# Save the output to a csv
print("********************************************************************************")
print("\n== SAVING CUSTOMER DATA ==")

data = {
    "CustomerId": [customerId],
    "Username": [testEmail],
    "Pw" : [testPassword], 
    "MessageTemplateId": [defaultMessageTemplateId], 
    "MemberId": [memberId],
    "ManagerId": [memberId], # This can be set as another user I believe - but this simple and explicit
}

print(csvPreamble)
print(csvExplanation.format(', '.join(data.keys())))

customers = pd.DataFrame(data=data)
NotebookHelper.Output(customers.sample(n=1))
customers.to_csv(fullFilename)

ConsoleHelpers.PreventImmediateConsoleClose("Saved! Check the results against the output and rerun if there are any issues.")
print("\n********************************************************************************")

