#!/usr/bin/env python
# coding: utf-8

# # Create Scheduled Automations (Arrears)
# 
# ## Caveats:
# Using the SQL option (as would be expected on first time setup), the user cannot construct a valid CSV. This will create a CSV copy of a given table (name) - not what is needed! Ideally this should construct a table with the (valid) columns:
#   
#     CustomerId,Username,Pw,MessageTemplateId,AutomationId
# 
# Currently, it is preferred to input as CSV (choose 'n' on step 2.) and have a pre-valdiated Message Template ID, CustomerIDs, etc...
# 
# ## Prerequisites:
# --------------------
# 
# For the sake of simplicity and faster development, each customer: 
# *  **SHOULD NOT HAVE AN EXISTING AUTOMATION YET**.
#    * Otherwise an automation will be inserted but the updating of the automation with a schedule may not occur for the one created.
# * have access to a valid messageschedule (template in UI) **or** access to a messagescheduledefault (these work for all customers).
#    * This is set in the CSV data read-in (or SQL).
# 
# ## Workflow:
# --------------------
# 1. Set Constants;
# 2. Ask whether to read from db;
#    * (yes) Input csv file name to export data to and eventually also read from;
#      * Add db credentials and server path;
#      * Export read data to a csv file.
#    * (no)  Input csv file name read from (previously exported to from other scripts).
#      * Read from csv file and load customer data into memory.
# 3. Configure API Requests;
#    * Authenticate customers.
# 4. Configure Automation Rules & Schedule;
# 
# **Note:** (*Steps 5, 6, and 7* done separately as the current arrears automation UI process does these separately and there is currently no endpoint that inserts with schedule. Inserting also does not return an id).
# 
# 5. Insert automations per Customer session;
# 6. Query Automations per customer and obtain their Automation ID for the first Arrears Automation found;
# 7. Update all Automations with a Schedule (configured in step 4).
# 
# ~~**Note: Current caveat --> the same message template is being used for all rules.**~~
# 
# **Note: A default message template is assigned to all Automations.** This should be fine, as the `messsagescheduledefault` schema is not customerContext bound.
# 

# In[ ]:


import pandas as pd
from requests import Session
from tqdm.auto import tqdm

from Auth import UserSessionsHandler
from CommonLib import NotebookHelper, ConsoleHelpers
from CommonLib.ListHelpers import FilterList
from CommonLib.ResponseDecorators import PropertyMeHttpRequestExceptionHandler
from Config import (ConfigureCsvFilename, ConfigurePropertyMeBaseUrl,
                    ConfigureUrl, ConfigureMySqlConnectionString,
                    ConfigureDbTableName)
from Database import *


# ## 1. Set Constants
# --------------------

# In[ ]:


baseUrl = ConfigurePropertyMeBaseUrl()
queryAutomationUrl = baseUrl + '/api/automation/automations?Type=Arrears'
createAutomationUrl = baseUrl + '/api/automation/automations'
patchAutomationEndpointUrl = baseUrl + '/api/automation/automations'

divider = "********************************************************************************"
createAutomationData = { "Type": "Arrears", "Name": "Load Test Automation", "IsActive": True }

fullFilenameDefault = 'single-aa-load-test-customer-data'
fullFilename = None
dbString = None

# MemberId isnt needed in this workflow, but keeping it here to not overwrite old data
customers = pd.DataFrame()


# ## 2. Set Datasource
# --------------------

# In[ ]:


# Retrieve the load testing customer data
print(divider)

csvExplanation = """
    The csv will require columns titled: CustomerId, Username, Pw, MessageTemplateId
    If these values are missing, then subsequent operations may fail unexpectedly.
    """
print("\n== CONFIGURING CSV ==")
print(csvExplanation)

fullFilename = ConfigureCsvFilename(fullFilenameDefault)

# Read from csv (expecting 4 columns)
print('\nREADING FROM CSV TO LOAD CUSTOMER DATA:')
customers = pd.read_csv(fullFilename)
print('\nCustomer rows from file (customerId, username, messageTemplateId, memberId, managerId) (Password not shown):')
NotebookHelper.Output(customers.drop(["Pw"], axis=1).head())

print(divider)


# ## 3. Configure API Requests
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


# ## 4. Configure Automation Rules & Schedule
# ------------------

# In[ ]:


# Setup automation rules and schedules
print(divider)
print('\nCONFIGURE AUTOMATION RULES AND SCHEDULES:')

# Setup weekdays for schedule to occur
while True:
    useAllWeekdays = input('Do you want to default to all business days of week in the schedule (Monday - Friday)? (Type "y" or "n"): ')
    if (useAllWeekdays == 'y' or useAllWeekdays == 'n'):
        break

