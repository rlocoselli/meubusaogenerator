import csv
import util.createColumnDoesNotExist

def insert(file, c):
    try:
        print(file)
    
        c.execute ("delete from calendar")
        
        with open(file, newline='') as csvfile:
            line = csvfile.readline().replace("\n","")

            util.createColumnDoesNotExist.createColumn(c,line,"calendar")

            c.copy_expert("COPY calendar (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)

    except Exception as err:
        print ("Error in generation",err)