"""
Testeur de complétude des champs de métadonnées.

Ce script analyse les sorties d'extraction de métadonnées et génère
des statistiques de complétude pour chaque champ, au format JSON.

Usage:
    python test_completeness.py [--source SOURCE] [--output FILE] [--limit N]

Options:
    --source SOURCE  Source des données: 'templates', 'mongodb', ou chemin vers un fichier JSON
    --output FILE    Fichier JSON de sortie (défaut: template/completeness_stats.json)
    --limit N        Nombre max de documents à analyser depuis MongoDB (défaut: tous)
    --bucket NAME    Nom du bucket MinIO pour filtrer les métadonnées MongoDB (défaut: tous)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from pymongo import MongoClient

from extractors.orchestrator import DeliberationOrchestrator

# Configuration MongoDB (même que dans orchestrator.py)
MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin:admin@localhost:27017")


def is_field_complete(value: Any) -> bool:
    """
    Vérifie si un champ est considéré comme "complet" (non vide).
    
    Rules:
    - None -> False
    - "" (string vide) -> False
    - [] (liste vide) -> False
    - {} (dict vide) -> False
    - {"key": ""} (dict avec valeurs vides) -> dépend du contexte
    - 0 -> True (zéro est une valeur valide)
    - False -> True (False est une valeur valide)
    """
    if value is None:
        return False
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        # Un dict est complet s'il a au moins une valeur non vide
        return any(is_field_complete(v) for v in value.values())
    # Pour les nombres et booléens, toute valeur est considérée comme complète
    return True


def get_field_completeness(value: Any) -> dict:
    """
    Calcule la complétude détaillée d'un champ.
    
    Returns:
        dict avec:
        - complete: bool
        - value_preview: aperçu de la valeur (tronqué si trop long)
        - type: type de la valeur
    """
    result = {
        "complete": is_field_complete(value),
        "type": type(value).__name__,
        "value_preview": None
    }
    
    if value is None:
        result["value_preview"] = "null"
    elif isinstance(value, str):
        if len(value) > 100:
            result["value_preview"] = value[:100] + "..."
        else:
            result["value_preview"] = value or "(empty string)"
    elif isinstance(value, list):
        result["value_preview"] = f"[{len(value)} items]"
    elif isinstance(value, dict):
        result["value_preview"] = f"{{...}} ({len(value)} keys)"
    else:
        result["value_preview"] = str(value)
    
    return result


def analyze_metadata(metadata: dict) -> dict:
    """
    Analyse un dictionnaire de métadonnées et calcule les statistiques de complétude.
    
    Returns:
        dict avec:
        - fields: dict de chaque champ avec sa complétude
        - summary: statistiques globales
    """
    fields_analysis = {}
    
    def analyze_recursive(data: dict, prefix: str = ""):
        """Analyse récursivement les champs imbriqués."""
        for key, value in data.items():
            field_path = f"{prefix}.{key}" if prefix else key
            
            # Analyser ce champ
            field_info = get_field_completeness(value)
            fields_analysis[field_path] = field_info
            
            # Si c'est un dict, analyser les sous-champs
            if isinstance(value, dict) and value:
                analyze_recursive(value, field_path)
    
    analyze_recursive(metadata)
    
    # Calculer les statistiques globales
    total_fields = len(fields_analysis)
    complete_fields = sum(1 for f in fields_analysis.values() if f["complete"])
    
    # Grouper par catégorie principale
    categories = {}
    for field_path, info in fields_analysis.items():
        category = field_path.split(".")[0]
        if category not in categories:
            categories[category] = {"total": 0, "complete": 0}
        categories[category]["total"] += 1
        if info["complete"]:
            categories[category]["complete"] += 1
    
    # Calculer les pourcentages par catégorie
    category_stats = {}
    for cat, stats in categories.items():
        pct = (stats["complete"] / stats["total"] * 100) if stats["total"] > 0 else 0
        category_stats[cat] = {
            "complete": stats["complete"],
            "total": stats["total"],
            "percentage": round(pct, 1)
        }
    
    return {
        "fields": fields_analysis,
        "summary": {
            "total_fields": total_fields,
            "complete_fields": complete_fields,
            "completeness_percentage": round(complete_fields / total_fields * 100, 1) if total_fields > 0 else 0,
            "by_category": category_stats
        }
    }


def analyze_multiple_documents(documents: list, source_name: str = "unknown") -> dict:
    """
    Analyse plusieurs documents et calcule les statistiques agrégées.
    
    Args:
        documents: Liste des métadonnées à analyser
        source_name: Nom de la source (pour les métadonnées du rapport)
    
    Returns:
        dict avec:
        - metadata: informations sur l'analyse
        - per_document: statistiques par document
        - aggregate: statistiques globales sur tous les documents
        - field_coverage: pour chaque champ, % de documents où il est complet
    """
    per_document = []
    field_counts = {}
    
    for i, doc in enumerate(documents):
        doc_analysis = analyze_metadata(doc)
        # Obtenir le nom du document depuis différentes sources possibles
        doc_name = (
            doc.get("_metadata", {}).get("source_file") or
            doc.get("deliberation", {}).get("numero") or 
            doc.get("source", {}).get("fichier") or 
            doc.get("_mongodb_info", {}).get("filename") or
            f"doc_{i+1}"
        )
        
        per_document.append({
            "name": str(doc_name),
            "summary": doc_analysis["summary"],
            "fields": doc_analysis["fields"]
        })
        
        # Compter les champs complets pour l'agrégation
        for field_path, info in doc_analysis["fields"].items():
            if field_path not in field_counts:
                field_counts[field_path] = {"total": 0, "complete": 0}
            field_counts[field_path]["total"] += 1
            if info["complete"]:
                field_counts[field_path]["complete"] += 1
    
    # Calculer la couverture par champ
    field_coverage = {}
    for field_path, counts in field_counts.items():
        pct = (counts["complete"] / counts["total"] * 100) if counts["total"] > 0 else 0
        field_coverage[field_path] = {
            "documents_with_field": counts["complete"],
            "total_documents": counts["total"],
            "coverage_percentage": round(pct, 1)
        }
    
    # Trier par couverture (moins couverts en premier)
    field_coverage_sorted = dict(sorted(
        field_coverage.items(),
        key=lambda x: x[1]["coverage_percentage"]
    ))
    
    # Statistiques agrégées
    total_complete = sum(d["summary"]["complete_fields"] for d in per_document)
    total_fields = sum(d["summary"]["total_fields"] for d in per_document)
    
    return {
        "metadata": {
            "source": source_name,
            "analysis_date": datetime.now().isoformat(),
            "version": "2.0.0"
        },
        "per_document": per_document,
        "aggregate": {
            "total_documents": len(documents),
            "total_fields_analyzed": total_fields,
            "total_complete_fields": total_complete,
            "overall_completeness": round(total_complete / total_fields * 100, 1) if total_fields > 0 else 0
        },
        "field_coverage": field_coverage_sorted
    }


def extract_from_templates(template_dir: str) -> list:
    """
    Extrait les métadonnées des fichiers template .txt.
    
    Args:
        template_dir: chemin vers le répertoire contenant les fichiers .txt
    
    Returns:
        liste des métadonnées extraites
    """
    results = []
    template_path = Path(template_dir)
    
    if not template_path.exists():
        print(f"Erreur: le répertoire {template_dir} n'existe pas")
        return results
    
    txt_files = list(template_path.glob("*.txt"))
    
    # Filtrer les fichiers qui ne sont pas des délibérations
    excluded = ["nomenclature_actes.txt"]
    txt_files = [f for f in txt_files if f.name not in excluded]
    
    print(f"Analyse de {len(txt_files)} fichiers template...")
    
    # Créer un orchestrateur en mode local (sans MinIO/MongoDB)
    orchestrator = DeliberationOrchestrator(local_mode=True)
    
    for txt_file in txt_files:
        print(f"  - {txt_file.name}...")
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Utiliser la méthode d'extraction de l'orchestrateur
            metadata = orchestrator._extract_metadata_from_text(text, txt_file.name)
            
            results.append(metadata)
            
        except Exception as e:
            print(f"    Erreur: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return results


def fetch_from_mongodb(limit: Optional[int] = None, bucket: Optional[str] = None) -> list:
    """
    Récupère les métadonnées depuis MongoDB.
    
    Args:
        limit: Nombre max de documents à récupérer (None = tous)
        bucket: Filtrer par bucket MinIO (None = tous les buckets)
    
    Returns:
        liste des métadonnées (full_metadata) stockées dans MongoDB
    """
    results = []
    
    print(f"Connexion à MongoDB: {MONGO_URL}...")
    
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        # Test de connexion
        client.admin.command('ping')
        print("  Connexion établie.")
        
        db = client["deliberations"]
        metadata_col = db["metadata"]
        
        # Construire la requête
        query = {}
        if bucket:
            query["bucket"] = bucket
        
        # Compter le total
        total_count = metadata_col.count_documents(query)
        print(f"  {total_count} document(s) trouvé(s) dans la collection 'metadata'")
        
        if bucket:
            print(f"  (filtré par bucket: {bucket})")
        
        # Récupérer les documents
        cursor = metadata_col.find(query)
        if limit:
            cursor = cursor.limit(limit)
            print(f"  Limité à {limit} document(s)")
        
        for doc in cursor:
            # Extraire full_metadata qui contient les métadonnées complètes
            full_metadata = doc.get("full_metadata")
            if full_metadata:
                # Ajouter des infos supplémentaires depuis le document MongoDB
                full_metadata["_mongodb_info"] = {
                    "filename": doc.get("filename"),
                    "bucket": doc.get("bucket"),
                    "extracted_at": doc.get("extracted_at").isoformat() if doc.get("extracted_at") else None
                }
                results.append(full_metadata)
            else:
                print(f"    Avertissement: pas de full_metadata pour {doc.get('filename')}")
        
        client.close()
        print(f"  {len(results)} document(s) récupéré(s)")
        
    except Exception as e:
        print(f"Erreur de connexion MongoDB: {e}")
        print("Vérifiez que MongoDB est en cours d'exécution (docker-compose up)")
        return []
    
    return results


def print_summary(stats: dict):
    """Affiche un résumé des statistiques en console."""
    print("\n" + "="*60)
    print("RÉSUMÉ DE COMPLÉTUDE")
    print("="*60)
    
    if "aggregate" in stats:
        agg = stats["aggregate"]
        print(f"\nSource: {stats.get('metadata', {}).get('source', 'inconnue')}")
        print(f"Documents analysés: {agg['total_documents']}")
        print(f"Complétude globale: {agg['overall_completeness']}%")
        
        print("\n--- Champs les moins couverts (top 10) ---")
        count = 0
        for field, cov in stats["field_coverage"].items():
            if cov["coverage_percentage"] < 100:
                print(f"  {field}: {cov['coverage_percentage']}% ({cov['documents_with_field']}/{cov['total_documents']})")
                count += 1
                if count >= 10:
                    break
        
        print("\n--- Complétude par document ---")
        for doc in stats["per_document"][:20]:  # Limiter à 20 pour l'affichage
            print(f"  {doc['name']}: {doc['summary']['completeness_percentage']}%")
        if len(stats["per_document"]) > 20:
            print(f"  ... et {len(stats['per_document']) - 20} autres documents")
    else:
        summary = stats["summary"]
        print(f"\nChamps complets: {summary['complete_fields']}/{summary['total_fields']} ({summary['completeness_percentage']}%)")
        
        print("\n--- Par catégorie ---")
        for cat, cat_stats in summary["by_category"].items():
            print(f"  {cat}: {cat_stats['percentage']}% ({cat_stats['complete']}/{cat_stats['total']})")
        
        print("\n--- Champs incomplets ---")
        for field, info in stats["fields"].items():
            if not info["complete"]:
                print(f"  {field}: {info['value_preview']}")


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyse la complétude des métadonnées extraites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python test_completeness.py --source templates
  python test_completeness.py --source mongodb --limit 100
  python test_completeness.py --source mongodb --bucket larochelle-deliberations
  python test_completeness.py --source output.json
        """
    )
    parser.add_argument(
        "--source", "-s", 
        default="templates",
        help="Source: 'templates', 'mongodb', ou chemin vers fichier JSON (défaut: templates)"
    )
    parser.add_argument(
        "--output", "-o", 
        default=None,
        help="Fichier de sortie (défaut: template/completeness_stats.json)"
    )
    parser.add_argument(
        "--limit", "-l", 
        type=int, 
        default=None,
        help="Nombre max de documents depuis MongoDB"
    )
    parser.add_argument(
        "--bucket", "-b",
        default=None,
        help="Filtrer par bucket MinIO (pour MongoDB)"
    )
    
    args = parser.parse_args()
    
    # Déterminer le fichier de sortie (dans template/)
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path(__file__).parent / "template" / args.output
    else:
        output_path = Path(__file__).parent / "template" / "completeness_stats.json"
    
    # Déterminer la source des données
    source_name = args.source
    
    if args.source == "templates":
        template_dir = Path(__file__).parent / "template"
        documents = extract_from_templates(str(template_dir))
        source_name = "templates (.txt files)"
        
    elif args.source == "mongodb":
        documents = fetch_from_mongodb(limit=args.limit, bucket=args.bucket)
        source_name = f"mongodb (bucket={args.bucket or 'all'}, limit={args.limit or 'none'})"
        
    elif Path(args.source).exists():
        # Fichier JSON existant
        with open(args.source, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Supporter un seul document ou une liste
        documents = data if isinstance(data, list) else [data]
        source_name = f"file: {args.source}"
        
    else:
        print(f"Erreur: source invalide '{args.source}'")
        print("Utilisez 'templates', 'mongodb', ou un chemin vers un fichier JSON")
        return 1
    
    if not documents:
        print("Aucun document à analyser")
        return 1
    
    # Analyser
    if len(documents) == 1:
        stats = analyze_metadata(documents[0])
        # Ajouter les métadonnées pour un seul document aussi
        stats["metadata"] = {
            "source": source_name,
            "analysis_date": datetime.now().isoformat(),
            "version": "2.0.0"
        }
    else:
        stats = analyze_multiple_documents(documents, source_name)
    
    # S'assurer que le répertoire de sortie existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\nStatistiques sauvegardées dans: {output_path}")
    
    # Afficher le résumé
    print_summary(stats)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
