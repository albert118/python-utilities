def ConfigureDbTableName(defaultName: str) -> str:
    tableName = input(f'\nWhat is the DB table name? (Enter no value to default to "{defaultName}"): ')
    if not tableName:
        tableName = defaultName
    return tableName