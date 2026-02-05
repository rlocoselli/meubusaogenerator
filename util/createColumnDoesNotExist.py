def createColumn (cursor,columns, table):
    for e in columns.split(","):
        try:
            cursor.execute ("ALTER TABLE " + table + " ADD " + e + " TEXT NULL")
        except Exception as err:
            a = 1
            #Column already exists
            