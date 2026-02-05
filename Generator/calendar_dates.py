import csv
import util.createColumnDoesNotExist

def insert(file, c):
    try:
        print(file)
        
        c.execute ("delete from calendar_dates")
        
        with open(file, newline='') as csvfile:
            line = csvfile.readline().replace("\n","")

            util.createColumnDoesNotExist.createColumn(c,line,"calendar_dates")
            c.copy_expert("COPY calendar_dates (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)

        c.execute ("UPDATE CALENDAR_DATES SET DATET = DATE WHERE DATET IS NULL")
        
    except Exception as err:
        print ("Error in generation",err)