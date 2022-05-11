__author__ = "Albert Ferguson"

from .DataBuilder import DataBuilder


class DataGen():
    def __init__(self, builder: DataBuilder, start: int):
        """Generate the data of a given builder.

        Note: __next__ is internally called to iterate this generator.
            This allows next(**kwargs) to be used. The override with kwargs
            injects kwargs into child builders as needed.
        """

        self._i = start
        self._builder = builder
        
    def __iter__(self):
        return self
    
    def next(self, **kwargs):
        json = self._builder.BuildJson(str(self._i), **kwargs)
        self.__next__()
        return json

    def __next__(self):
        self._i += 1
