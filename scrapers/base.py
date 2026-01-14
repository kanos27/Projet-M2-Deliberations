import io
from abc import ABC, abstractmethod
import requests
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"


class BaseScraper(ABC):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
                            secret_key=MINIO_SECRET_KEY, secure=False)
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            print(f"Created bucket: {self.bucket_name}")

    def _object_exists(self, filename: str) -> bool:
        try:
            self.client.stat_object(self.bucket_name, filename)
            return True
        except S3Error:
            return False

    def upload_pdf(self, url: str, filename: str) -> bool:
        if self._object_exists(filename):
            print(f"  Already exists: {filename}")
            return True
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = io.BytesIO(response.content)
            self.client.put_object(self.bucket_name, filename, data, len(
                response.content), content_type="application/pdf")
            print(f"  Uploaded: {filename}")
            return True
        except Exception as e:
            print(f"  Error: {filename} - {e}")
            return False

    @abstractmethod
    def fetch_pdf_links(self, num_documents: int, page_size: int) -> list[dict]:
        pass

    def run(self, num_documents: int = 10, page_size: int = 10):
        pdfs = self.fetch_pdf_links(num_documents, page_size)
        print(f"\nTotal PDFs found: {len(pdfs)}")
        print(f"Uploading to bucket '{self.bucket_name}'...\n")
        success = sum(1 for pdf in pdfs if self.upload_pdf(
            pdf["url"], pdf["filename"]))
        print(f"\nDone! Uploaded {success}/{len(pdfs)} PDFs")
        return pdfs
