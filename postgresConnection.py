import psycopg2 
import os

def getConnectionCursor(database):
    server = os.environ['SERVER']
    conn = psycopg2.connect(
    host=server,
    database=database,
    user=os.environ['USER'],
    password=os.environ['MOT'])
    
    conn.set_client_encoding('UTF8')
    
    conn.autocommit = True

    cursor = conn.cursor()

    return cursor

def getConnection(database):
    server = os.environ['SERVER']
    conn = psycopg2.connect(
    host=server,
    database=database,
    user=os.environ['USER'],
    password=os.environ['MOT'])
    
    conn.set_client_encoding('UTF8')
    
    conn.autocommit = True

    return conn