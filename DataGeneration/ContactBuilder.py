__author__ = "Albert Ferguson"

import json

from .DataBuilder import DataBuilder


class ContactBuilder(DataBuilder):
    """Contact Entity builder with 1 Primary Contact Persons.

    Contacts pertain to the following configuration:
        * Addresses are all constants.
        * Communication Preferences are set to "ByEmail" ("BySMS" is also an option).
        * 1 contact person passed and they are set to Primary.
        * Tenant role.
        * Not a Supplier.
        * Reference is unique to iter counter and prefixed by #ref -.
    """

    def __init__(self, customerID: str):
        self._customerID = customerID

        # same as postal and default address
        self._physicalAddr = {
            "BuildingName": "",
            "Country": "Australia",
            "Latitude": "-34.9168096",
            "Longitude": "138.6268871",
            "MailboxName": "",
            "Number": "13",
            "PostalCode": "5067",
            "Reference": "Sydenham Rd, 13",
            "State": "SA",
            "Street": "Sydenham Rd",
            "Suburb": "Norwood",
            "Text": "13 Sydenham RdNorwood SA 5067",
            "Unit": "",
            "mode": 0
        }

    @property
    def CustomerID(self):
        return self._customerID
    
    def BuildJson(self, refId: str, **kwargs) -> str:
        contactEmail = kwargs.get("contactEmail", "devtesting+aaloadtesting@propertyme.com")

        return json.dumps({
            "ContactPersons": [{
                "CellPhone": "",
                "CombinedPhones": "",
                "CommunicationPreferences": "ByEmail", # required to trigger Automation messages
                "CompanyName": "Load Tester Contact",
                "ContactId": "00000000-0000-0000-0000-000000000000",
                "CustomerId": self._customerID,
                "Email": contactEmail,
                "FirstName": "",
                "FullName": "",
                "HomePhone": "",
                "Id": "00000000-0000-0000-0000-000000000000",
                "IsPrimary": "true",
                "LastName": "",
                "NormalisedMobilePhone": "",
                "PhysicalAddress": self._physicalAddr,
                "PostalAddress": self._physicalAddr,
                "Salutation": "",
                "SecondaryEmailAddresses": "[]",
                "SortOrder": 0,
                "WorkPhone": "",
                "isDeleted": "false",
                "_emailChanged": "true" # also sent when setting CommunicationPreferences
            }],
            "DefaultAddress": self._physicalAddr,
            "IsSupplier": "false",
            "Reference": f'"ref#{refId} - load testing contact"',
            "Roles": "'[tenant]'",
            "SpecialType": "None",
            "Id": "00000000-0000-0000-0000-000000000000"
        })
