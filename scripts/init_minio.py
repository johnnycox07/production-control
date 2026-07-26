from minio import Minio

from src.core.config import settings

BUCKETS = ["reports", "exports", "imports"]


def initialize_minio_buckets():
    client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        secure=settings.minio_secure,   
    )

    for bucket in BUCKETS:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"Created bucket: {bucket}")
        else:
            print(f"Bucket already exists: {bucket}")


if __name__ == "__main__":
    initialize_minio_buckets()