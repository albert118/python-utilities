__author__ = "Albert Ferguson"

import json
from datetime import datetime

from dateutil.relativedelta import relativedelta

from .DataBuilder import DataBuilder


class TenancyBuilder(DataBuilder):
    """Tenancy Entity builder for a given customer. 

    The following kwargs MUST be passed to init correct linkages:

    Kwargs
    ------
    
    contactID: str, guid-like
        Contact entity PK to link.

    lotID: str, guid-like
        Lot entity PK to link.

    daysInArrears: int
        Integer number of days to be in arrears by.
        Default is 0. 
        daysInArrears internally defaults to 1 but this is an offset to result in 0
        based on the calculations of TenancyStart and TenancyEnd dates.
    
    Tenancies pertain to the following configuration:
        * Rent always defaults to 1337.420.
        * Bond is 4 * rent
        * Tenancy term is always in months and set to 12 (this could be made a kwarg).
        * TenancyStart and CreatedOn meta fields are set to creation time (datetime.now)
        * AgreementEnd is set to the moveInDate + tenancyTerm/12 years.
        * TenancyEnd is set to the agreementEnd - 2 days (tenancy ends before move out).
        * Rentpaid field is init to $1. This creates a rent ledger and allows arrears to work as expected.
        * Reference is UUID on insert, this entity is dependent on Lot and Contact.
            * Deleting the relavent lots and contacts will cascade and remove this tenancy.
            * If the testing dataset becomes corrupted, use the rent/bond amount as a common (weak) lookup
    """

    def __init__(self, customerID: str):
        self._customerID = customerID

    @property
    def CustomerID(self):
        return self._customerID
    
    def BuildJson(self, refId: str, **kwargs) -> str:
        contactID =  kwargs.get("contactID", "00000000-0000-0000-0000-000000000000")
        lotID = kwargs.get("lotID", "00000000-0000-0000-0000-000000000000")
        
        # default to 1, this does not reflec the UI number!
        daysInArrears = kwargs.get("daysInArrears", 1)
        
        # Easy way to erase tenancies if you forget the IDs is to lookup by the unique rent.
        # Costs must be assigned to appear within arrears!
        rent = 1337.420 
        bond = rent * 4

        #  TODO: length of tenancy in months - this could be made a kwarg.
        tenancyTerm = 12
        #  TODO: move in Today by default - this could be made a kwarg.
        moveInDate = datetime.now()

        agreementEnd = moveInDate + relativedelta(years=(tenancyTerm/12))
        tenancyEnd = agreementEnd + relativedelta(days=-2)
        
        # This calculates the number as seen in the UI.
        _daysInArrears = moveInDate + relativedelta(days=(daysInArrears - 1))

        return json.dumps({  
            "ContactPersons": "[]",
            "IsClientAccessDisabled": "false",
            "NewContact": "null",
            "Tenancy": {
                "AgreementEnd": str(agreementEnd),
                "AgreementStart":  str(moveInDate),
                "AllowMepayPayments": "false",
                "BankReference": "",
                "BondAmount": str(bond),
                "BondInTrust": "0",
                "BondReference": "",
                "ContactId": contactID,
                "CreatedOn": str(moveInDate),
                "CustomerId": "00000000-0000-0000-0000-000000000000", # Setting this upfront may cause errors when inserting a new tenancy. Let this value be populated in the application
                "DirectDebit": "false",
                "DirectDebitFixedAmount": "",
                "DirectDebitFrequency": "RentDue",
                "EffectivePaidTo": "",
                "ExcludeArrearsAutomation": "false",
                "GenerateRentInvoice": "false",
                "Id": "00000000-0000-0000-0000-000000000000",
                "LastReviewedOn": "",
                "LotId": lotID,
                "MepayStatus": "Disabled",
                "NextDirectDebitDate": "",
                "NextIncreaseAmount": "",
                "NextIncreaseDate": "",
                "NextReviewDate": str(agreementEnd),
                "OpenBondReceived": "0",
                "PaidTo": str(_daysInArrears),
                "PartPaid": "1.00", # a min value must be set to populate the RentLedger on generation
                "ProrataTo": "null",
                "ReceiptWarning": "",
                "RentAmount": str(rent),
                "RentInvoiceDaysInAdvance": "0",
                "RentPeriod": "weekly",
                "RentSequence": "0",
                "ReviewFrequency": str(tenancyTerm),
                "TaxOnRent": "false",
                "TenancyEnd": str(tenancyEnd),
                "TenancyStart": str(datetime.now()),
                "UpdatedOn": str(datetime.now()),
            }
        })
