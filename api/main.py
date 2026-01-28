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


# Enum for presence filter
class PresenceFilter(str, Enum):
    present = "present"
    absent = "absent"
    any = "any"


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


def _build_person_query(person_name: str, presence: PresenceFilter) -> dict:
    """
    Build MongoDB query for person filtering.
    
    People are stored as objects with fields: civilite, nom, prenom
    We search in the 'nom' field (case-insensitive, partial match).
    For membres_absents, we ignore the 'procuration' sub-field.
    """
    name_regex = {"$regex": person_name, "$options": "i"}
    
    if presence == PresenceFilter.present:
        return {"full_metadata.membres_presents.nom": name_regex}
    elif presence == PresenceFilter.absent:
        return {"full_metadata.membres_absents.nom": name_regex}
    else:  # any
        return {
            "$or": [
                {"full_metadata.membres_presents.nom": name_regex},
                {"full_metadata.membres_absents.nom": name_regex}
            ]
        }


@app.get("/metadata", tags=["Metadata"])
def list_metadata(
    bucket: Optional[str] = None,
    format: MetadataFormat = MetadataFormat.full,
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD ou DD/MM/YYYY)"),
    date_to: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD ou DD/MM/YYYY)"),
    date_exact: Optional[str] = Query(None, description="Date exacte (YYYY-MM-DD ou DD/MM/YYYY)"),
    person: Optional[str] = Query(None, description="Nom de la personne à rechercher"),
    presence: PresenceFilter = Query(PresenceFilter.any, description="Filtrer par présence/absence"),
    skip: int = 0,
    limit: int = 50
):
    """
    Liste les métadonnées extraites des délibérations.
    
    - **bucket**: Filtrer par bucket MinIO source
    - **format**: Format de sortie (full, complete, scdl)
    - **date_from**: Date de début pour filtrer (YYYY-MM-DD)
    - **date_to**: Date de fin pour filtrer (YYYY-MM-DD)
    - **date_exact**: Date exacte pour filtrer (YYYY-MM-DD)
    - **person**: Nom de la personne à rechercher dans les membres
    - **presence**: Filtrer par présence (present/absent/any)
    - **skip**: Nombre d'entrées à ignorer (pagination)
    - **limit**: Nombre maximum d'entrées à retourner
    """
    query = {}
    if bucket:
        query["bucket"] = bucket
    
    # Add date filter
    date_query = _build_date_query(date_from, date_to, date_exact)
    if date_query:
        query.update(date_query)
    
    # Add person filter
    if person:
        person_query = _build_person_query(person, presence)
        if "$and" in query:
            query["$and"].append(person_query)
        elif "$or" in query:
            query = {"$and": [query, person_query]}
        else:
            query.update(person_query)
    
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
    return docs


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


# ============== SEARCH ROUTES ==============

@app.get("/search", tags=["Search"])
def search_deliberations(
    q: str = Query(..., min_length=2, description="Terme de recherche"),
    bucket: Optional[str] = None,
    limit: int = 20
):
    """
    Recherche dans les métadonnées des délibérations.
    
    Recherche dans: objet de la délibération, nom de la collectivité, décision.
    
    - **q**: Terme de recherche (minimum 2 caractères)
    - **bucket**: Filtrer par bucket
    - **limit**: Nombre maximum de résultats
    """
    query = {
        "$or": [
            {"full_metadata.deliberation.objet": {"$regex": q, "$options": "i"}},
            {"full_metadata.collectivite.nom": {"$regex": q, "$options": "i"}},
            {"full_metadata.decision": {"$regex": q, "$options": "i"}},
            {"scdl_metadata.DELIB_OBJET": {"$regex": q, "$options": "i"}},
            {"scdl_metadata.COLL_NOM": {"$regex": q, "$options": "i"}}
        ]
    }
    
    if bucket:
        query["bucket"] = bucket
    
    docs = list(metadata_col.find(query).limit(limit))
    
    results = []
    for doc in docs:
        results.append({
            "_id": str(doc["_id"]),
            "filename": doc.get("filename"),
            "bucket": doc.get("bucket"),
            "delib_id": doc.get("full_metadata", {}).get("deliberation", {}).get("id"),
            "delib_objet": doc.get("full_metadata", {}).get("deliberation", {}).get("objet"),
            "collectivite": doc.get("full_metadata", {}).get("collectivite", {}).get("nom"),
            "date": doc.get("full_metadata", {}).get("deliberation", {}).get("date"),
            "url": doc.get("full_metadata", {}).get("deliberation", {}).get("url_document")
        })
    
    return {"count": len(results), "results": results}


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
    people = [doc["_id"] for doc in result if doc["_id"] and doc["_id"].get("nom")]
    
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
    
    # Count absences (search in nom field of membres_absents objects)
    absent_query = {**base_query, "full_metadata.membres_absents.nom": name_regex}
    absent_count = metadata_col.count_documents(absent_query)
    
    # Get total deliberations
    total_count = metadata_col.count_documents(base_query)
    
    return {
        "person": person_name,
        "bucket": bucket,
        "total_deliberations": total_count,
        "present_count": present_count,
        "absent_count": absent_count,
        "presence_rate": round(present_count / total_count * 100, 2) if total_count > 0 else 0
    }


@app.get("/metadata/people/{person_name}/deliberations", tags=["People"])
def get_person_deliberations(
    person_name: str,
    presence: PresenceFilter = PresenceFilter.any,
    bucket: Optional[str] = None,
    format: MetadataFormat = MetadataFormat.full,
    skip: int = 0,
    limit: int = 50
):
    """
    Récupère les délibérations où une personne est mentionnée.
    
    - **person_name**: Nom de la personne (recherche partielle, insensible à la casse)
    - **presence**: Filtrer par présence (present/absent/any)
    - **bucket**: Filtrer par bucket MinIO source
    - **format**: Format de sortie (full, complete, scdl)
    - **skip**: Pagination - entrées à ignorer
    - **limit**: Pagination - nombre max d'entrées
    """
    query = _build_person_query(person_name, presence)
    
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
        "presence_filter": presence,
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



