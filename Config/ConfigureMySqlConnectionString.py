import urllib

# Enter login credentials for database connection
def ConfigureMySqlConnectionString(defaultIp: str = '127.0.0.1', defaultPort: str = '3306', defaultDbName: str = 'pmdb_dev') -> str:
    print('\nSETTING UP DB CONNECTION:')
    user = input('Enter the DB username (no spaces!): ')
    inPw = input('Enter the DB password (no apostrophes!): ')
    pw = urllib.parse.quote_plus(inPw)
    
    defaultIpAndPort = defaultIp + ':' + defaultPort
    
    ipAndPort = input(f'What is the DB ip and port? (Enter no value to default to "{defaultIpAndPort}"): ')
    if not ipAndPort:
        ipAndPort = defaultIpAndPort
        
    dbName = input(f'What is the DB name? (Enter no value to default to "{defaultDbName}"): ')
    if not dbName:
        dbName = defaultDbName
        
    dbString = f'mysql+pymysql://{user}:{pw}@{ipAndPort}/{dbName}'
    
    print(f'\nThe db connection string to be used is "{dbString}"')
    
    return dbString