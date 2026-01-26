import io
from abc import ABC, abstractmethod
from datetime import datetime
import requests
from minio import Minio
from minio.error import S3Error
from pymongo import MongoClient

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MONGO_URL = "mongodb://admin:admin@localhost:27017"


class BaseScraper(ABC):
    def __init__(self, bucket_name: str, source_name: str):
        self.bucket_name = bucket_name
        self.source_name = source_name
        self.minio = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
                           secret_key=MINIO_SECRET_KEY, secure=False)
        self.mongo = MongoClient(MONGO_URL)
        self.db = self.mongo["deliberations"]
        self.documents_col = self.db["documents"]
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.minio.bucket_exists(self.bucket_name):
            self.minio.make_bucket(self.bucket_name)
            print(f"Created bucket: {self.bucket_name}")

    def _object_exists(self, filename: str) -> bool:
        try:
            self.minio.stat_object(self.bucket_name, filename)
            return True
        except S3Error:
            return False

    def _doc_exists_in_db(self, filename: str) -> bool:
        return self.documents_col.find_one({"filename": filename, "source": self.source_name}) is not None

    def _save_to_db(self, pdf: dict):
        doc = {
            "filename": pdf["filename"],
            "title": pdf.get("title"),
            "source": self.source_name,
            "bucket": self.bucket_name,
            "url": pdf.get("url"),
            "metadata": pdf.get("metadata"),
            "created_at": datetime.utcnow()
        }
        self.documents_col.insert_one(doc)

    def upload_pdf(self, pdf: dict) -> bool:
        filename = pdf["filename"]
        url = pdf["url"]
        if self._object_exists(filename) and self._doc_exists_in_db(filename):
            print(f"  Already exists: {filename}")
            return True
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = io.BytesIO(response.content)
            self.minio.put_object(self.bucket_name, filename, data, len(response.content), content_type="application/pdf")
            self._save_to_db(pdf)
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
        success = sum(1 for pdf in pdfs if self.upload_pdf(pdf))
        print(f"\nDone! Uploaded {success}/{len(pdfs)} PDFs")
        return pdfs