daysOfWeek = []
    
if (useAllWeekdays == 'n'):
    listOfDays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    print('Accepted days: "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"')
    
    while True:
        print(f'Current selected days of week {daysOfWeek}')
        dayEntered = input('Type in a day or hit "Enter" immediately to proceed with selected days of week. (Finishing with empty list defaults to all business days): ')
        
        if not dayEntered:
            break 
        
        if dayEntered in listOfDays and dayEntered not in daysOfWeek:
            daysOfWeek.append(dayEntered)
        

if len(daysOfWeek) == 0:
    daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

print(f'\nSelected days of week: {daysOfWeek}.\n')

# Setup the time for schedule to occur on each selected day
print('Minutes into the days reference: 540 = 9am, 600 = 10am, 660 = 11am, 720 = 12pm, 780 = 1pm, 840 = 2pm, 900 = 3pm, 960 = 4pm, 1020 = 5pm.')
while True:
    minutesInput = input('Enter the minutes into the day for each automation to be scheduled at: ')
    try:
        minutesIntoDays = int(minutesInput)
        if (minutesIntoDays >= 0 and minutesIntoDays < 1440):
            break 
    except ValueError:
        print(f'{minutesInput} is not a valid value.')
    print(f'Please enter an integer from 0 - 1439.')
        
print(f'\nSelected minutes into days: {minutesIntoDays}.\n')
    
# Setup days in arrears for rent (one condition per rule)
print('By default all automations will be updated with rules for 3, 5 and 7 days in rent arrears and all with the same messageTemplateId for that customer (as read from csv file).')
while True:
    useDefaultRules = input('Do you want to use the default? (Type "y" or hit "Enter" immediately to use defaults. Enter "n" to define your own days): ')
    if not useDefaultRules or useDefaultRules == 'y' or useDefaultRules == 'n':
        break 
        
daysInArrears = []

if (useDefaultRules == 'n'):
    while True:
        print(f'Current days in arrears {daysInArrears}')
        daysInArrearsInput = input('Type in a number or hit "Enter" immediately to proceed with selected days in arrears values. (Empty list reverts to using default values): ')
        
        if not daysInArrearsInput:
            break 
            
        try:
            daysInArrearsInt = int(daysInArrearsInput)
            if daysInArrearsInt not in daysInArrears:
                daysInArrears.append(daysInArrearsInt)
        except ValueError:
            print(f'{daysInArrearsInput} is not a valid integer value')
    
if len(daysInArrears) == 0:
    daysInArrears = [3, 5, 7]
else:
    daysInArrears = sorted(daysInArrears)

scheduleSummary = f"""SELECTED VALUES:
    Days of week: {daysOfWeek}
    Minutes into days: {minutesIntoDays}
    Days in arrears: {daysInArrears}
    """.format(daysOfWeek, minutesIntoDays, daysInArrears)

print('\n**CHECK VALUES ARE EXPECTED**')
print(scheduleSummary)
input('Hit "Enter" to continue to authenticating each customer. To re-execute the script and start again, close the program.') 
print(divider)


# ## 5. Insert automations per Customer session
# -----------------

# In[ ]:


# Create automations for each customer
print(divider)
print('\nCREATING AUTOMATIONS FOR EACH CUSTOMER:')

@PropertyMeHttpRequestExceptionHandler(True)
def CreateAutomation(requestSession: Session):
    global createAutomationUrl
    global createAutomationData
    return requestSession.post(createAutomationUrl, data=createAutomationData)

print(f"\tPOST requests to be made to {createAutomationUrl}.")

for session in pmeHandler.Sessions:
    print(f"Preparing to create automation for {session.Username}")
    CreateAutomation(session.Current)
    
print('\nAutomation creation completed. If no error messages have been printed, then they have all been successful created')
print("********************************************************************************")


# ## 6. Query Automations per customer and obtain their Automation ID for the first Arrears Automation found
# ----------------------------

# In[ ]:


# Get the automation id(s) (since endpoint that creates an automation does not return id)
# At this point, it's convenient to track CustomerId - AutomationId pairs. So customerCsvData
# includes a new "AutomationId" column at this point.

print(divider)
print('\nQUERYING FOR ARREARS AUTOMATIONS AND OBTAINING CREATED IDs:')
print(f'GET requests to be made to {queryAutomationUrl}.')

ids_automationToCustomer = { "CustomerId": [], "AutomationId": [] }

