class BatchNotFoundError(Exception):
    def __init__(self, batch_id: int):
        self.batch_id = batch_id
        super().__init__(f"Batch {batch_id} not found")

class ProductNotFoundError(Exception):
    def __init__(self, unique_code: str):
        self.product_id = unique_code
        super().__init__(f"Product {unique_code} not found")

class ProductAlreadyAggregatedError(Exception):
    def __init__(self, unique_code: str):
        self.unique_code = unique_code
        super().__init__(f"Product {unique_code} is already aggregated")

class WebhookNotFoundError(Exception):
    def __init__(self, webhook_id: int):
        self.webhook_id = webhook_id
        super().__init__(f"Webhook subscription {webhook_id} not found")