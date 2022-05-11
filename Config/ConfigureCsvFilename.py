def ConfigureCsvFilename(defaultName: str = 'my-file'):
    filename = input(f'Enter the csv filename (exclude the .csv extension suffix. Enter no value to default to "{defaultName}"): ')
    if not filename:
        filename = defaultName

    fullFilename = filename + '.csv'
    print(f'\nThe full filename will be "{fullFilename}"')
    
    return fullFilename