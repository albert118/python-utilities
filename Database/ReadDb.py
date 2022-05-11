from typing import Union

from pandas import DataFrame, read_sql

from .ContextBox import *
from .ParsingHelpers import *


@DatabaseConnection()
def GetTableData(dbString: str, table: str, index: Union[str, int] = 0) -> DataFrame:
    """Read data from a given table. Table must be accessable via the dbString given.
    
    Args
    ----
    dbString: str,
        A valid db connection string.
        e.g.

        ```
        dbString = ConfigureMySqlConnectionString()
        ```
    
    table: str,
        the table to update.
    
    Kwargs
    ------
    index: Union[str, int],
        Configure the index of the returned dataframe. A valid column name is required.
        Defaults to 0 and sets no index.
    
    Returns
    -------

    df: DataFrame(index=index),
        A dataframe representing the requrested table.
        Optionally, indexed by `index` (see kwarg opt).
    
    """

    _conn = GetConnection(dbString)
    sqlString = f"SELECT * FROM {table};"
    
    df = read_sql(sqlString, _conn, index_col=index)
    return df
