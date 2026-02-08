"""
Matiere Classification Tester

Comprehensive testing tool for the matière/subject extraction pipeline.
Tests keyword-based and LLM-based classification methods against documents.

Features:
- Accept single file, folder, or MinIO bucket as input
- Return detailed JSON results per document
- Multi-model LLM comparison
- Overall match ratio calculation

Usage:
    python matiere_tester.py --file path/to/file.pdf
    python matiere_tester.py --folder path/to/folder
    python matiere_tester.py --bucket bucket-name --prefix optional/prefix
    python matiere_tester.py --folder path/to/folder --compare-models
"""

import os
import sys
import json
import argparse
import time
import tempfile
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Try to import MinIO
try:
    from minio import Minio
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    print("[Warning] minio not installed. Bucket testing disabled.")

# Try to import PyMuPDF for PDF handling
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("[Warning] PyMuPDF not installed. PDF handling disabled.")

from conversion.extractors.matiere import (
    MatiereExtractor, NomenclatureParser, MODELS, HF_TOKEN
)


class MatiereTester:
    """
    Comprehensive tester for matière extraction.
    Compares keyword-based and LLM-based classification.
    """
    
    def __init__(
        self,
        nomenclature_path: str = None,
        minio_endpoint: str = None,
        minio_access_key: str = None,
        minio_secret_key: str = None,
        minio_secure: bool = False
    ):
        """
        Initialize the tester.
        
        Args:
            nomenclature_path: Path to ACTES nomenclature file
            minio_endpoint: MinIO server endpoint (optional)
            minio_access_key: MinIO access key (optional)
            minio_secret_key: MinIO secret key (optional)
            minio_secure: Use HTTPS for MinIO (default: False)
        """
        self.nomenclature_path = nomenclature_path
        self.nomenclature = NomenclatureParser(nomenclature_path)
        
        # MinIO client setup
        self.minio_client = None
        if MINIO_AVAILABLE and minio_endpoint:
            try:
                self.minio_client = Minio(
                    minio_endpoint,
                    access_key=minio_access_key or os.getenv("MINIO_ACCESS_KEY"),
                    secret_key=minio_secret_key or os.getenv("MINIO_SECRET_KEY"),
                    secure=minio_secure
                )
            except Exception as e:
                print(f"[Warning] Failed to initialize MinIO client: {e}")
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        if not PDF_AVAILABLE:
            raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
        
        text_parts = []
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}")
        
        return "\n".join(text_parts)
    
    def _read_text_file(self, file_path: str) -> str:
        """Read text from a text file."""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not decode file {file_path} with any supported encoding")
    
    def _get_text_from_file(self, file_path: str) -> str:
        """Extract text from a file (PDF or text)."""
        path = Path(file_path)
        
        if path.suffix.lower() == '.pdf':
            return self._extract_text_from_pdf(file_path)
        elif path.suffix.lower() in ['.txt', '.text', '.json', '.md']:
            return self._read_text_file(file_path)
        else:
            # Try to read as text
            try:
                return self._read_text_file(file_path)
            except Exception:
                raise ValueError(f"Unsupported file type: {path.suffix}")
    
    def _classify_keywords_only(self, text: str) -> dict:
        """Classify using keywords only (no LLM)."""
        extractor = MatiereExtractor(
            text, 
            nomenclature_path=self.nomenclature_path,
            use_llm=False
        )
        
        # Get keyword result directly
        result = extractor._classify_by_keywords()
        
        if result:
            return {
                "code": result.get("code", ""),
                "nom": result.get("nom", ""),
                "confidence": result.get("confidence", 0.0)
            }
        
        return {"code": "", "nom": "", "confidence": 0.0}
    
    def _classify_llm_only(self, text: str, model_key: str = "default") -> dict:
        """Classify using LLM only."""
        if not HF_TOKEN:
            return {
                "code": "",
                "nom": "",
                "confidence": 0.0,
                "error": "HF_TOKEN not set"
            }
        
        extractor = MatiereExtractor(
            text,
            nomenclature_path=self.nomenclature_path,
            use_llm=True,
            model_name=model_key
        )
        
        start_time = time.time()
        result = extractor._classify_with_llm()
        elapsed = time.time() - start_time
        
        if result:
            return {
                "code": result.get("code", ""),
                "nom": result.get("nom", ""),
                "confidence": result.get("confidence", 0.0),
                "response_time": round(elapsed, 2)
            }
        
        return {
            "code": "",
            "nom": "",
            "confidence": 0.0,
            "response_time": round(elapsed, 2),
            "error": "LLM returned no result"
        }
    
    def test_document(
        self, 
        text: str, 
        document_name: str = "unnamed",
        test_models: list = None
    ) -> dict:
        """
        Test classification on a single document.
        
        Args:
            text: Document text content
            document_name: Name/identifier for the document
            test_models: List of model keys to test (default: ["default"])
            
        Returns:
            Dict with classification results
        """
        if test_models is None:
            test_models = ["default"]
        
        # Get keyword classification
        keyword_result = self._classify_keywords_only(text)
        
        # Get LLM classifications for each model
        llm_results = {}
        for model_key in test_models:
            if model_key in MODELS:
                llm_results[model_key] = self._classify_llm_only(text, model_key)
                # Add a small delay between API calls to avoid rate limiting
                if len(test_models) > 1:
                    time.sleep(0.5)
            else:
                llm_results[model_key] = {
                    "code": "",
                    "nom": "",
                    "confidence": 0.0,
                    "error": f"Unknown model: {model_key}"
                }
        
        # Determine matches
        matches = {}
        for model_key, llm_result in llm_results.items():
            keyword_code = keyword_result.get("code", "")
            llm_code = llm_result.get("code", "")
            
            # Check exact match
            exact_match = keyword_code == llm_code
            
            # Check category match (first level)
            category_match = (
                keyword_code.split('.')[0] == llm_code.split('.')[0]
                if keyword_code and llm_code else False
            )
            
            matches[model_key] = {
                "exact_match": exact_match,
                "category_match": category_match
            }
        
        return {
            "document": document_name,
            "keyword_prediction": keyword_result,
            "llm_predictions": llm_results,
            "matches": matches
        }
    
    def test_file(
        self, 
        file_path: str, 
        test_models: list = None
    ) -> dict:
        """
        Test classification on a single file.
        
        Args:
            file_path: Path to the document file
            test_models: List of model keys to test
            
        Returns:
            Dict with classification results
        """
        try:
            text = self._get_text_from_file(file_path)
            return self.test_document(
                text, 
                document_name=Path(file_path).name,
                test_models=test_models
            )
        except Exception as e:
            return {
                "document": Path(file_path).name,
                "error": str(e)
            }
    
    def test_folder(
        self, 
        folder_path: str, 
        test_models: list = None,
        extensions: list = None,
        recursive: bool = False
    ) -> dict:
        """
        Test classification on all documents in a folder.
        
        Args:
            folder_path: Path to the folder
            test_models: List of model keys to test
            extensions: List of file extensions to process (default: [".pdf", ".txt"])
            recursive: Search subfolders recursively
            
        Returns:
            Dict with all results and overall statistics
        """
        if extensions is None:
            extensions = [".pdf", ".txt"]
        
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": f"Folder not found: {folder_path}"}
        
        # Find all matching files
        files = []
        if recursive:
            for ext in extensions:
                files.extend(folder.rglob(f"*{ext}"))
        else:
            for ext in extensions:
                files.extend(folder.glob(f"*{ext}"))
        
        files = sorted(files)
        
        if not files:
            return {"error": f"No matching files found in {folder_path}"}
        
        # Process each file
        results = []
        print(f"\n{'='*60}")
        print(f"Testing {len(files)} documents from: {folder_path}")
        print(f"Models: {test_models or ['default']}")
        print(f"{'='*60}\n")
        
        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Testing: {file_path.name}...", end=" ", flush=True)
            result = self.test_file(str(file_path), test_models=test_models)
            results.append(result)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                # Show quick summary
                kw = result.get("keyword_prediction", {}).get("code", "?")
                for model_key, match in result.get("matches", {}).items():
                    llm = result.get("llm_predictions", {}).get(model_key, {}).get("code", "?")
                    status = "✅" if match.get("exact_match") else "⚠️"
                    print(f"{status} kw={kw} | {model_key}={llm}", end=" ")
                print()
        
        # Calculate statistics
        return self._calculate_statistics(results, test_models or ["default"])
    
    def test_bucket(
        self,
        bucket_name: str,
        prefix: str = "",
        test_models: list = None,
        extensions: list = None
    ) -> dict:
        """
        Test classification on documents from a MinIO bucket.
        
        Args:
            bucket_name: Name of the MinIO bucket
            prefix: Object prefix to filter files
            test_models: List of model keys to test
            extensions: List of file extensions to process
            
        Returns:
            Dict with all results and overall statistics
        """
        if not MINIO_AVAILABLE:
            return {"error": "minio package not installed"}
        
        if not self.minio_client:
            return {"error": "MinIO client not configured"}
        
        if extensions is None:
            extensions = [".pdf", ".txt"]
        
        # List objects in bucket
        try:
            objects = self.minio_client.list_objects(
                bucket_name, prefix=prefix, recursive=True
            )
            
            # Filter by extension
            files = []
            for obj in objects:
                if any(obj.object_name.lower().endswith(ext) for ext in extensions):
                    files.append(obj.object_name)
            
        except Exception as e:
            return {"error": f"Failed to list bucket objects: {e}"}
        
        if not files:
            return {"error": f"No matching files found in bucket {bucket_name}/{prefix}"}
        
        # Process each file
        results = []
        print(f"\n{'='*60}")
        print(f"Testing {len(files)} documents from bucket: {bucket_name}/{prefix}")
        print(f"Models: {test_models or ['default']}")
        print(f"{'='*60}\n")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, object_name in enumerate(files, 1):
                file_name = Path(object_name).name
                local_path = Path(temp_dir) / file_name
                
                print(f"[{i}/{len(files)}] Testing: {file_name}...", end=" ", flush=True)
                
                try:
                    # Download file
                    self.minio_client.fget_object(bucket_name, object_name, str(local_path))
                    
                    # Test the file
                    result = self.test_file(str(local_path), test_models=test_models)
                    result["source"] = f"{bucket_name}/{object_name}"
                    results.append(result)
                    
                    if "error" in result:
                        print(f"❌ Error: {result['error']}")
                    else:
                        kw = result.get("keyword_prediction", {}).get("code", "?")
                        for model_key, match in result.get("matches", {}).items():
                            llm = result.get("llm_predictions", {}).get(model_key, {}).get("code", "?")
                            status = "✅" if match.get("exact_match") else "⚠️"
                            print(f"{status} kw={kw} | {model_key}={llm}", end=" ")
                        print()
                    
                except Exception as e:
                    results.append({
                        "document": file_name,
                        "source": f"{bucket_name}/{object_name}",
                        "error": str(e)
                    })
                    print(f"❌ Error: {e}")
        
        return self._calculate_statistics(results, test_models or ["default"])
    
    def _calculate_statistics(self, results: list, model_keys: list) -> dict:
        """Calculate overall statistics from test results."""
        total = len(results)
        errors = sum(1 for r in results if "error" in r)
        processed = total - errors
        
        # Per-model statistics
        model_stats = {}
        for model_key in model_keys:
            exact_matches = 0
            category_matches = 0
            total_response_time = 0
            response_count = 0
            
            for result in results:
                if "error" in result:
                    continue
                
                matches = result.get("matches", {}).get(model_key, {})
                if matches.get("exact_match"):
                    exact_matches += 1
                if matches.get("category_match"):
                    category_matches += 1
                
                llm_pred = result.get("llm_predictions", {}).get(model_key, {})
                if "response_time" in llm_pred:
                    total_response_time += llm_pred["response_time"]
                    response_count += 1
            
            model_stats[model_key] = {
                "model_name": MODELS.get(model_key, model_key),
                "exact_match_count": exact_matches,
                "exact_match_ratio": round(exact_matches / processed, 4) if processed > 0 else 0,
                "category_match_count": category_matches,
                "category_match_ratio": round(category_matches / processed, 4) if processed > 0 else 0,
                "avg_response_time": round(total_response_time / response_count, 2) if response_count > 0 else None
            }
        
        # Overall statistics (based on default model or first model)
        primary_model = "default" if "default" in model_keys else model_keys[0]
        primary_stats = model_stats.get(primary_model, {})
        
        return {
            "summary": {
                "total_documents": total,
                "processed": processed,
                "errors": errors,
                "overall_exact_match_ratio": primary_stats.get("exact_match_ratio", 0),
                "overall_category_match_ratio": primary_stats.get("category_match_ratio", 0),
                "test_date": datetime.now().isoformat(),
                "models_tested": model_keys
            },
            "model_comparison": model_stats,
            "results": results
        }
    
    def compare_models(
        self,
        source: str,
        source_type: str = "folder",
        bucket_name: str = None
    ) -> dict:
        """
        Run a full comparison across all available models.
        
        Args:
            source: Path to file/folder or bucket prefix
            source_type: "file", "folder", or "bucket"
            bucket_name: Bucket name if source_type is "bucket"
            
        Returns:
            Dict with comprehensive comparison results
        """
        all_models = list(MODELS.keys())
        
        print(f"\n{'='*60}")
        print("MULTI-MODEL COMPARISON TEST")
        print(f"Models to test: {', '.join(all_models)}")
        print(f"Model details:")
        for key, name in MODELS.items():
            print(f"  - {key}: {name}")
        print(f"{'='*60}")
        
        if source_type == "file":
            # For single file, wrap in statistics format
            result = self.test_file(source, test_models=all_models)
            return self._calculate_statistics([result], all_models)
        elif source_type == "folder":
            return self.test_folder(source, test_models=all_models)
        elif source_type == "bucket":
            return self.test_bucket(bucket_name, prefix=source, test_models=all_models)
        else:
            return {"error": f"Unknown source type: {source_type}"}


