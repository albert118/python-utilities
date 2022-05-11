__all__ = ["DatabaseConnection", "GetConnection"]

from functools import wraps
import traceback

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection, url

# privately handled fields. Do not access directly! Use _getConnection()
__dbConnection = None
__engine = None

def DatabaseConnection(pauseOnException=True, returnValueOnException=None, fullTrace=False):
    def decorator(dbAccessor):
        """Catch common session configuration errors."""
        @wraps(dbAccessor)
        def dbAccessorWrapper(*args, **kwargs):
            global __dbConnection
            global __engine

            try:
                return dbAccessor(*args, **kwargs)
            except Exception as ex:
                print(f"An Exception has occured: {ex}")
                
                if fullTrace:
                    traceback.print_exc()
                
                if pauseOnException:
                    input('Hit "Enter" to proceed or close window.')
                return returnValueOnException
            finally:
                # if pooling is enabled, the connection must be invalidated to drop it.
                __dbConnection.invalidate()
                __dbConnection.close()
                __dbConnection = None

                __engine.dispose()
                __engine = None

                print("\n********************************************************************************")
                print("== CLOSED DB CONNECTION ==")
                print("********************************************************************************\n")

        return dbAccessorWrapper
    return decorator

def GetConnection(dbString: str) -> Connection:
    """Get and, if not already existing, Configure an engine.

    Note: Any call that utilises this engine should wrap its enclosing
        function with a `DatabaseConnection()` decorator to correctly dispose
        the connection and handle errors.

        This also allows configuring the error pausing behaviour, as well as
        the return type (default `None`) on errors.

    Args
    ----
    dbString: str,
        A valid db connection string.
        e.g.

        ```
        dbString = ConfigureMySqlConnectionString()
        ```    

    Returns
    -------
    dbConnection: Connection,
        A validated and active dbConnection.
    
    """

    global __dbConnection
    global __engine

    if (not __engine or not __dbConnection):
        __engine = create_engine(url.make_url(dbString), pool_recycle=-1, echo=True, logging_name='myengine', poolclass=pool.NullPool)
        __dbConnection = __engine.connect()

    return __dbConnection
