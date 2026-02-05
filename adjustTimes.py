from calculateDistanceStopsPostgres import GenerateTimes
 
from postgresConnection import getConnectionCursor, getConnection
import sys

conn = getConnection("PortoAlegre_Brazil")
c = getConnectionCursor("PortoAlegre_Brazil")
GenerateTimes(c, conn, int(sys.argv[1]),int(sys.argv[2]))
c.close()
conn.close()