def save_results(results: dict, output_path: str):
    """Save results to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")


def print_summary(results: dict):
    """Print a formatted summary of test results."""
    summary = results.get("summary", {})
    model_comparison = results.get("model_comparison", {})
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total documents:    {summary.get('total_documents', 0)}")
    print(f"Successfully processed: {summary.get('processed', 0)}")
    print(f"Errors:             {summary.get('errors', 0)}")
    print(f"Test date:          {summary.get('test_date', 'N/A')}")
    
    if model_comparison:
        print(f"\n{'='*60}")
        print("MODEL COMPARISON")
        print(f"{'='*60}")
        print(f"{'Model':<20} {'Exact Match':<15} {'Category Match':<15} {'Avg Time':<10}")
        print("-" * 60)
        
        for model_key, stats in model_comparison.items():
            exact = f"{stats['exact_match_ratio']*100:.1f}%"
            category = f"{stats['category_match_ratio']*100:.1f}%"
            time_str = f"{stats['avg_response_time']:.2f}s" if stats['avg_response_time'] else "N/A"
            print(f"{model_key:<20} {exact:<15} {category:<15} {time_str:<10}")
    
    print(f"{'='*60}")


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Test matière classification on documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a single file
  python matiere_tester.py --file path/to/document.pdf
  
  # Test all documents in a folder
  python matiere_tester.py --folder path/to/folder
  
  # Test with all models for comparison
  python matiere_tester.py --folder path/to/folder --compare-models
  
  # Test from MinIO bucket
  python matiere_tester.py --bucket my-bucket --prefix documents/
  
  # Save results to a specific file
  python matiere_tester.py --folder path/to/folder -o results.json
        """
    )
    
    # Input sources (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--file", "-f",
        help="Path to a single file to test"
    )
    source_group.add_argument(
        "--folder", "-d",
        help="Path to a folder containing documents to test"
    )
    source_group.add_argument(
        "--bucket", "-b",
        help="MinIO bucket name to test documents from"
    )
    
    # Options
    parser.add_argument(
        "--prefix", "-p",
        default="",
        help="Prefix for bucket objects (used with --bucket)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to save JSON results (default: test_results.json)"
    )
    parser.add_argument(
        "--compare-models", "-c",
        action="store_true",
        help="Test all available LLM models for comparison"
    )
    parser.add_argument(
        "--models", "-m",
        nargs="+",
        choices=list(MODELS.keys()),
        default=["default"],
        help="Specific models to test (default: default)"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Search subfolders recursively (used with --folder)"
    )
    parser.add_argument(
        "--extensions", "-e",
        nargs="+",
        default=[".pdf", ".txt"],
        help="File extensions to process (default: .pdf .txt)"
    )
    parser.add_argument(
        "--nomenclature",
        help="Path to custom nomenclature ACTES file"
    )
    parser.add_argument(
        "--minio-endpoint",
        default=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        help="MinIO server endpoint"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output"
    )
    
    args = parser.parse_args()
    
    # Check HF_TOKEN
    if not HF_TOKEN:
        print("\n⚠️  Warning: HF_TOKEN environment variable not set")
        print("   LLM classification will be disabled")
        print("   Set HF_TOKEN in your .env file or environment")
        print()
    
    # Initialize tester
    tester = MatiereTester(
        nomenclature_path=args.nomenclature,
        minio_endpoint=args.minio_endpoint if args.bucket else None
    )
    
    # Determine models to test
    test_models = list(MODELS.keys()) if args.compare_models else args.models
    
    # Run tests
    results = None
    
    if args.file:
        if args.compare_models:
            results = tester.compare_models(args.file, source_type="file")
        else:
            # For single file without compare, wrap in statistics
            file_result = tester.test_file(args.file, test_models=test_models)
            results = tester._calculate_statistics([file_result], test_models)
    
    elif args.folder:
        if args.compare_models:
            results = tester.compare_models(args.folder, source_type="folder")
        else:
            results = tester.test_folder(
                args.folder,
                test_models=test_models,
                extensions=args.extensions,
                recursive=args.recursive
            )
    
    elif args.bucket:
        if args.compare_models:
            results = tester.compare_models(
                args.prefix,
                source_type="bucket",
                bucket_name=args.bucket
            )
        else:
            results = tester.test_bucket(
                args.bucket,
                prefix=args.prefix,
                test_models=test_models,
                extensions=args.extensions
            )
    
    if results:
        # Print summary
        if not args.quiet:
            print_summary(results)
        
        # Save results
        output_path = args.output or "test_results.json"
        save_results(results, output_path)
        
        # Return appropriate exit code
        if results.get("error"):
            sys.exit(1)
        
        summary = results.get("summary", {})
        if summary.get("errors", 0) > 0:
            sys.exit(2)  # Some documents had errors
        
        sys.exit(0)


if __name__ == "__main__":
    main()
