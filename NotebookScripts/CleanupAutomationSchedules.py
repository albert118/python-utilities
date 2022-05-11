#!/usr/bin/env python
# coding: utf-8

# # Cleanup Automation Schedules (Arrears)
# 
# ## Prerequisites:
# --------------------
# * CSV file with columns CustomerId, Username and Password. 
# * Each customer within the csv file to be read is expected to have an automation of type 'Arrears'. 
# * Using the same csv file used for creating automations is expected.
# 
# ## Workflow:
# --------------------
# 
# 1. Set constants;
#    * This includes setup of the default filenames and endpoints.
# 2. Read from csv file and load customer data into memory;
# 3. Configure api request base data;
#    * Authenticate all users.
#    * Make requests to existing endpoints and obtain automations per customer, before extracting the Automation ID.
# 4. Make a subsequent request to update the automation to be flexible (schedule removed).
# 
# **NOTE: This only removes schedules, the automations will still exist!**

# In[ ]:


import pandas as pd
from requests import Session

from Auth import UserSessionsHandler
from CommonLib import NotebookHelper, ConsoleHelpers
from CommonLib.ListHelpers import FilterList
from CommonLib.ResponseDecorators import PropertyMeHttpRequestExceptionHandler
from Config import ConfigureCsvFilename, ConfigureUrl, ConfigurePropertyMeBaseUrl


# ## 1. Set Constants
# --------------------

# In[ ]:


divider = "********************************************************************************"
fullFilenameDefault = 'aa-load-test-customer-data'
fullFilename = None
dbString = None
failedCsvFilename = "aa-load-test-cleanups-failed.csv"

customers = pd.DataFrame()

baseUrl = ConfigurePropertyMeBaseUrl()


# ## 2. Read CSV Load Customer Data
# --------------------

# In[ ]:


# Retrieve the load testing customer data
print(divider)
print('\nLOADING CUSTOMER DATA FROM CSV:')

csvExplanation = """
    The csv will require columns titled: CustomerId, Username, Pw, MessageTemplateId
    If these values are missing, then subsequent operations may fail unexpectedly.
    """

print("== CONFIGURING CSV ==")
print(csvExplanation)

if not fullFilename:
    fullFilename = ConfigureCsvFilename(fullFilenameDefault)

# Read from csv (expecting 4 columns)
print('\nREADING FROM CSV:')
customers = pd.read_csv(fullFilename)

# Add the new AutomationId column if it wasn't already there
if "AutomationId" not in customers.columns:
    customers["AutomationId"] = ""

print('\nCustomer rows from file (customerId, username, messageTemplateId, memberId, managerId) (Password not shown):')
NotebookHelper.Output(customers.drop(["Pw"], axis=1).head())

input("Ensure this data is correct. Then hit Enter to continue")
print(divider)


# ## 3. Configure API Requests - Authentication
# --------------------

# In[ ]:


# Configure the load testing 'customer' authentication sessions.
print(divider)
print('\nAUTHENTICATING AND OBTAINING SESSION DATA FOR EACH CUSTOMER:')

def MakeSession(s: pd.Series, handler: UserSessionsHandler):
    """Functional approach is a neat way to easily auth users in a dataframe."""
    return handler.AddUserSession(s.Username, s.Pw, customerId=s.CustomerId)

pmeHandler = UserSessionsHandler(baseUrl)
customers.apply(lambda c: MakeSession(c, pmeHandler), axis=1)
pmeHandler.AuthenticateSessions()

print('\n\n**CHECK CUSTOMER DATA IS ALL EXPECTED**')
print(f"{len(pmeHandler.Sessions)} sessions were created.")
print(f"Session summary:\t{pmeHandler.Sessions[:5]}")
endSectionMessage = "To re-execute the script and start again, close the program."
ConsoleHelpers.PreventImmediateConsoleClose(endSectionMessage)

print(divider)


# ## 3. Configure API Requests - Automation ID Retrieval
# --------------------

# In[ ]:


# Get the arrears automation id for each customer
print(divider)
print('\nQUERYING FOR ARREARS AUTOMATIONS AND OBTAINING CREATED IDs:')

queryAutomationUrl = baseUrl + '/api/automation/automations?Type=Arrears'

