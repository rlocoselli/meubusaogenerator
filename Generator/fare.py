import csv
import util.createColumnDoesNotExist

def insert(file, c):
    try:
        print(file)
        c.execute ("delete from fare_attributes")

        with open(file, newline='') as csvfile:
            line = csvfile.readline().replace("\n","")

            util.createColumnDoesNotExist.createColumn(c,line,"fare_attributes")

            c.copy_expert("COPY fare_attributes (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)

    except Exception as err:
        print ("Error in generation",err)