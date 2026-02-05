import os
import ddl
from postgresConnection import getConnectionCursor, getConnection
from zipfile import ZipFile
import requests
from Generator import calendar_dates, calendar, fare, route, shape, stops, stopstimes, trip
import psycopg2
from psycopg2 import sql

def create_log_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS log (
        id SERIAL PRIMARY KEY,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    cursor.execute(create_table_query)

def log_message(cursor, message):
    insert_query = """
    INSERT INTO log (message) VALUES (%s)
    """
    cursor.execute(insert_query, (message,))

def download_and_unzip(url, destination):
    # Download the zip file from the URL
    response = requests.get(url)
    zip_filename = os.path.join(destination, "data.zip")
    with open(zip_filename, "wb") as f:
        f.write(response.content)
    
    # Unzip the downloaded file
    with ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(destination)
    os.remove(zip_filename)

def insert_data_from_generator(subdir, cursor):
    if os.path.exists(os.path.join(subdir, "routes.txt")):
        calendar_dates.insert(os.path.join(subdir, "calendar_dates.txt"), cursor)
        calendar.insert(os.path.join(subdir, "calendar.txt"), cursor)
        fare.insert(os.path.join(subdir, "fare_attributes.txt"), cursor) 
        route.insert(os.path.join(subdir, "routes.txt"), cursor) 
        shape.insert(os.path.join(subdir, "shapes.txt"), cursor)
        stops.insert(os.path.join(subdir, "stops.txt"), cursor)
        stopstimes.insert(os.path.join(subdir, "stop_times.txt"), cursor)
        trip.insert(os.path.join(subdir, "trips.txt"), cursor)

# Get list of subdirectories
subdirs = [x[0] for x in os.walk('.')]

# Connect to PostgreSQL
conn = getConnection("postgres")
c = conn.cursor()

# Create log table if not exists
create_log_table(c)
conn.commit()

for y in subdirs:
    c = getConnectionCursor("postgres")
    if "_" in y and "__pycache__" not in y:
        db = y.replace("./","")
        print(db)
        # Get URL from url.txt file
        url_file_path = os.path.join(y, "url.txt")
        if not os.path.exists(url_file_path):
            print("url.txt not found in", y)
            log_message(c, f"url.txt not found in {y}")
            continue
        
        try:
            c.execute("CREATE DATABASE \"" + db + "\"")
            c.close()
        except Exception as err:
            print ("Database already exists " + db)
        
        c = getConnectionCursor(db)
        for table in ddl.table_names:
            try:
                c.execute("DROP TABLE " + table)
            except Exception as err:
                print ("Table does not exist to be dropped", table)
            
        for table in ddl.tables:
            try:
                c.execute(table)
            except Exception as err:
                print ("Table already created")
                
        try:
            with open(url_file_path, "r") as url_file:
                url = url_file.read().strip()
                # Download and unzip the file
                download_and_unzip(url, y)
                # Insert data using generator
                insert_data_from_generator(y, c)
        except Exception as err:
            print ("Error URL " + db)
                
        for index in ddl.indexes:
            try:
                c.execute(index)
            except Exception as err:
                print ("Index already created")
        
        # Update null values
     
