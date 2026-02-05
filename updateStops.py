from datetime import datetime,timedelta
import sys
import sqlite3
from Distance import getDistance
from geopy.geocoders import Nominatim


def updateStops (c, conn):

    c.execute("select stop_name, stop_id, stop_lat, stop_lon from stops")
    
    rows = c.fetchall()

    i = 0
    
    geolocator = Nominatim(user_agent="Meubusao")

    for row in rows:
        
        try:
            Latitude = str(row[2])
            Longitude = str(row[3])
            
            location = geolocator.reverse(Latitude+","+Longitude)
            
            address = location.raw['address']
                        
            addr = address.get("road") + " " + str(address.get("house_number") or "") + " - " + str(address.get("suburb") or "")
            
            allAddr = f"{row[0]}({addr})"
            
            print(allAddr)
            
            cSql=f"UPDATE STOPS set stop_name='{allAddr}' where stop_id = '{row[1]}'"
            
            c.execute(cSql) 
            
        except Exception as err:
            print("Error in trip",row[0])
            print(err)
