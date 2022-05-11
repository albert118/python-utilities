__author__ = "Albert Ferguson"

import json
from datetime import datetime

from .DataBuilder import DataBuilder


class LotBuilder(DataBuilder):
    """Lot Entity builder for a given customer and manager.
    
    Lots pertain to the following configuration:
        * Addresses are all constants. JSON is equiv. to the addressText field.
        * Lots have 0 rooms, spaces, area, etc.
        * Lots are not archived (default active state).
        * No active Ownership, RentalListing, Sale, Agreement, Tenancy, Rent are incl.
            * These are typically update post-hoc by adding the relavent entity to existing lots.
        * Updated and Created On meta fields are set to creation time (datetime.now)
        * Reference is unique to iter counter and prefixed by #ref -.
    """
    
    def __init__(self, customerID: str, managerID: str):
        self._managerID = managerID
        self._customerID = customerID

        self._addressText = "'13 Sydenham Rd Norwood SA 5067'"
        self._long = 138.6268871
        self._lat = -34.9168096
        self._aUnit = "'SquareMeters'"

        self._addressJSON_fmt = {
            "Unit": "",
            "Number": "13",
            "Street": "Sydenham Rd",
            "Suburb": "Norwood",
            "PostalCode": "5067",
            "State": "SA",
            "Country": "Australia",
            "BuildingName": "",
            "MailboxName": "",
            "Latitude": "-34.9168096",
            "Longitude": "138.6268871",
            "Text": "13 Sydenham RdNorwood SA 5067",
            "Reference": "Sydenham Rd, 13"
        }

    @property
    def CustomerID(self):
        return self._customerID
    
    def BuildJson(self, refId: str, **kwargs) -> str:
        return json.dumps({
            "Lot": {
                "ActiveManagerMemberId": self._managerID,
                "ActiveOwnershipId": "",
                "ActiveRentalListingId": "",
                "ActiveSaleAgreementId": "",
                "ActiveSaleListingId": "",
                "ActiveTenancyId": "",
                "AdRentAmount": "",
                "AdRentPeriod": "",
                "Address": self._addressJSON_fmt,
                "AddressText": self._addressText,
                "ArchivedOn": "",
                "Area": "",
                "AreaUnit": "SquareMetres",
                "Bathrooms": "0",
                "Bedrooms": "0",
                "CarSpaces": "0",
                "CreatedOn": str(datetime.now()),
                "CustomerId": self._customerID,
                "Description": "",
                "ExternalListingId": "",
                "Id": "00000000-0000-0000-0000-000000000000",
                "InitialInspectionFrequency": "null",
                "InitialInspectionFrequencyType": "weekly",
                "InspectionFrequency": "",
                "InspectionFrequencyType": "weekly",
                "IsArchived": "false",
                "IsRental": "false",
                "KeyNumber": "",
                "Labels": "",
                "LandArea": "",
                "LandAreaUnit": self._aUnit,
                "Latitude": self._lat,
                "Longitude": self._long,
                "MainPhotoDocumentId": "",
                "NextInspectionOn": "null",
                "Notes": "",
                "PrimaryType": "Residential",
                "PropertySubtype": "House",
                "Reference": f"ref# - {refId}",
                "RuralCategory": "",
                "StrataManagerContactId": "",
                "UpdatedOn": str(datetime.now())
            }
        })
