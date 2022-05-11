__author__ = "Albert Ferguson"

import abc


class DataBuilder(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass) -> bool:
        return(hasattr(subclass, "CustomerID")
        and callable(subclass.CustomerID)
        or NotImplemented)

    @abc.abstractclassmethod
    def __init__(self, customerID: str):
        raise NotImplementedError

    @abc.abstractproperty
    def CustomerID(self) -> str:
        """
        Get the builders configured CustomerID.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def BuildJson(self, refId: str, **kwargs) -> str:
        """
        Build the data into a dictionary.
        """

        raise NotImplementedError
