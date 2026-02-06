import argparse
import io
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import requests
from minio import Minio
from minio.error import S3Error
from pymongo import MongoClient

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MONGO_URL = "mongodb://admin:admin@localhost:27017"


class BaseScraper(ABC):
    def __init__(self, bucket_name: str, source_name: str, local_mode: bool = False, local_path: str = None):
        self.bucket_name = bucket_name
        self.source_name = source_name
        self.local_mode = local_mode
        self.local_path = Path(local_path) if local_path else None

        if local_mode:
            # Mode local: pas de connexion MinIO/MongoDB
            self.minio = None
            self.mongo = None
            self.db = None
            self.documents_col = None
            if self.local_path:
                self.local_path.mkdir(parents=True, exist_ok=True)
                print(f"Mode local: sauvegarde dans {self.local_path}")
        else:
            # Mode cloud: connexion MinIO + MongoDB
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
        if self.documents_col is None:
            return False
        return self.documents_col.find_one({"filename": filename, "source": self.source_name}) is not None

    def _file_exists_local(self, filename: str) -> bool:
        if not self.local_path:
            return False
        return (self.local_path / filename).exists()

    def _save_pdf_local(self, pdf: dict, force: bool = False) -> bool:
        """Sauvegarde un PDF localement."""
        filename = pdf["filename"]
        url = pdf["url"]

        if not force and self._file_exists_local(filename):
            print(f"  Already exists: {filename}")
            return True

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            file_path = self.local_path / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"  Saved: {filename}")
            return True
        except Exception as e:
            print(f"  Error: {filename} - {e}")
            return False

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

    def upload_pdf(self, pdf: dict, force: bool = False) -> bool:
        # Mode local: sauvegarde dans un répertoire
        if self.local_mode:
            return self._save_pdf_local(pdf, force)

        # Mode cloud: upload vers MinIO + sauvegarde MongoDB
        filename = pdf["filename"]
        url = pdf["url"]
        if not force and self._object_exists(filename) and self._doc_exists_in_db(filename):
            print(f"  Already exists: {filename}")
            return True
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = io.BytesIO(response.content)
            self.minio.put_object(self.bucket_name, filename, data, len(
                response.content), content_type="application/pdf")
            # En mode force, on supprime l'ancien document avant d'insérer
            if force:
                self.documents_col.delete_one(
                    {"filename": filename, "source": self.source_name})
            self._save_to_db(pdf)
            print(f"  Uploaded: {filename}")
            return True
        except Exception as e:
            print(f"  Error: {filename} - {e}")
            return False

    @abstractmethod
    def fetch_pdf_links(self, num_documents: int = None, page_size: int = None) -> list[dict]:
        pass

    def run(self, num_documents: int = None, page_size: int = None, force: bool = False):
        pdfs = self.fetch_pdf_links(num_documents, page_size)
        print(f"\nTotal PDFs found: {len(pdfs)}")

        if self.local_mode:
            print(f"Saving to '{self.local_path}'...\n")
        else:
            print(f"Uploading to bucket '{self.bucket_name}'...\n")

        success = sum(1 for pdf in pdfs if self.upload_pdf(pdf, force=force))

        if self.local_mode:
            print(f"\nDone! Saved {success}/{len(pdfs)} PDFs locally")
        else:
            print(f"\nDone! Uploaded {success}/{len(pdfs)} PDFs")
        return pdfs

    @classmethod
    def create_argument_parser(cls, description: str = "Scraper de délibérations") -> argparse.ArgumentParser:
        """Crée un parser d'arguments commun à tous les scrapers."""
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Groupe mutuellement exclusif: mode cloud ou local
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            "--bucket", "-b",
            help="Nom du bucket MinIO (remplace le bucket par défaut)"
        )
        mode_group.add_argument(
            "--local", "-l",
            metavar="PATH",
            help="Chemin local pour sauvegarder les PDFs (mode local)"
        )

        parser.add_argument(
            "--force", "-f",
            action="store_true",
            help="Force le re-téléchargement même si le document existe déjà"
        )

        return parser

    @classmethod
    def run_from_cli(cls):
        """Exécute le scraper à partir des arguments CLI."""
        parser = cls.create_argument_parser()
        cls.add_scraper_arguments(parser)
        args = parser.parse_args()

        # Déterminer le mode
        local_mode = args.local is not None

        # Créer le scraper
        scraper = cls(local_mode=local_mode, local_path=args.local)

        # En mode cloud, appliquer le bucket personnalisé si spécifié
        if not local_mode and args.bucket:
            scraper.bucket_name = args.bucket
            scraper._ensure_bucket()

        scraper.run_with_args(args)

    @classmethod
    def add_scraper_arguments(cls, parser: argparse.ArgumentParser):
        """Ajoute les arguments spécifiques au scraper. À surcharger dans les sous-classes."""
        pass

    def run_with_args(self, args: argparse.Namespace):
        """Exécute le scraper avec les arguments parsés. À surcharger dans les sous-classes."""
        self.run(force=args.force)
