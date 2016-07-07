from pymongo import MongoClient


class ConnectionDB:
    instance = None
    con = None

    def __new__(cls):
        if ConnectionDB.instance is None:
            ConnectionDB.instance = object.__new__(cls)
        return ConnectionDB.instance

    def __init__(self):
        if ConnectionDB.con is None:
            try:
                ConnectionDB.con = MongoClient(host="192.168.0.10", port=27017)
            except:
                print "Error"
                raise

    def __del__(self):
        if ConnectionDB.con is not None:
            ConnectionDB.con.close()
