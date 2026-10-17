import asyncio
import io
import os

from minio import Minio


class ObjectStorage:
    def __init__(self, client: Minio, bucket: str):
        self.client = client
        self.bucket = bucket

    async def ensure_bucket(self):
        if not await asyncio.to_thread(self.client.bucket_exists, self.bucket):
            await asyncio.to_thread(self.client.make_bucket, self.bucket)

    async def upload(self, key: str, data: bytes, content_type: str):
        await asyncio.to_thread(
            self.client.put_object,
            self.bucket,
            key,
            io.BytesIO(data),
            len(data),
            content_type=content_type,
        )

    async def delete(self, key: str):
        await asyncio.to_thread(self.client.remove_object, self.bucket, key)


minio_client = Minio(
    endpoint=os.environ["MINIO_ENDPOINT"],
    access_key=os.environ["MINIO_ROOT_USER"],
    secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
)

bucket = os.environ["MINIO_BUCKET"]
storage = ObjectStorage(minio_client, bucket)
