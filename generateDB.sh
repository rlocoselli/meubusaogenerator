python3 insertCalendarSQLLite.py ./$1/calendar.txt ./$1/$2  
python3 insertStopsTimeSQLLite.py ./$1/stop_times.txt ./$1/$2
python3 insertTripsSQLLite.py ./$1/trips.txt ./$1/$2
python3 insertStopsSQLLite.py ./$1/stops.txt ./$1/$2
python3 insertRouteSQLLite.py ./$1/routes.txt ./$1/$2
python3 insertShapeSQLLite.py ./$1/shapes.txt ./$1/$2
python3 insertFareSQLLite.py ./$1/fare_attributes.txt ./$1/$2
python3 insertCalendarDateSQLLite.py ./$1/calendar_dates.txt ./$1/$2