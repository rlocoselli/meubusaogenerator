from updateStops import updateStops
 
from postgresConnection import getConnectionCursor, getConnection
import sys

conn = getConnection("PortoAlegre_Brazil")
c = getConnectionCursor("PortoAlegre_Brazil")
updateStops(c, conn)