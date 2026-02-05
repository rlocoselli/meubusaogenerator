import csv
import util.createColumnDoesNotExist

def insert(file, c):
    try:
        print(file)
        
        c.execute ("delete from stopstime")
        
        with open(file, newline='') as csvfile:
            line = csvfile.readline().replace("\n","")

            util.createColumnDoesNotExist.createColumn(c,line,"stopstime")
            c.copy_expert("COPY stopstime (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)

    except Exception as err:
        print ("Error in generation",err)