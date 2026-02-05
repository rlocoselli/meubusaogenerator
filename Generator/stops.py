import csv
import util.replaceQuotesCSV
import util.createColumnDoesNotExist

def insert(file, c):
    try:
        print(file)
        
        c.execute ("delete from stops")
            
        with open(file, newline='', encoding="utf8") as csvfile:
            line = csvfile.readline().replace("\n","")

            util.createColumnDoesNotExist.createColumn(c,line,"stops")
            c.copy_expert("COPY stops (" + line + ") FROM STDIN (FORMAT CSV)", csvfile)

    except Exception as err:
        print ("Error in generation",err)