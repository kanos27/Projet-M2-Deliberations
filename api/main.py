import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

app = FastAPI(title="Délibérations API")

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
