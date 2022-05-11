from sqlalchemy import text
from tqdm.auto import tqdm

from .ContextBox import *
from .ParsingHelpers import *


@DatabaseConnection()
def ProcessStatements(dbString: str, statements: list[str]) -> None:
    """A generic db write helper that uses one db connection to make an SQL statement per list item. 
    
    Args
    ----
    dbString: str,
        A valid db connection string. e.g. mysql+pymysql://myusername:mypassword@127.0.0.1:3306/databasename
    
    data: list,
        A list of SQL statements to run
    """

    _conn = GetConnection(dbString)
    
    rowsAffected = 0

    # tqdm will update the user of progress.
    for statement in tqdm(statements):
        print(f'\nRunning a statement:\n')
        resProxy = _conn.execute(statement)
        rowsAffected += resProxy.rowcount if resProxy else 0
        
    print(f"{rowsAffected} WERE AFFECTED.")

@DatabaseConnection()
def UpdateTableDataForCustomers(dbString: str, table: str, data: dict[dict]) -> None:
    """Clever UPDATE helper. Parses data dictionaries to generate and execute db table updates.
    
    Note: this could easily be adjusted to utilise a single UPDATE with a WHERE IN (*ids) clause.
        However, this leaves the option to adjust the values of each customer individually.
    
    Args
    ----
    dbString: str,
        A valid db connection string. e.g. mysql+pymysql://myusername:mypassword@127.0.0.1:3306/databasename
    
    table: str,
        the table to update.
    
    data: dict[dict]:
        A dictionary of dictionaries that considers each value a "line". 
        * Each "line" is keyed by the CustomerId it affects.
        * Every "line" is a new UPDATE statement.
        * The value dictionary is column-values pairs dict.
        * Every UPDATE appends a WHERE clause with data's customerId key.
    
    """

    _conn = GetConnection(dbString)

    _table = table.lower().strip()
    rowsAffected = 0

    # tqdm will update the user of progress.
    for customerData in tqdm(data):
        line = data[customerData]

        customer = customerData.lower().strip()
        columns = list(line.keys())
        
        setValues = StrParseSetColumnValue(StrParseColumns(columns), StrParseColumns(columns, True))
        statement = GetUpdateStatement(_table, setValues, f"CustomerId='{customer}'")
        
        resProxy = _conn.execute(statement, **line)
        rowsAffected += resProxy.rowcount if resProxy else 0
        
    print(f"{rowsAffected} WERE AFFECTED.")

def GetUpdateStatement(updatePredicate: str, setPredicate: str, wherePredicate: str) -> str:
    return text(f"""
        UPDATE {updatePredicate} 
        SET {setPredicate}
        WHERE {wherePredicate}
    """)