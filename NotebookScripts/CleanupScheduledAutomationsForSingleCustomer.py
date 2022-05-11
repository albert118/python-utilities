#!/usr/bin/env python
# coding: utf-8

# # Cleanup Scheduled Automations for Single Customer
# 
# Workflow:
# 1. Configure csv file names (1 for first customer, 1 for automation ids), base url and db connection string 
# 2. Read csv for customer login details (in first row)
# 3. Read csv for list of automation ids to remove schedules from
# 4. Authenticate with first customer
# 5. Make API request to remove schedules (by making them flexible)
# 7. Export data to csv for data that failed cleanup

# In[ ]:


import pandas as pd
from requests import Session

from Auth import UserSession
from CommonLib import ConsoleHelpers
from CommonLib.ResponseDecorators import PropertyMeHttpRequestExceptionHandler
from Config import ConfigureCsvFilename, ConfigurePropertyMeBaseUrl, ConfigureMySqlConnectionString
from Database import WriteDb


# In[ ]:


# Configure csv file name, base url and db connection string
divider = "\n********************************************************************************"

csvExplanation = '''
The first csv file will be read from to obtain the customer in first row for login and automation deletion.    
The second csv file will be read from for list of automation ids to remove schedules from.
    
    NOTE: This may be the csv file of "aa-load-test-inserted-automations-for-<customerId>.csv" generated from "InsertScheduledAutomationsForSingleCustomer.py"
    Alternatively, it can be the "aa-load-test-failed-cleanup-automations-for-<customerId>.csv" to re run the failed patches from a previous run of this script.
    
The automations which successfully had their ids removed will then also be deleted from the db
'''
print(csvExplanation)

customerFilenameDefault = 'aa-load-test-customer-data'
print('The following csv is for the CUSTOMER LOGIN')
customerFullFilename = ConfigureCsvFilename(customerFilenameDefault)

baseUrl = ConfigurePropertyMeBaseUrl()
patchAutomationEndpointUrl = baseUrl + '/api/automation/automations'

print('\nA db connection is required to update cloned customers to have an Uncharged Dataset type and "pro" member permissions for bypassing subscription and role checks.')
dbString = ConfigureMySqlConnectionString()

print(divider)


# In[ ]:


# Get details of first customer from csv
print("== READING FROM FIRST CSV FOR CUSTOMER ==")

customers = pd.read_csv(customerFullFilename)
firstCustomer = customers.iloc[0].to_dict()

firstCustomerId = firstCustomer['CustomerId']
loginEmail = firstCustomer['Username']
pw = firstCustomer['Pw']
messageTemplateId = firstCustomer['MessageTemplateId']

print(f'User to login as: {loginEmail}')
print(f'CustomerId : {firstCustomerId}')

print(divider)


# In[ ]:


# Configure filename for inserted automations
automationsFullFilenameDefault = f'aa-load-test-inserted-automations-for-{firstCustomerId}'
print('The following csv is for the AUTOMATION IDS')
automationsFullFilename = ConfigureCsvFilename(automationsFullFilenameDefault)
print(divider)


# In[ ]:


# Get details of first customer from csv
print("== READING FROM SECOND CSV FOR AUTOMATION IDS ==")

automationIds = pd.read_csv(automationsFullFilename)

print(automationIds)
print(divider)


# In[ ]:


# Authenticate that first customer
print('\nAUTHENTICATING:')
userSession = UserSession(loginEmail, pw, baseUrl, True, firstCustomerId)
print(userSession)
print(divider)


# In[ ]:


# Patch automations with a schedule via API requests
print('\nPATCHING EACH AUTOMATION WITH A SCHEDULE:')

patchAutomationData = {
    "Rules": [],
    "Schedule": {
        "DaysOfWeek": []
    }
}
failedCleanupAutomations = []
automationsToDelete = []

@PropertyMeHttpRequestExceptionHandler()
def PatchAutomationRequest(requestSession: Session, automationId: str, json: dict):
    global patchAutomationEndpointUrl
    return requestSession.patch(f'{patchAutomationEndpointUrl}/{automationId}', json=json)

def PatchAutomation(requestSession: Session, automationId: str) -> bool:
    patchResp = PatchAutomationRequest(requestSession, automationId, patchAutomationData)

    if patchResp is None:
        print(f'Unable to patch automation with id {automationId}')
        return False
        
    print(f'Automation patched for id {automationId}')
    return True

def PatchAuto(s: pd.Series):
    if s.ScheduleExists:
        succeeded = PatchAutomation(userSession.Current, s.AutomationId)
        
        if not succeeded:
            failedCleanupAutomations.append({
                "AutomationId": s.AutomationId,
                "ScheduleExists": True
            })
            return

    # Placed outside 'if' block to also add in automations which previously were inserted but failed with creating schedule
    automationsToDelete.append({
        "AutomationId": s.AutomationId,
        "ScheduleExists": False
    })


print(f"PATCH requests to be made to base url '{patchAutomationEndpointUrl}/<automationId>'")
print(f"Preparing to update automations with schedules for customer {loginEmail}...")

automationIds.apply(PatchAuto, axis=1)

print("\nPATCHING COMPLETED")
print(divider)


# In[ ]:


# Export to csv
if len(failedCleanupAutomations) == 0:
    print('\nNo patches failed. Nothing to export.')
else:
    failedAutomationsDf = pd.DataFrame(failedCleanupAutomations)
    failedAutomationsFullFilename = f'aa-load-test-failed-cleanup-automations-for-{firstCustomerId}.csv'
    failedAutomationsDf.to_csv(failedAutomationsFullFilename)
    print(f'\nExported failed automations to file {failedAutomationsFullFilename}')


# In[ ]:


ConsoleHelpers.PreventImmediateConsoleClose('Completed.')

