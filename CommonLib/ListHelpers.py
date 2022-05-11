def FilterList(iterable, predicate):
    """
    Similar to Array.find() in js. Returns None if no result found
    
    Parameters
    ----------
    iterable: list
        A list for the predicate to act on
    predicate: lambda
        To help filter the list. Example --> lambda a: a.get("Type") == "Arrears"
    """
    return next(filter(predicate, iterable), None)
