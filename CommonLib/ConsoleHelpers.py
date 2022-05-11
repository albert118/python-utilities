def PreventImmediateConsoleClose(closingMsg: str = ''):
    print('\n\n' + closingMsg)
    while True:
        endingInput = input('Hit "Enter" with no value to close console.')

        if not endingInput:
            break
