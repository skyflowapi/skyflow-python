class DetokenizeResponseRecordMetadata:
    def __init__(self, skyflow_id: str = None, table_name: str = None):
        self.skyflow_id = skyflow_id
        self.table_name = table_name

    def __repr__(self):
        return f"DetokenizeResponseRecordMetadata(skyflow_id={self.skyflow_id}, table_name={self.table_name})"

    def __str__(self):
        return self.__repr__()
