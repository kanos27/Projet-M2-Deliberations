import os
import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from fastapi import Query

app = FastAPI(
    title="Délibérations API",
    description="API pour accéder aux documents et métadonnées des délibérations",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin:admin@localhost:27017")
client = MongoClient(MONGO_URL)
db = client["deliberations"]
documents_col = db["documents"]
metadata_col = db["metadata"]


# Enum for metadata format
class MetadataFormat(str, Enum):
    full = "full"
    complete = "complete"
    scdl = "scdl"


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class DocumentBase(BaseModel):
    filename: str
    title: Optional[str] = None
    source: str
    bucket: str
    url: Optional[str] = None
    metadata: Optional[dict] = None


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    id: str = Field(alias="_id")
    created_at: datetime

    class Config:
        populate_by_name = True


@app.get("/")
def root():
    return {"status": "ok", "service": "deliberations-api"}


@app.get("/documents")
def list_documents(source: Optional[str] = None, skip: int = 0, limit: int = 50):
    query = {}
    if source:
        query["source"] = source
    docs = list(documents_col.find(query).skip(skip).limit(limit))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    if not ObjectId.is_valid(doc_id):
        raise HTTPException(status_code=400, detail="Invalid document ID")
    doc = documents_col.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc["_id"] = str(doc["_id"])
    return doc


@app.post("/documents", status_code=201)
def create_document(doc: DocumentCreate):
    data = doc.model_dump()
    data["created_at"] = datetime.utcnow()
    result = documents_col.insert_one(data)
    data["_id"] = str(result.inserted_id)
    return data


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    if not ObjectId.is_valid(doc_id):
        raise HTTPException(status_code=400, detail="Invalid document ID")
    result = documents_col.delete_one({"_id": ObjectId(doc_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": doc_id}


@app.get("/sources")
def list_sources():
    sources = documents_col.distinct("source")
    return sources


# ============== METADATA ROUTES ==============

def _parse_date_filter(date_str: str) -> str:
    """Parse date string to ISO format for MongoDB query."""
    # Handle various date formats
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    elif re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        parts = date_str.split('/')
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return date_str


def _build_date_query(date_from: Optional[str], date_to: Optional[str], date_exact: Optional[str]) -> dict:
    """Build MongoDB query for date filtering."""
    if date_exact:
        parsed_date = _parse_date_filter(date_exact)
        return {
            "$or": [
                {"full_metadata.deliberation.date": parsed_date},
                {"scdl_metadata.DELIB_DATE": parsed_date}
            ]
        }
    
    date_conditions = []
    if date_from:
        parsed_from = _parse_date_filter(date_from)
        date_conditions.append({
            "$or": [
                {"full_metadata.deliberation.date": {"$gte": parsed_from}},
                {"scdl_metadata.DELIB_DATE": {"$gte": parsed_from}}
            ]
        })
    if date_to:
        parsed_to = _parse_date_filter(date_to)
        date_conditions.append({
            "$or": [
                {"full_metadata.deliberation.date": {"$lte": parsed_to}},
                {"scdl_metadata.DELIB_DATE": {"$lte": parsed_to}}
            ]
        })
    
    if date_conditions:
        return {"$and": date_conditions}
    return {}


def _build_person_query(person_name: str) -> dict:
    """
    Build MongoDB query for person filtering.
    
    People are stored as objects with fields: civilite, nom, prenom
    We search in both 'nom' and 'prenom' fields (case-insensitive, partial match).
    Searches in both membres_presents and membres_absents.
    """
    name_regex = {"$regex": person_name, "$options": "i"}
    
    return {
        "$or": [
            {"full_metadata.membres_presents.nom": name_regex},
            {"full_metadata.membres_presents.prenom": name_regex},
            {"full_metadata.membres_absents.nom": name_regex},
            {"full_metadata.membres_absents.prenom": name_regex}
        ]
    }


@app.get("/metadata", tags=["Metadata"])
def list_metadata(
    q: Optional[str] = Query(None, description="Terme de recherche (objet, collectivité, contenu, filename)"),
    bucket: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD ou DD/MM/YYYY)"),
    date_to: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD ou DD/MM/YYYY)"),
    date_exact: Optional[str] = Query(None, description="Date exacte (YYYY-MM-DD ou DD/MM/YYYY)"),
    year: Optional[str] = Query(None, description="Année (ex: 2024)"),
    vote_resultat: Optional[str] = Query(None, description="Résultat du vote (ADOPTÉE, REJETÉE, etc.)"),
    commission: Optional[str] = Query(None, description="Commission consultée"),
    rapporteur: Optional[str] = Query(None, description="Rapporteur de la délibération"),
    person: Optional[str] = Query(None, description="Nom de la personne à rechercher"),
    matiere_code: Optional[str] = Query(None, description="Code ACTES de la matière (ex: 9.1, 1.1)"),
    matiere_nom: Optional[str] = Query(None, description="Nom de la matière"),
    skip: int = 0,
    limit: int = 50
):
    """
    Recherche et liste les métadonnées extraites des délibérations.
    
    - **q**: Terme de recherche général (objet, collectivité, contenu, filename)
    - **bucket**: Filtrer par bucket MinIO source
    - **date_from**: Date de début pour filtrer (YYYY-MM-DD)
    - **date_to**: Date de fin pour filtrer (YYYY-MM-DD)
    - **date_exact**: Date exacte pour filtrer (YYYY-MM-DD)
    - **year**: Année (2023, 2024, etc.)
    - **vote_resultat**: Résultat du vote (ADOPTÉE, etc.)
    - **commission**: Commission consultée
    - **rapporteur**: Rapporteur de la délibération
    - **person**: Nom de la personne à rechercher dans les membres
    - **matiere_code**: Code ACTES de la matière (ex: 9.1, 1.1)
    - **matiere_nom**: Nom de la matière
    - **skip**: Nombre d'entrées à ignorer (pagination)
    - **limit**: Nombre maximum d'entrées à retourner
    """
    query_conditions = []

    # Text search
    if q:
        query_conditions.append({
            "$or": [
                {"full_metadata.deliberation.objet": {"$regex": q, "$options": "i"}},
                {"full_metadata.collectivite.nom": {"$regex": q, "$options": "i"}},
                {"full_metadata.decision": {"$regex": q, "$options": "i"}},
                {"full_metadata.commission_consultee.nom": {"$regex": q, "$options": "i"}},
                {"full_metadata.contenu.texte_integral": {"$regex": q, "$options": "i"}},
                {"scdl_metadata.DELIB_OBJET": {"$regex": q, "$options": "i"}},
                {"scdl_metadata.COLL_NOM": {"$regex": q, "$options": "i"}},
                {"filename": {"$regex": q, "$options": "i"}}
            ]
        })

    # Bucket filter
    if bucket:
        query_conditions.append({"bucket": bucket})

    # Date filters
    date_query = _build_date_query(date_from, date_to, date_exact)
    if date_query:
        query_conditions.append(date_query)

    # Year filter
    if year:
        query_conditions.append({
            "$or": [
                {"full_metadata.deliberation.date": {"$regex": f"^{year}"}},
                {"scdl_metadata.DELIB_DATE": {"$regex": f"^{year}"}}
            ]
        })

    # Vote resultat filter
    if vote_resultat:
        query_conditions.append({
            "full_metadata.vote.resultat": {"$regex": vote_resultat, "$options": "i"}
        })

    # Commission filter
    if commission:
        query_conditions.append({
            "full_metadata.commission_consultee.nom": {"$regex": commission, "$options": "i"}
        })

    # Rapporteur filter
    if rapporteur:
        words = rapporteur.strip().split()
        word_conditions = []
        for word in words:
            word_regex = {"$regex": word, "$options": "i"}
            word_conditions.append({
                "$or": [
                    {"full_metadata.seance.rapporteur.civilite": word_regex},
                    {"full_metadata.seance.rapporteur.nom": word_regex},
                    {"full_metadata.seance.rapporteur.prenom": word_regex}
                ]
            })
        if word_conditions:
            query_conditions.append({"$and": word_conditions})

    # Person filter
    if person:
        person_query = _build_person_query(person)
        query_conditions.append(person_query)

    # Matiere code filter (code ACTES)
    if matiere_code:
        query_conditions.append({
            "full_metadata.deliberation.matiere.code": {"$regex": f"^{matiere_code}", "$options": "i"}
        })

    # Matiere nom filter
    if matiere_nom:
        query_conditions.append({
            "full_metadata.deliberation.matiere.nom": {"$regex": matiere_nom, "$options": "i"}
        })

    # Build final query
    query = {"$and": query_conditions} if query_conditions else {}

    # Count total results
    total = metadata_col.count_documents(query)

    # Get paginated results sorted by date descending
    docs = list(metadata_col.find(query).sort("full_metadata.deliberation.date", -1).skip(skip).limit(limit))

    for doc in docs:
        doc["_id"] = str(doc["_id"])

    return {
        "total": total,
        "count": len(docs),
        "skip": skip,
        "limit": limit,
        "results": docs
    }


@app.get("/metadata/count", tags=["Metadata"])
def count_metadata(bucket: Optional[str] = None):
    """Retourne le nombre total de métadonnées."""
    query = {}
    if bucket:
        query["bucket"] = bucket
    count = metadata_col.count_documents(query)
    return {"count": count, "bucket": bucket}


@app.get("/metadata/buckets", tags=["Metadata"])
def list_metadata_buckets():
    """Liste tous les buckets ayant des métadonnées."""
    buckets = metadata_col.distinct("bucket")
    return buckets


@app.get("/metadata/filter-options", tags=["Metadata"])
def get_filter_options():
    """
    Récupère toutes les options disponibles pour les filtres de recherche.
    
    Retourne les valeurs distinctes pour:
    - vote_resultats: Résultats de vote (ADOPTÉE, REJETÉE, etc.)
    - commissions: Commissions consultées
    - collectivites: Collectivités
    - rapporteurs: Rapporteurs des délibérations
    - lieux: Lieux des séances
    - buckets: Buckets sources
    - years: Années disponibles
    - matieres: Matières avec codes ACTES
    """
    # Résultats de vote
    vote_resultats_pipeline = [
        {"$match": {"full_metadata.vote.resultat": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$full_metadata.vote.resultat"}},
        {"$sort": {"_id": 1}}
    ]
    vote_resultats = [doc["_id"] for doc in metadata_col.aggregate(vote_resultats_pipeline) if doc["_id"]]
    
    # Commissions consultées - normalisation avec $toLower pour éviter les doublons de casse
    commissions_pipeline = [
        {"$match": {"full_metadata.commission_consultee.nom": {"$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": {"$toLower": "$full_metadata.commission_consultee.nom"},
            "original": {"$first": "$full_metadata.commission_consultee.nom"}
        }},
        {"$sort": {"original": 1}}
    ]
    commissions = [doc["original"] for doc in metadata_col.aggregate(commissions_pipeline) if doc.get("original")]
    
    # Avis de commission
    avis_pipeline = [
        {"$match": {"full_metadata.commission_consultee.avis": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$full_metadata.commission_consultee.avis"}},
        {"$sort": {"_id": 1}}
    ]
    avis = [doc["_id"] for doc in metadata_col.aggregate(avis_pipeline) if doc["_id"]]
    
    # Collectivités
    collectivites_pipeline = [
        {"$match": {"full_metadata.collectivite.nom": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$full_metadata.collectivite.nom"}},
        {"$sort": {"_id": 1}}
    ]
    collectivites = [doc["_id"] for doc in metadata_col.aggregate(collectivites_pipeline) if doc["_id"]]
    
    # Rapporteurs
    rapporteurs_pipeline = [
        {"$match": {"full_metadata.seance.rapporteur.nom": {"$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": {
                "civilite": "$full_metadata.seance.rapporteur.civilite",
                "nom": "$full_metadata.seance.rapporteur.nom",
                "prenom": "$full_metadata.seance.rapporteur.prenom"
            }
        }},
        {"$sort": {"_id.nom": 1}}
    ]
    rapporteurs_raw = list(metadata_col.aggregate(rapporteurs_pipeline))
    rapporteurs = []
    for doc in rapporteurs_raw:
        r = doc["_id"]
        if r and r.get("nom"):
            parts = [r.get("civilite", ""), r.get("prenom", ""), r.get("nom", "")]
            rapporteurs.append(" ".join(p for p in parts if p).strip())
    
    # Lieux de séance
    lieux_pipeline = [
        {"$match": {"full_metadata.seance.lieu": {"$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$full_metadata.seance.lieu"}},
        {"$sort": {"_id": 1}}
    ]
    lieux = [doc["_id"] for doc in metadata_col.aggregate(lieux_pipeline) if doc["_id"]]
    
    # Années disponibles
    years_pipeline = [
        {"$match": {"full_metadata.deliberation.date": {"$ne": None, "$ne": ""}}},
        {"$project": {"year": {"$substr": ["$full_metadata.deliberation.date", 0, 4]}}},
        {"$group": {"_id": "$year"}},
        {"$sort": {"_id": -1}}
    ]
    years = [doc["_id"] for doc in metadata_col.aggregate(years_pipeline) if doc["_id"]]
    
    # Buckets
    buckets = metadata_col.distinct("bucket")
    
    # Matières (codes ACTES)
    matieres_pipeline = [
        {"$match": {"full_metadata.deliberation.matiere.code": {"$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": {
                "code": "$full_metadata.deliberation.matiere.code",
                "nom": "$full_metadata.deliberation.matiere.nom"
            }
        }},
        {"$sort": {"_id.code": 1}}
    ]
    matieres_raw = list(metadata_col.aggregate(matieres_pipeline))
    matieres = [
        {"code": doc["_id"]["code"], "nom": doc["_id"].get("nom", "")}
        for doc in matieres_raw
        if doc["_id"].get("code")
    ]
    
    return {
        "vote_resultats": vote_resultats,
        "commissions": commissions,
        "avis_commissions": avis,
        "collectivites": collectivites,
        "rapporteurs": rapporteurs,
        "lieux": lieux,
        "years": years,
        "buckets": buckets,
        "matieres": matieres
    }


@app.get("/metadata/by-filename/{filename}", tags=["Metadata"])
def get_metadata_by_filename(
    filename: str,
    bucket: Optional[str] = None,
    format: MetadataFormat = MetadataFormat.full
):
    """
    Récupère les métadonnées par nom de fichier.
    
    - **filename**: Nom du fichier PDF source
    - **bucket**: Bucket MinIO (optionnel, utile si même fichier dans plusieurs buckets)
    - **format**: Format de sortie (full, complete, scdl)
    """
    query = {"filename": filename}
    if bucket:
        query["bucket"] = bucket
    
    doc = metadata_col.find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Metadata not found for this filename")
    
    doc["_id"] = str(doc["_id"])
    
    if format == MetadataFormat.complete:
        doc.pop("scdl_metadata", None)
    elif format == MetadataFormat.scdl:
        doc.pop("full_metadata", None)
    
    return doc


@app.get("/metadata/search/by-delib-id", tags=["Metadata"])
def search_metadata_by_delib_id(
    delib_id: str = Query(..., description="Identifiant de la délibération (ex: 251215_01)"),
    format: MetadataFormat = MetadataFormat.full
):
    """
    Recherche les métadonnées par identifiant de délibération.
    
    - **delib_id**: Identifiant de la délibération (partie numérique, ex: 251215_01)
    - **format**: Format de sortie (full, complete, scdl)
    """
    # Search in full_metadata.deliberation.id
    query = {
        "$or": [
            {"full_metadata.deliberation.id": {"$regex": delib_id, "$options": "i"}},
            {"scdl_metadata.DELIB_ID": {"$regex": delib_id, "$options": "i"}}
        ]
    }
    
    docs = list(metadata_col.find(query))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        if format == MetadataFormat.complete:
            doc.pop("scdl_metadata", None)
        elif format == MetadataFormat.scdl:
            doc.pop("full_metadata", None)
    
    return docs


# ============== DOCUMENT LOOKUP ROUTES ==============

@app.get("/documents/by-url", tags=["Documents"])
def get_document_by_url(url: str = Query(..., description="URL du document PDF")):
    """
    Récupère un document par son URL d'origine.
    
    - **url**: URL complète du document PDF
    """
    doc = documents_col.find_one({"url": url})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found for this URL")
    doc["_id"] = str(doc["_id"])
    return doc


@app.get("/documents/by-filename/{filename}", tags=["Documents"])
def get_document_by_filename(
    filename: str,
    bucket: Optional[str] = None
):
    """
    Récupère un document par son nom de fichier.
    
    - **filename**: Nom du fichier PDF
    - **bucket**: Bucket MinIO (optionnel)
    """
    query = {"filename": filename}
    if bucket:
        query["bucket"] = bucket
    
    doc = documents_col.find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc["_id"] = str(doc["_id"])
    return doc


@app.get("/documents/{doc_id}/metadata", tags=["Documents"])
def get_document_with_metadata(
    doc_id: str,
    format: MetadataFormat = MetadataFormat.full
):
    """
    Récupère un document avec ses métadonnées associées.
    
    - **doc_id**: ID MongoDB du document
    - **format**: Format des métadonnées (full, complete, scdl)
    """
    if not ObjectId.is_valid(doc_id):
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    doc = documents_col.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc["_id"] = str(doc["_id"])
    
    # Find associated metadata
    metadata = metadata_col.find_one({
        "filename": doc["filename"],
        "bucket": doc["bucket"]
    })
    
    if metadata:
        metadata["_id"] = str(metadata["_id"])
        if format == MetadataFormat.complete:
            metadata.pop("scdl_metadata", None)
        elif format == MetadataFormat.scdl:
            metadata.pop("full_metadata", None)
        doc["extracted_metadata"] = metadata
    else:
        doc["extracted_metadata"] = None
    
    return doc





# ============== PEOPLE ROUTES ==============

@app.get("/metadata/people", tags=["People"])
def list_all_people(bucket: Optional[str] = None):
    """
    Liste toutes les personnes uniques mentionnées dans les métadonnées.
    
    Retourne la liste des personnes présentes et absentes dans toutes les délibérations.
    Chaque personne est identifiée par son nom, prénom et civilité.
    
    - **bucket**: Filtrer par bucket MinIO source
    """
    query = {}
    if bucket:
        query["bucket"] = bucket
    
    # Aggregate all unique people from membres_presents and membres_absents
    # People are stored as objects with fields: civilite, nom, prenom
    # For membres_absents, we exclude the 'procuration' field
    pipeline = [
        {"$match": query},
        {
            "$project": {
                "presents": {"$ifNull": ["$full_metadata.membres_presents", []]},
                "absents": {
                    "$map": {
                        "input": {"$ifNull": ["$full_metadata.membres_absents", []]},
                        "as": "absent",
                        "in": {
                            "civilite": "$$absent.civilite",
                            "nom": "$$absent.nom",
                            "prenom": "$$absent.prenom"
                        }
                    }
                }
            }
        },
        {
            "$project": {
                "all_people": {"$setUnion": ["$presents", "$absents"]}
            }
        },
        {"$unwind": "$all_people"},
        {
            "$group": {
                "_id": {
                    "civilite": "$all_people.civilite",
                    "nom": "$all_people.nom",
                    "prenom": "$all_people.prenom"
                }
            }
        },
        {"$sort": {"_id.nom": 1, "_id.prenom": 1}}
    ]
    
    result = list(metadata_col.aggregate(pipeline))
    
    # Clean and deduplicate people:
    # - Remove names ending with isolated capital letters with accents (À, È, etc.)
    # - Normalize spaces in compound names (Jean- Claude -> Jean-Claude)
    import re
    cleaned_people = {}
    
    for doc in result:
        person = doc.get("_id")
        if not person or not person.get("nom"):
            continue
        
        nom = person.get("nom", "").strip()
        prenom = person.get("prenom", "").strip()
        civilite = person.get("civilite", "").strip()
        
        # Skip if name contains newlines or ends with isolated accented capital (À, È, Ì, etc.)
        if '\n' in nom or '\r' in nom or re.search(r'\s+[À-Ÿ]$', nom):
            continue
        if '\n' in prenom or '\r' in prenom or re.search(r'\s+[À-Ÿ]$', prenom):
            continue
            
        # Normalize compound names: "Jean- Claude" -> "Jean-Claude"
        prenom = re.sub(r'-\s+', '-', prenom)
        nom = re.sub(r'-\s+', '-', nom)
        
        # Use (nom, prenom) as key for deduplication
        key = (nom.upper(), prenom.upper())
        if key not in cleaned_people:
            cleaned_people[key] = {
                "civilite": civilite,
                "nom": nom,
                "prenom": prenom
            }
    
    people = list(cleaned_people.values())
    people.sort(key=lambda p: (p.get("nom", "").upper(), p.get("prenom", "").upper()))
    
    return {
        "count": len(people),
        "people": people
    }


@app.get("/metadata/people/{person_name}/stats", tags=["People"])
def get_person_stats(
    person_name: str,
    bucket: Optional[str] = None
):
    """
    Récupère les statistiques de présence/absence d'une personne.
    
    Note: absent_count est null car les données membres_absents ne sont pas 
    extraites des PDFs. Seules les présences sont comptabilisées.
    
    - **person_name**: Nom de la personne (recherche partielle, insensible à la casse)
    - **bucket**: Filtrer par bucket MinIO source
    """
    base_query = {}
    if bucket:
        base_query["bucket"] = bucket
    
    name_regex = {"$regex": person_name, "$options": "i"}
    
    # Count présences (search in nom field of membres_presents objects)
    present_query = {**base_query, "full_metadata.membres_presents.nom": name_regex}
    present_count = metadata_col.count_documents(present_query)
    
    # Get total deliberations
    total_count = metadata_col.count_documents(base_query)
    
    return {
        "person": person_name,
        "bucket": bucket,
        "total_deliberations": total_count,
        "present_count": present_count,
        "absent_count": None,  # Not extracted from PDFs
        "presence_rate": round(present_count / total_count * 100, 2) if total_count > 0 else 0
    }


@app.get("/metadata/people/{person_name}/deliberations", tags=["People"])
def get_person_deliberations(
    person_name: str,
    bucket: Optional[str] = None,
    format: MetadataFormat = MetadataFormat.full,
    skip: int = 0,
    limit: int = 50
):
    """
    Récupère les délibérations où une personne est mentionnée.
    
    - **person_name**: Nom de la personne (recherche partielle, insensible à la casse)
    - **bucket**: Filtrer par bucket MinIO source
    - **format**: Format de sortie (full, complete, scdl)
    - **skip**: Pagination - entrées à ignorer
    - **limit**: Pagination - nombre max d'entrées
    """
    query = _build_person_query(person_name)
    
    if bucket:
        query["bucket"] = bucket
    
    # Define projection based on format
    projection = {"_id": 1, "filename": 1, "bucket": 1, "extracted_at": 1}
    if format == MetadataFormat.full:
        projection["full_metadata"] = 1
        projection["scdl_metadata"] = 1
    elif format == MetadataFormat.complete:
        projection["full_metadata"] = 1
    elif format == MetadataFormat.scdl:
        projection["scdl_metadata"] = 1
    
    docs = list(metadata_col.find(query, projection).skip(skip).limit(limit))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    
    total = metadata_col.count_documents(query)
    
    return {
        "person": person_name,
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": docs
    }


# NOTE: This route must be AFTER all specific /metadata/... routes
# to avoid matching paths like /metadata/people as metadata_id
@app.get("/metadata/{metadata_id}", tags=["Metadata"])
def get_metadata_by_id(
    metadata_id: str,
    format: MetadataFormat = MetadataFormat.full
):
    """
    Récupère les métadonnées par leur ID MongoDB.
    
    - **metadata_id**: ID MongoDB de l'entrée metadata
    - **format**: Format de sortie (full, complete, scdl)
    """
    if not ObjectId.is_valid(metadata_id):
        raise HTTPException(status_code=400, detail="Invalid metadata ID")
    
    doc = metadata_col.find_one({"_id": ObjectId(metadata_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    doc["_id"] = str(doc["_id"])
    
    # Filter based on format
    if format == MetadataFormat.complete:
        doc.pop("scdl_metadata", None)
    elif format == MetadataFormat.scdl:
        doc.pop("full_metadata", None)
    
    return doc



