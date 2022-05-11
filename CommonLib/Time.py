import time
from datetime import datetime
from functools import wraps


def FunctionExecutionTimer():
    def decorator(foo):
        """Surmise a function's execution timing."""
        
        @wraps(foo)
        def timerFuncWrapper(*args, **kwargs):
            timeStart = datetime.now()
            tic = time.perf_counter()
            response = foo(*args, **kwargs)
            toc = time.perf_counter()
            timeEnd = datetime.now()

            print("##########################################################")
            print(f"{foo.__name__} timed execution summary:")
            print(f"\tran for {toc - tic:0.4f} seconds.")
            print(f"\tStarted at {timeStart} and ended at {timeEnd}.")
            print("##########################################################")

            return response

        return timerFuncWrapper
    return decorator
