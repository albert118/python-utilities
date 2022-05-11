#!/usr/bin/env python
# coding: utf-8

# # Insert Scheduled Automations for Single Customer
# 
# Workflow:
# 1. Configure csv file name, base url, db connection string and automation rules
# 2. Read csv and use first customer
# 3. Authenticate with first customer. Do this before inserting into SQL to prevent updating db unnecessarily.
# 4. Insert automations via SQL
# 5. Make API request to create schedules
# 6. Export created data to csv for cleanup

# In[ ]:


import pandas as pd
from requests import Session
import uuid

from Auth import UserSession
from CommonLib import ConsoleHelpers
from CommonLib.ResponseDecorators import PropertyMeHttpRequestExceptionHandler
from Config import ConfigureCsvFilename, ConfigurePropertyMeBaseUrl, ConfigureMySqlConnectionString
from Database import WriteDb


# In[ ]:


# Configure csv file name, base url and db connection string
divider = "\n********************************************************************************"

print('A csv file will be read from. The customer in first row will be used to login and create automations for.')
filenameDefault = 'aa-load-test-customer-data'
fullFilename = ConfigureCsvFilename(filenameDefault)

baseUrl = ConfigurePropertyMeBaseUrl()
patchAutomationEndpointUrl = baseUrl + '/api/automation/automations'

print('\nA db connection is required to update cloned customers to have an Uncharged Dataset type and "pro" member permissions for bypassing subscription and role checks.')
dbString = ConfigureMySqlConnectionString()

print(divider)


# In[ ]:


# Setup automation rules and schedules
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


# In[ ]:


# Configure number of times to insert an automation
print('\nCONFIGURE NUMBER OF AUTOMATIONS TO INSERT:')
while True:
    numToInsertInput = input('\nEnter number of automations to insert (Entering no value defaults to 1): ')
    try:
        numToInsert = 1 if not numToInsertInput else int(numToInsertInput)
        if numToInsert < 1:
            print('Value must be at least 1')
            continue
        break
    except ValueError:
        print('Enter a proper integer')
        
print(f'Selected rows to insert: {numToInsert}')
print(divider)


# In[ ]:


# Get details of first customer from csv
print("== READING FROM CSV ==")
customers = pd.read_csv(fullFilename)
firstCustomer = customers.head(1)

firstCustomerId = firstCustomer['CustomerId'][0]
loginEmail = firstCustomer['Username'][0]
pw = firstCustomer['Pw'][0]
messageTemplateId = firstCustomer['MessageTemplateId'][0]

print(f'''
    User to login as: {loginEmail}
    MessageTemplateId for all automations: {messageTemplateId}
''')

print(divider)


# In[ ]:


# Authenticate that first customer
print('\nAUTHENTICATING:')
userSession = UserSession(loginEmail, pw, baseUrl, True, firstCustomerId)
print(userSession)
print(divider)


# In[ ]:


# create insert customerautomationtype sql statement
writeStatements = []
customerAutomationTypeStatement = f'''insert into customerautomationtype
    (Id, CustomerId, CreatedOn, Type, AreSchedulesPaused)
values
    (uuid(), "{firstCustomerId}", now(), "Arrears", 0)'''

writeStatements.append(customerAutomationTypeStatement)

print(f'initial insert statement: \n{customerAutomationTypeStatement}')


# In[ ]:


# Create insert automations sql statement
sqlStatement = '''
insert into automation 
    (Id, CustomerId, CreatedOn, Type, IsActive, Preconditions, Rules, Name, Status)
Values'''

def GetNewAutomationRowValues(id: str) -> str:
    return  f'\n\t("{id}", "{firstCustomerId}", now(), "Arrears", 1, "[]", "[]", "Load Test Automation", "NotProcessed")'


newIds = [str(uuid.uuid4()) for i in range(numToInsert)]
valueRows = [GetNewAutomationRowValues(newId) for newId in newIds]
sqlStatement += ', '.join(valueRows)
    
print(f'''NOTE: the rules will be added as part of API request to update with schedule

The final insert sql statement will be:
{sqlStatement}
''')
input('\nHit "Enter" to run this insert, otherwise close this program.')

writeStatements.append(sqlStatement)
print(divider)


# In[ ]:


# Insert automations for customer
WriteDb.ProcessStatements(dbString, writeStatements)


# In[ ]:


# Patch automations with a schedule via API requests
print('\nPATCHING EACH AUTOMATION WITH A SCHEDULE:')

attemptedPatchAutomations = []
    
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

@PropertyMeHttpRequestExceptionHandler()
def PatchAutomationRequest(requestSession: Session, automationId: str, json: dict):
    global patchAutomationEndpointUrl
    return requestSession.patch(f'{patchAutomationEndpointUrl}/{automationId}', json=json)

def PatchAutomation(requestSession: Session, automationId: str, templateId: str):
    patchAutomationData = {
        "Rules": ConstructRules(daysInArrears, templateId),
        "Schedule": {
            "DaysOfWeek": daysOfWeek,
            "MinutesIntoDays": minutesIntoDays
        }
    }
    
    patchResp = PatchAutomationRequest(requestSession, automationId, patchAutomationData)
    
    attemptedPatchAutomations.append({
        "AutomationId": automationId,
        "ScheduleExists": patchResp is not None
    })
    msgPrefix = 'FAILED patch' if patchResp is None else 'Automation patched'
    print(f'{msgPrefix} for ID: {automationId}')

def PatchAuto(s: pd.Series):
    PatchAutomation(userSession.Current, s.AutomationId, messageTemplateId)


print(f"PATCH requests to be made to base url '{patchAutomationEndpointUrl}/<automationId>'")
print(f"Preparing to update automations with schedules for customer {loginEmail}...")

newIdsDf = pd.DataFrame(newIds, columns=['AutomationId'])
newIdsDf.apply(PatchAuto, axis=1)

print(newIdsDf)

print(divider)


# In[ ]:


# Export to csv
attemptedPatchAutomationsDf = pd.DataFrame(attemptedPatchAutomations)
newIdsFullFilename = f'aa-load-test-inserted-automations-for-{firstCustomerId}.csv'
attemptedPatchAutomationsDf.to_csv(newIdsFullFilename)
print(f'\nExported new automation ids to file {newIdsFullFilename}')


# In[ ]:


ConsoleHelpers.PreventImmediateConsoleClose('Completed. Hit "Enter" immediately to close console.')