@PropertyMeHttpRequestExceptionHandler(True)
def GetAutomationRequest(requestSession: Session):
    global queryAutomationUrl
    return requestSession.get(queryAutomationUrl)

def GetAutomation(requestSession: Session):
    """Get the Automation for the current session.
    
    Returns None if no arrears automation found, otherwise a dictionary of key values for the automation
    """
    
    response = GetAutomationRequest(requestSession)
    if response is None:
        return None
    
    arrearsAutomation = FilterList(response.json(), lambda a: a.get("Type") == "Arrears")
    return arrearsAutomation

# let the user retry if failures occur
isRetry = True
while isRetry:
    for session in tqdm(pmeHandler.Sessions):
        automation = GetAutomation(session.Current)    

        if automation is None:
            print(f"No automation was found for '{session.Username}'")
            continue

        autoId = automation.get("Id")

        print(session.CustomerId)
        ids_automationToCustomer["CustomerId"].append(session.CustomerId)
        ids_automationToCustomer["AutomationId"].append(autoId)
        print(ids_automationToCustomer)


    # later we may restart - all other reads of this csv data expect
    # an iloc index not a label!
    df_automationToCustomer = pd.DataFrame(data=ids_automationToCustomer)
    if (df_automationToCustomer.shape[0] > 0):
        # This is the only column we care to affect in this join
        # this is a hack but join gotta go fast
        if "AutomationId" in customers.columns:
            customers.drop(["AutomationId"], axis=1, inplace=True)
        
        tempData = customers.copy(deep=True)
        tempData = tempData.set_index("CustomerId").join(df_automationToCustomer.set_index("CustomerId"))
    
        print("Saved updated Customers data to CSV (includes AutomationIds)")
        print('\nALL OBTAINED AUTOMATIONS:')
        NotebookHelper.Output(tempData[["AutomationId"]].head())
        
        isRetry = input("Save changes and proceed? 'n' to retry.").lower().strip() == 'n'
        # persist changes
        tempData.to_csv(fullFilename)
        customers = tempData
    else:
        print("No Automations were obtained, no data will be saved.")
        input("'Enter' to continue, or close the window and retry the script.")
        isRetry = False
print(divider)


# ## 7. Update all Automations with a Schedule (configured in step 4)
# ----------------

# In[ ]:


# Patch automations with a schedule
print(divider)
print('\nPATCHING EACH AUTOMATION WITH A SCHEDULE:')
    
def ConstructCondition(daysInArrears: int):
    return {
        "Type": "TenantArrears", 
        "ArrearsType": "rent", 
        "DaysInArrears": daysInArrears
    }

def ConstructAction(templateId: str):
    return {
        "Type": "SendTemplateMessage",
        "MessageTemplateId": templateId
    }

def ConstructRule(daysInArrears: int, templateId: str):
    return {
        "Conditions": [ConstructCondition(daysInArrears)],
        "Actions": [ConstructAction(templateId)]
    }

def ConstructRules(daysInArrearsList: list, templateId: str):
    rules = [] 
    for daysInArrearsNum in daysInArrearsList:
        rules.append(ConstructRule(daysInArrearsNum, templateId))
    return rules 

@PropertyMeHttpRequestExceptionHandler(True)
def PatchAutomationRequest(requestSession: Session, automationId: str, json: dict):
    global patchAutomationEndpointUrl
    return requestSession.patch(f'{patchAutomationEndpointUrl}/{automationId}', json=json)

def PatchAutomation(requestSession: Session, automationId: str, templateId: str):
    patchAutomationData = {
        "Name": "Load test Automation",
        "Rules": ConstructRules(daysInArrears, templateId),
        "Schedule": {
            "DaysOfWeek": daysOfWeek,
            "MinutesIntoDays": minutesIntoDays
        }
    }
    
    patchResp = PatchAutomationRequest(requestSession, automationId, patchAutomationData)
    
    if patchResp is not None:
        print(f"Automation PATCH for ID: '{automationId}'")
        
# functional approach is a neat way to easily propogate PATCHs for users in a dataframe
def PatchAuto(s: pd.Series):
    global pmeHandler
    session = pmeHandler.GetCustomerUserSession(s.name).Current
    PatchAutomation(session, s.AutomationId, s.MessageTemplateId)
    return

print(f"PATCH requests to be made to base url '{patchAutomationEndpointUrl}/<automationId>'")
print(f"Preparing to update automations with schedules for {customers.shape[0]} customers...")
customers.apply(PatchAuto, axis=1)
print(divider)


# In[ ]:


ConsoleHelpers.PreventImmediateConsoleClose('Completed. Hit "Enter" immediately to close console.')

