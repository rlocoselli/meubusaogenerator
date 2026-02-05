import csv
import util.createColumnDoesNotExist

def insert(file, c):
    try:
        print(file)
        
        c.execute ("delete from trip")
        
        with open(file, newline='') as csvfile:
            line = csvfile.readline().replace("\n","")
            list_columns = tuple(e for e in line.split(","))
            util.createColumnDoesNotExist.createColumn(c,line,"trip")
            c.copy_expert("COPY trip (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)

    except Exception as err:
        print ("Error in generation",err)