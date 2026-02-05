def getDatabase(db):
    print(db)
    if db == "Grenoble_France":
        return "./" + db + "/grenoble.db"
    elif db == "Managua_Nicaragua":
        return "./" + db + "/managua.db"
    elif db == "PortoAlegre_Brazil":
        return "./" + db + "/poa.db"
    elif db == "Esteli_Nicaragua":
        return "./" + db + "/esteli.db"
    elif db == "Otago_NewZealand":
        return "./" + db + "/otago.db"
    elif db == "SaoPaulo_Brazil":
        return "./" + db + "/saopaulo.db"
    elif db == "Funchal_Portugal":
        return "./" + db + "/funchal.db"
