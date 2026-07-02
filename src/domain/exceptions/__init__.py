class BatchNotFoundError(Exception):
    def __init__(self, batch_id: int):
        self.batch_id = batch_id
        super().__init__(f"Batch {batch_id} not found")