__all__ = ["StrParseColumns", "StrParseSetColumnValue"]


def StrParseColumns(columns: list[str], keyMode=False) -> list[str]:
    """Parse a list of column names to a list of valid column names.

    Args
    ----
    columns: list(str):
        list of string columns to parse.

    Kwargs
    ------
    keyMode: bool
        return valid columns but all column names are prefixed with the ':' char.
        This "keymode" allows a dictionary comprehension to unpack values from a dict
        to match the relavent column names - neatly.
    """

    _cols = _filterOnlyValidColumns(columns)
    
    if keyMode:
        _cols = [':' + e for e in _cols]

    return _cols

def StrParseSetColumnValue(columns: list[str], values: list[str]) -> str:
    """Parse a string list of columns and values and format as column=value.

    Args
    ----
    columns: list[str],
        A list of columns to set values to.

    values: list[str],
        A list of values to set to each column.
    
    Returns
    -------

    column=value pairs comma delimited.
    e.g.

    args: ["A", "B", "C"], [1, 2, 3] => "A=1, B=2, C=3"
    """

    if (len(columns) != len(values)):
        raise IndexError("Columns and Values must match indexes to encode!")
    

    _cols = _filterOnlyValidColumns(columns)

    pairs = list()

    for i in range(len(_cols)):
        col, val = _cols[i], values[i]
        pairs.append(f"{col}={val}")
    
    return ', '.join(pairs)

def _filterOnlyValidColumns(columns: list[str]) -> list[str]:
    if (len(columns) == 0):
        raise IndexError("Columns must contain at least 1 column to validate!")

    # remove None types
    _cols = list(filter(None, columns))
    # remove empty or space including column names
    _cols[:] = [e for e in columns if len(e.strip()) != 0]

    return _cols
