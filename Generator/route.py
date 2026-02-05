import csv
import util.createColumnDoesNotExist

def insert(file, c):
    try:
        print(file)
        c.execute ("delete from route")
        try:
            c.execute("alter table route add favorite integer")
        except Exception as err:
            print ("Column favorite already in place")
        
        with open(file, newline='',encoding="utf8") as csvfile:
            line = csvfile.readline().replace("\n","")

            util.createColumnDoesNotExist.createColumn(c,line,"route")

            c.copy_expert("COPY route (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)

    except Exception as err:
        print ("Error in generation",err)