# If the auto schedules were already reset by exterior SQL scripts, then this will error out
# and become blocking to the reset process.
@PropertyMeHttpRequestExceptionHandler(False)
def GetAutomationRequest(requestSession: Session):
    return requestSession.get(queryAutomationUrl)

# Returns None if no arrears automation found, otherwise a dictionary of key values for the automation
def GetAutomation(requestSession: Session):
    response = GetAutomationRequest(requestSession)
    if response is None:
        return None
    
    arrearsAutomation = FilterList(response.json(), lambda a: a.get("Type") == "Arrears")
    return arrearsAutomation

print(f'GET requests to be made to {queryAutomationUrl}')

# functional approach is a neat way to easily auth users in a dataframe
def GetAutomations(s: pd.Series):
    global pmeHandler # must be setup earlier in the script
    session = pmeHandler.GetCustomerUserSession(s.CustomerId)
    automation = GetAutomation(session.Current) 
    
    if not automation:
        print(f"No automation was found for {s.Username}")
        return
    
    try:
        s.AutomationId = automation.get("Id")
    except AttributeError as ex:
        print(f"\nAn error occurred. No AutomationId was retrieved.\n\tError: {ex}")
    return

# previous steps may include AutomationId for us already! only GET WHERE AutomationId IS NaN
noAutoIds = customers[customers.AutomationId.isnull()].set_index("CustomerId")
if noAutoIds.shape[0] > 0:
    # even though a prev step probably failed to retrieve an auto id,
    # double check to clear as much data as possible
    noAutoIds.apply(GetAutomations, axis=1)
    # adjust any NaN values we can
    customers = customers.combine_first(noAutoIds)

# valid Automations are not empty so reindex for display purposes
validSlice = customers[customers.AutomationId != '']

print("\nSUMMARY OF OBTAINED AUTOMATIONS (Username, AutomationId): ")
NotebookHelper.Output(f"{validSlice.shape[0]} valid automations obtained.")
NotebookHelper.Output(validSlice[["CustomerId", "AutomationId"]].head())

endSectionMessage = "Continue Patching the Automation (Removing schedules). "
ConsoleHelpers.PreventImmediateConsoleClose(endSectionMessage)

print(f'\n{divider}')


# ## 4. Remove Automation Schedules (Make Flexible)
# --------------------

# In[ ]:


# Patch automations to remove schedule
print(divider)
print('\nPATCHING EACH AUTOMATION TO REMOVE SCHEDULE:')

patchAutomationEndpointUrl = baseUrl + '/api/automation/automations'
patchAutomationData = {
    "Rules": [],
    "Schedule": {
        "DaysOfWeek": []
    }
}
failedCleanups = []

@PropertyMeHttpRequestExceptionHandler(True)
def PatchAutomationRequest(requestSession: Session, automationId: str, json: dict):
    return requestSession.patch(f'{patchAutomationEndpointUrl}/{automationId}', json=json)

def PatchAutomation(requestSession: Session, automationId: str) -> bool:
    patchResp = PatchAutomationRequest(requestSession, automationId, patchAutomationData)

    if patchResp is None:
        print(f'Unable to patch automation with id {automationId}')
        return False
        
    print(f'Automation patched for id {automationId}')
    return True


# functional approach is a neat way to easily auth users in a dataframe
def PatchSessions(s: pd.Series, handler: UserSessionsHandler):
    session = handler.GetCustomerUserSession(s.CustomerId)
    succeeded = PatchAutomation(session.Current, s.AutomationId)
    
    if not succeeded:
        failedCleanups.append(s.to_dict())

print(f'PATCH requests to be made to url "{patchAutomationEndpointUrl}/<automationId>"\n')
customers.apply(lambda c: PatchSessions(c, pmeHandler), axis=1)

# Export failed csv to new csv file
if len(failedCleanups) > 0:
    failedCleanupsDf = pd.DataFrame(failedCleanups)
    failedCleanupsDf.to_csv(failedCsvFilename)
    print(f'\nUNSUCCESSFUL cleanups have been saved to a new csv file named "{failedCsvFilename}"')
else:
    print('\nAll automations successfully cleaned up')

print(f'\n{divider}')


# In[ ]:


#Prevent immediate closing of console on completion for user to be able to continue looking at the logs
closingMessage = "\n\nNOTE: ***THE AUTOMATIONS STILL EXIST***. Only the schedules have been removed."
ConsoleHelpers.PreventImmediateConsoleClose(closingMessage)

