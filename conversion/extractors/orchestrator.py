"""
Orchestrateur principal pour l'extraction de métadonnées.
Combine tous les extracteurs modulaires pour produire un JSON complet.
Supporte MinIO pour la récupération des PDFs et MongoDB pour la sauvegarde.
Mode local disponible via argument --local.
"""
import json
import os
import io
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import fitz  # PyMuPDF
from minio import Minio
from minio.error import S3Error
from pymongo import MongoClient

from .collectivite import CollectiviteExtractor, CommuneReference
from .deliberation import DeliberationExtractor
from .prefecture import PrefectureExtractor
from .seance import SeanceExtractor
from .vote import VoteExtractor
from .membres import MembresExtractor
from .paragraphes import ParagraphesExtractor

load_dotenv()

# Configuration par défaut (peut être surchargée par variables d'environnement)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin:admin@localhost:27017")

# Noms par défaut
DEFAULT_BUCKET = "larochelle-deliberations"
DEBUG_FOLDER = "debug"


class DeliberationOrchestrator:
    """Orchestrateur pour l'extraction complète des métadonnées d'une délibération."""
    
    def __init__(self, communes_csv_path: str = None, debug: bool = False, 
                 local_mode: bool = False, bucket_name: str = None):
        """
        Initialise l'orchestrateur.
        
        Args:
            communes_csv_path: Chemin vers le CSV des communes (pour SIRET/PREF_ID)
            debug: Active le mode debug (sauvegarde du texte extrait)
            local_mode: Si True, utilise les chemins locaux au lieu de MinIO/MongoDB
            bucket_name: Nom du bucket MinIO (défaut: larochelle-deliberations)
        """
        self.debug = debug
        self.local_mode = local_mode
        self.bucket_name = bucket_name or DEFAULT_BUCKET
        
        # Initialiser les clients MinIO et MongoDB si pas en mode local
        self.minio_client = None
        self.mongo_client = None
        self.db = None
        self.metadata_col = None
        
        if not local_mode:
            self._init_minio()
            self._init_mongodb()
        
        # Charger la référence des communes
        self.commune_ref = None
        if communes_csv_path:
            self.commune_ref = CommuneReference(communes_csv_path)
        else:
            # Essayer le chemin par défaut
            default_csv = Path(__file__).parent.parent / "communes_reference.csv"
            if default_csv.exists():
                self.commune_ref = CommuneReference(str(default_csv))
    
    def _init_minio(self):
        """Initialise le client MinIO."""
        try:
            self.minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )
            # S'assurer que le bucket existe
            if not self.minio_client.bucket_exists(self.bucket_name):
                print(f"Avertissement: Le bucket '{self.bucket_name}' n'existe pas")
        except Exception as e:
            print(f"Erreur de connexion MinIO: {e}")
            self.minio_client = None
    
    def _init_mongodb(self):
        """Initialise le client MongoDB."""
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client["deliberations"]
            self.metadata_col = self.db["metadata"]
            self.documents_col = self.db["documents"]  # Collection des documents scrapés
            # Test de connexion
            self.mongo_client.admin.command('ping')
        except Exception as e:
            print(f"Erreur de connexion MongoDB: {e}")
            self.mongo_client = None
            self.db = None
            self.metadata_col = None
            self.documents_col = None
    
    def _get_document_url(self, filename: str) -> str:
        """
        Récupère l'URL du document depuis la collection documents (scraper).
        
        Args:
            filename: Nom du fichier PDF
            
        Returns:
            URL du document ou chaîne vide si non trouvé
        """
        if self.documents_col is None:
            return ""
        
        doc = self.documents_col.find_one({"filename": filename, "bucket": self.bucket_name})
        if doc and doc.get("url"):
            return doc["url"]
        return ""
    
    def _get_pdf_from_minio(self, filename: str) -> bytes:
        """Récupère un PDF depuis MinIO."""
        if not self.minio_client:
            raise RuntimeError("Client MinIO non initialisé")
        
        try:
            response = self.minio_client.get_object(self.bucket_name, filename)
            pdf_data = response.read()
            response.close()
            response.release_conn()
            return pdf_data
        except S3Error as e:
            raise RuntimeError(f"Erreur lors de la récupération de {filename}: {e}")
    
    def _list_pdfs_in_bucket(self) -> list:
        """Liste tous les PDFs dans le bucket MinIO."""
        if not self.minio_client:
            return []
        
        try:
            objects = self.minio_client.list_objects(self.bucket_name)
            return [obj.object_name for obj in objects if obj.object_name.endswith('.pdf')]
        except S3Error as e:
            print(f"Erreur lors du listing du bucket: {e}")
            return []
    
    def _save_debug_to_minio(self, filename: str, text: str):
        """Sauvegarde le texte de debug dans MinIO sous le dossier debug/."""
        if not self.minio_client:
            print("[DEBUG] Client MinIO non disponible, impossible de sauvegarder le debug")
            return
        
        debug_filename = f"{DEBUG_FOLDER}/{Path(filename).stem}.txt"
        text_bytes = text.encode('utf-8')
        text_stream = io.BytesIO(text_bytes)
        
        try:
            self.minio_client.put_object(
                self.bucket_name,
                debug_filename,
                text_stream,
                len(text_bytes),
                content_type="text/plain"
            )
            print(f"[DEBUG] Texte sauvegardé dans MinIO: {debug_filename}")
        except S3Error as e:
            print(f"[DEBUG] Erreur lors de la sauvegarde: {e}")
    
    def _metadata_exists(self, filename: str) -> bool:
        """
        Vérifie si les métadonnées existent déjà pour un fichier.
        
        Args:
            filename: Nom du fichier PDF
            
        Returns:
            True si les métadonnées existent déjà
        """
        if self.metadata_col is None:
            return False
        
        return self.metadata_col.find_one({"filename": filename, "bucket": self.bucket_name}) is not None
    
    def _get_processed_filenames(self) -> set:
        """
        Récupère l'ensemble des fichiers déjà traités pour ce bucket.
        
        Returns:
            Set des noms de fichiers déjà présents dans la collection metadata
        """
        if self.metadata_col is None:
            return set()
        
        cursor = self.metadata_col.find(
            {"bucket": self.bucket_name},
            {"filename": 1}
        )
        return {doc["filename"] for doc in cursor}
    
    def _clear_metadata_collection(self):
        """
        Supprime toutes les métadonnées du bucket courant.
        Utilisé avec l'option --force pour recréer entièrement la collection.
        """
        if self.metadata_col is None:
            return
        
        result = self.metadata_col.delete_many({"bucket": self.bucket_name})
        print(f"🗑️  {result.deleted_count} entrée(s) supprimée(s) de la collection metadata pour le bucket '{self.bucket_name}'")
    
    def _save_metadata_to_mongodb(self, full_data: dict, scdl_data: dict, filename: str) -> str:
        """
        Sauvegarde les métadonnées dans MongoDB.
        
        Args:
            full_data: Métadonnées complètes
            scdl_data: Métadonnées au format SCDL
            filename: Nom du fichier source
            
        Returns:
            ID du document inséré
        """
        if self.metadata_col is None:
            raise RuntimeError("Collection MongoDB non initialisée")
        
        document = {
            "filename": filename,
            "bucket": self.bucket_name,
            "extracted_at": datetime.now(timezone.utc),
            "full_metadata": full_data,
            "scdl_metadata": scdl_data
        }
        
        # Vérifier si une entrée existe déjà pour ce fichier
        existing = self.metadata_col.find_one({"filename": filename, "bucket": self.bucket_name})
        if existing:
            # Mettre à jour l'entrée existante
            self.metadata_col.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "extracted_at": datetime.now(timezone.utc),
                    "full_metadata": full_data,
                    "scdl_metadata": scdl_data
                }}
            )
            return str(existing["_id"])
        else:
            # Créer une nouvelle entrée
            result = self.metadata_col.insert_one(document)
            return str(result.inserted_id)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un PDF local."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Erreur lors de l'extraction du PDF {pdf_path}: {e}")
        return text
    
    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes, filename: str = "unknown") -> str:
        """Extrait le texte d'un PDF depuis des bytes."""
        text = ""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Erreur lors de l'extraction du PDF {filename}: {e}")
        return text
    
    def _extract_metadata_from_text(self, text: str, source_file: str, document_url: str = "") -> dict:
        """
        Extrait les métadonnées à partir du texte.
        
        Args:
            text: Texte extrait du PDF
            source_file: Nom du fichier source
            document_url: URL du document source (depuis le scraper)
            
        Returns:
            Dictionnaire des métadonnées structurées
        """
        result = {
            "_metadata": {
                "source_file": source_file,
                "extraction_date": datetime.now().isoformat(),
                "version": "2.0.0"
            }
        }
        
        # Exécuter chaque extracteur
        # Collectivité (avec référence communes)
        collectivite_ext = CollectiviteExtractor(text, self.commune_ref)
        result["collectivite"] = collectivite_ext.extract()
        
        # Délibération
        delib_ext = DeliberationExtractor(text)
        delib_data = delib_ext.extract()
        # Ajouter l'URL du document (depuis le scraper)
        delib_data["url_document"] = document_url
        result["deliberation"] = delib_data
        
        # Préfecture (récupérer pref_id depuis collectivité)
        pref_ext = PrefectureExtractor(text)
        pref_data = pref_ext.extract()
        # Ajouter pref_id si disponible
        pref_id = collectivite_ext.get_pref_id()
        if pref_id:
            pref_data["id"] = pref_id
        result["prefecture"] = pref_data
        
        # Séance
        seance_ext = SeanceExtractor(text)
        result["seance"] = seance_ext.extract()
        
        # Vote
        vote_ext = VoteExtractor(text)
        result["vote"] = vote_ext.extract()
        
        # Membres
        membres_ext = MembresExtractor(text)
        membres_data = membres_ext.extract()
        result["membres_presents"] = membres_data.get("membres_presents", [])
        result["membres_absents"] = membres_data.get("membres_absents", [])
        
        # Paragraphes et contenus textuels
        para_ext = ParagraphesExtractor(text)
        para_data = para_ext.extract()
        result["considerants"] = para_data.get("considerants", {})
        result["commission_consultee"] = para_data.get("commission_consultee", {})
        result["decision"] = para_data.get("decision", "")
        result["paragraphes"] = para_data.get("paragraphes", {})
        
        return result
    
    def process_pdf(self, pdf_path: str) -> dict:
        """
        Traite un PDF local et extrait toutes les métadonnées.
        
        Args:
            pdf_path: Chemin vers le fichier PDF local
            
        Returns:
            Dictionnaire des métadonnées structurées
        """
        # Extraire le texte
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            return {"error": f"Impossible d'extraire le texte de {pdf_path}"}
        
        filename = os.path.basename(pdf_path)
        
        # Mode debug : sauvegarder le texte extrait
        if self.debug:
            if self.local_mode:
                debug_path = Path(pdf_path).with_suffix('.txt')
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"[DEBUG] Texte sauvegardé dans {debug_path}")
            else:
                self._save_debug_to_minio(filename, text)
        
        return self._extract_metadata_from_text(text, filename)
    
    def process_pdf_from_minio(self, filename: str) -> dict:
        """
        Traite un PDF depuis MinIO et extrait toutes les métadonnées.
        
        Args:
            filename: Nom du fichier dans le bucket MinIO
            
        Returns:
            Dictionnaire des métadonnées structurées
        """
        if self.local_mode:
            raise RuntimeError("process_pdf_from_minio non disponible en mode local")
        
        # Récupérer le PDF depuis MinIO
        try:
            pdf_bytes = self._get_pdf_from_minio(filename)
        except Exception as e:
            return {"error": str(e)}
        
        # Extraire le texte
        text = self.extract_text_from_pdf_bytes(pdf_bytes, filename)
        
        if not text:
            return {"error": f"Impossible d'extraire le texte de {filename}"}
        
        # Mode debug : sauvegarder le texte extrait
        if self.debug:
            self._save_debug_to_minio(filename, text)
        
        # Récupérer l'URL du document depuis la collection documents
        document_url = self._get_document_url(filename)
        
        return self._extract_metadata_from_text(text, filename, document_url)
    
    def convert_to_scdl(self, full_data: dict) -> dict:
        """
        Convertit les données complètes au format SCDL légal.
        
        Args:
            full_data: Données extraites complètes
            
        Returns:
            Dictionnaire au format SCDL (template_metadata_info.txt)
        """
        # Extraire les données imbriquées
        collectivite = full_data.get("collectivite", {})
        deliberation = full_data.get("deliberation", {})
        prefecture = full_data.get("prefecture", {})
        vote = full_data.get("vote", {})
        
        # Construire le format SCDL
        scdl = {
            "COLL_NOM": collectivite.get("nom", ""),
            "COLL_SIRET": collectivite.get("siret", ""),
            "DELIB_ID": deliberation.get("id", "").replace("DCM", ""),
            "DELIB_DATE": deliberation.get("date", ""),
            "DELIB_MATIERE_CODE": deliberation.get("matiere", {}).get("code", ""),
            "DELIB_MATIERE_NOM": deliberation.get("matiere", {}).get("nom", ""),
            "DELIB_OBJET": deliberation.get("objet", ""),
            "BUDGET_ANNEE": "",
            "BUDGET_NOM": "",
            "PREF_ID": prefecture.get("id", ""),
            "PREF_DATE": prefecture.get("date_envoi", ""),
            "VOTE_EFFECTIF": vote.get("membres_en_exercice"),
            "VOTE_REEL": vote.get("votants"),
            "VOTE_POUR": vote.get("votes_pour"),
            "VOTE_CONTRE": vote.get("votes_contre"),
            "VOTE_ABSTENTION": vote.get("abstentions"),
            "DELIB_URL": deliberation.get("url_document", "")
        }
        
        return scdl
    
    def process_directory(self, pdf_dir: str, output_path: str = None) -> tuple:
        """
        Traite tous les PDFs d'un répertoire local.
        En mode local: Produit deux fichiers JSON.
        En mode cloud: Sauvegarde dans MongoDB.
        
        Args:
            pdf_dir: Chemin vers le répertoire contenant les PDFs
            output_path: Chemin de sortie pour le JSON complet (mode local uniquement)
            
        Returns:
            Tuple (résultats complets, résultats SCDL)
        """
        results_full = []
        results_scdl = []
        pdf_dir = Path(pdf_dir)
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"Traitement de {len(pdf_files)} fichier(s) PDF...")
        
        for pdf_path in pdf_files:
            print(f"  - {pdf_path.name}")
            # Extraction complète
            result_full = self.process_pdf(str(pdf_path))
            results_full.append(result_full)
            
            # Conversion SCDL
            result_scdl = self.convert_to_scdl(result_full)
            results_scdl.append(result_scdl)
            
            # Sauvegarder dans MongoDB si pas en mode local
            if not self.local_mode and self.metadata_col is not None:
                doc_id = self._save_metadata_to_mongodb(result_full, result_scdl, pdf_path.name)
                print(f"    → Métadonnées sauvegardées dans MongoDB (ID: {doc_id})")
        
        # Sauvegarder les fichiers JSON si en mode local
        if self.local_mode:
            if output_path:
                output_full = Path(output_path)
                output_legal = output_full.parent / "output_legal.json"
            else:
                output_full = pdf_dir / "output.json"
                output_legal = pdf_dir / "output_legal.json"
            
            with open(output_full, 'w', encoding='utf-8') as f:
                json.dump(results_full, f, ensure_ascii=False, indent=2)
            print(f"Collection complète sauvegardée dans {output_full}")
            
            with open(output_legal, 'w', encoding='utf-8') as f:
                json.dump(results_scdl, f, ensure_ascii=False, indent=2)
            print(f"Collection SCDL sauvegardée dans {output_legal}")
        else:
            print(f"\n{len(results_full)} document(s) traité(s) et sauvegardé(s) dans MongoDB")
        
        return results_full, results_scdl
    
    def process_bucket(self, limit: int = None, force: bool = False) -> tuple:
        """
        Traite tous les PDFs du bucket MinIO.
        Les métadonnées sont sauvegardées dans MongoDB.
        Par défaut, ne traite que les nouveaux fichiers (non présents dans la collection metadata).
        
        Args:
            limit: Nombre maximum de PDFs à traiter (None = tous)
            force: Si True, supprime les métadonnées existantes et retraite tous les fichiers
            
        Returns:
            Tuple (résultats complets, résultats SCDL)
        """
        if self.local_mode:
            raise RuntimeError("process_bucket non disponible en mode local")
        
        if not self.minio_client:
            raise RuntimeError("Client MinIO non initialisé")
        
        # Mode force : supprimer toutes les métadonnées existantes
        if force:
            print("⚠️  Mode FORCE activé : suppression des métadonnées existantes...")
            self._clear_metadata_collection()
        
        results_full = []
        results_scdl = []
        
        # Récupérer la liste des PDFs dans le bucket
        all_pdf_files = self._list_pdfs_in_bucket()
        
        # Filtrer les fichiers déjà traités (sauf en mode force)
        if not force:
            processed_files = self._get_processed_filenames()
            pdf_files = [f for f in all_pdf_files if f not in processed_files]
            skipped_count = len(all_pdf_files) - len(pdf_files)
            if skipped_count > 0:
                print(f"ℹ️  {skipped_count} fichier(s) déjà traité(s), ignoré(s)")
        else:
            pdf_files = all_pdf_files
        
        # Appliquer la limite si spécifiée
        if limit:
            pdf_files = pdf_files[:limit]
        
        if not pdf_files:
            print("✅ Aucun nouveau fichier à traiter")
            return results_full, results_scdl
        
        print(f"Traitement de {len(pdf_files)} nouveau(x) fichier(s) PDF depuis le bucket '{self.bucket_name}'...")
        
        for filename in pdf_files:
            print(f"  - {filename}")
            # Extraction complète
            result_full = self.process_pdf_from_minio(filename)
            
            if "error" in result_full:
                print(f"    ⚠ Erreur: {result_full['error']}")
                continue
            
            results_full.append(result_full)
            
            # Conversion SCDL
            result_scdl = self.convert_to_scdl(result_full)
            results_scdl.append(result_scdl)
            
            # Sauvegarder dans MongoDB
            if self.metadata_col is not None:
                doc_id = self._save_metadata_to_mongodb(result_full, result_scdl, filename)
                print(f"    → Métadonnées sauvegardées dans MongoDB (ID: {doc_id})")
        
        print(f"\n✅ {len(results_full)} document(s) traité(s) et sauvegardé(s) dans MongoDB")
        
        return results_full, results_scdl
    
    def to_json(self, data: dict, indent: int = 2) -> str:
        """Convertit les données en JSON formaté."""
        return json.dumps(data, ensure_ascii=False, indent=indent)


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extraction de métadonnées de délibérations PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # Mode cloud - traite uniquement les NOUVEAUX PDFs du bucket MinIO
  python -m conversion.extractors.orchestrator --bucket larochelle-deliberations

  # Mode cloud avec limite (nouveaux fichiers uniquement)
  python -m conversion.extractors.orchestrator --bucket larochelle-deliberations -n 10

  # Mode cloud FORCE - supprime les métadonnées existantes et retraite tout
  python -m conversion.extractors.orchestrator --bucket larochelle-deliberations --force

  # Mode local - traite un répertoire local
  python -m conversion.extractors.orchestrator --local ./pdfs -o output.json

  # Mode local - traite un fichier unique
  python -m conversion.extractors.orchestrator --local ./document.pdf

  # Mode debug (sauvegarde les textes extraits)
  python -m conversion.extractors.orchestrator --bucket larochelle-deliberations -d
        """
    )
    
    # Groupe mutuellement exclusif : source des PDFs
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--bucket', '-b',
        help="Nom du bucket MinIO contenant les PDFs (mode cloud)"
    )
    source_group.add_argument(
        '--local', '-l',
        metavar='PATH',
        help="Chemin local vers un fichier PDF ou répertoire (mode local)"
    )
    
    # Options communes
    parser.add_argument(
        '-o', '--output',
        help="Fichier JSON de sortie (mode local uniquement)"
    )
    parser.add_argument(
        '-c', '--communes',
        help="Fichier CSV de référence des communes"
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help="Mode debug (sauvegarde le texte extrait dans MinIO ou localement)"
    )
    parser.add_argument(
        '-n', '--num',
        type=int,
        help="Nombre maximum de PDFs à traiter (mode cloud uniquement)"
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help="Mode force: supprime les métadonnées existantes et retraite tous les fichiers (mode cloud uniquement)"
    )
    
    args = parser.parse_args()
    
    # Déterminer le mode
    local_mode = args.local is not None
    
    # Créer l'orchestrateur
    orchestrator = DeliberationOrchestrator(
        communes_csv_path=args.communes,
        debug=args.debug,
        local_mode=local_mode,
        bucket_name=args.bucket if not local_mode else None
    )
    
    if local_mode:
        # Mode local
        input_path = Path(args.local)
        
        if input_path.is_file():
            result_full = orchestrator.process_pdf(str(input_path))
            result_scdl = orchestrator.convert_to_scdl(result_full)
            
            if args.output:
                output_full = Path(args.output)
                output_legal = output_full.parent / f"{output_full.stem}_legal.json"
                
                with open(output_full, 'w', encoding='utf-8') as f:
                    json.dump(result_full, f, ensure_ascii=False, indent=2)
                print(f"Collection complète sauvegardée dans {output_full}")
                
                with open(output_legal, 'w', encoding='utf-8') as f:
                    json.dump(result_scdl, f, ensure_ascii=False, indent=2)
                print(f"Collection SCDL sauvegardée dans {output_legal}")
            else:
                print("=== Collection complète ===")
                print(orchestrator.to_json(result_full))
                print("\n=== Collection SCDL ===")
                print(orchestrator.to_json(result_scdl))
                
        elif input_path.is_dir():
            output = args.output or str(input_path / "output.json")
            orchestrator.process_directory(str(input_path), output)
        else:
            print(f"Erreur: {args.local} n'existe pas")
            return 1
    else:
        # Mode cloud (MinIO + MongoDB)
        if orchestrator.minio_client is None:
            print("Erreur: Impossible de se connecter à MinIO")
            return 1
        
        if orchestrator.metadata_col is None:
            print("Erreur: Impossible de se connecter à MongoDB")
            return 1
        
        orchestrator.process_bucket(limit=args.num, force=args.force)
    
    return 0


if __name__ == "__main__":
    exit(main())
