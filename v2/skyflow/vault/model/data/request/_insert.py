class InsertRequest:
    _table_name = None
    #members
    def __init__(self):
        pass
    #methods

    def __set_table_name(self, table_name: str):
        self.__table_name = table_name
        print("st table name: ", self.__table_name)