python insertCalendarSQLLite.py ./%1/calendar.txt ./%1/%2  
python insertStopsTimeSQLLite.py ./%1/stop_times.txt ./%1/%2
python insertTripsSQLLite.py ./%1/trips.txt ./%1/%2
python insertStopsSQLLite.py ./%1/stops.txt ./%1/%2
python insertRouteSQLLite.py ./%1/routes.txt ./%1/%2
python insertShapeSQLLite.py ./%1/shapes.txt ./%1/%2
python insertFareSQLLite.py ./%1/fare_attributes.txt ./%1/%2
IF EXIST ./%1/calendar_dates.txt (
    python insertCalendarDateSQLLite.py ./%1/calendar_dates.txt ./%1/%2
)