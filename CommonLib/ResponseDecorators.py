import json
from functools import wraps
from pprint import PrettyPrinter

from requests.exceptions import ConnectionError, SSLError


def PropertyMeHttpRequestExceptionHandler(pauseOnException=False, returnValueOnException=None):
    def decorator(httpRequestFunc):
        """Catch common session configuration errors."""
        @wraps(httpRequestFunc)
        def httpRequestFuncWrapper(*args, **kwargs):
            isException = False
            
            try:
                response = httpRequestFunc(*args, **kwargs)
                
                if not response.ok:
                    print(f'Request was not successful')
                    #if response.status_code == 403:
                        #authAndPermMessage = """User not authenticated (or setup) in PME for accessed endpoint. Are you sure this use has the correct permisssions set?"""
                        # for lack of a custom error type
                        #raise ConnectionError(authAndPermMessage)
                    raise Exception(response.text)
                return response
            except ConnectionError as connexError:
                print("Connection Error, is PropertyMe running?")
                _errorPrinter(connexError)
                isException = True
            except SSLError:
                print("SSL Error, PropertyMe on localhost doesnt support HTTPS. Check the baseaddress.")
                isException = True
            except Exception as error:
                _errorPrinter(error)
                isException = True
            finally:
                # double nesting avoids accidentally returning returnValueOnException
                # when no exception occurs. This would override the desired return of response.
                if isException:
                    if pauseOnException:
                        input('Hit "Enter" to proceed or close window.')
                    return returnValueOnException

        return httpRequestFuncWrapper
    return decorator

def _errorPrinter(error):
    print(f'Error occurred: \n')
    errorStr = str(error)
    
    if errorStr is None:
        print(error)
    else:
        try:
            ed = json.loads(errorStr)
            pp = PrettyPrinter(indent=4)
            pp.pprint(ed)
        except json.JSONDecodeError as jerror:
            print(error)