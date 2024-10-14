from skyflow.generated.rest import V1BulkDeleteRecordResponse


class DeleteResponse:
    def __init__(self, deleted_ids, error):
        self.deleted_ids = deleted_ids
        self.error = error

    def __repr__(self):
        return f"DeleteResponse(deleted_ids={self.deleted_ids}, error={self.error})"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parsed_delete_response(delete_response: V1BulkDeleteRecordResponse):
        deleted_ids = delete_response.record_id_response
        error = []
        return DeleteResponse(deleted_ids=deleted_ids, error=error)