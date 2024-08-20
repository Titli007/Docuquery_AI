import os
import uuid
from pymongo import MongoClient
import chromadb
from pdfminer.high_level import extract_text as extract_pdf_text
import docx
from typing import List, Tuple
from config import MONGO_URI, DATABASE_NAME, VECTOR_DB_PATH

# MongoDB setup
print("Connecting to MongoDB...")
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
documents_collection = db['documents']
print("Connected to MongoDB!")

# ChromaDB setup
print("Connecting to ChromaDB...")
chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
collection = chroma_client.get_or_create_collection(name="document_embeddings")
print("Connected to ChromaDB!")

class DocumentProcessor:
    def __init__(self):
        self.temp_dir = "./tmp"
        print("Creating temporary directory if not exists...")
        os.makedirs(self.temp_dir, exist_ok=True)
        print(f"Temporary directory created at {self.temp_dir}")

    def parse_pdf(self, file_path: str) -> str:
        print(f"Parsing PDF file at {file_path}...")
        text = extract_pdf_text(file_path)
        print(f"Parsed PDF text length: {len(text)}")
        return text

    def parse_doc(self, file_path: str) -> str:
        print(f"Parsing DOC/DOCX file at {file_path}...")
        doc = docx.Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        print(f"Parsed DOC/DOCX text length: {len(text)}")
        return text

    def parse_txt(self, file_path: str) -> str:
        print(f"Parsing TXT file at {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        print(f"Parsed TXT text length: {len(text)}")
        return text

    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        print(f"Chunking text into pieces of {chunk_size} characters each...")
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        print(f"Total chunks created: {len(chunks)}")
        return chunks

    def extract_metadata(self, file_path: str) -> dict:
        print(f"Extracting metadata from file at {file_path}...")
        file_stats = os.stat(file_path)
        metadata = {
            "file_size": file_stats.st_size,
            "creation_date": file_stats.st_ctime,
            "last_modified": file_stats.st_mtime,
            "file_name": os.path.basename(file_path),
            "file_path": file_path
        }
        print(f"Extracted metadata: {metadata}")
        return metadata

    def summarize_text(self, text: str) -> str:
        print("Summarizing text...")
        summary = text[:1000] + '...' if len(text) > 1000 else text
        print(f"Summary length: {len(summary)}")
        return summary

    def process_document(self, file_path: str, file_type: str) -> str:
        print("Processing document...")
        # Generate a unique asset ID
        asset_id = str(uuid.uuid4())
        print(f"Generated asset ID: {asset_id}")

        # Parse the document
        if file_type == "pdf":
            text = self.parse_pdf(file_path)
        elif file_type in ["doc", "docx"]:
            text = self.parse_doc(file_path)
        elif file_type == "txt":
            text = self.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Chunk the text into smaller pieces for efficient querying
        chunks = self.chunk_text(text)

        # Store embeddings for each chunk
        print("Storing chunks in ChromaDB...")
        chunk_ids = []
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            collection.add(documents=[chunk], ids=[chunk_id], metadatas=[{"asset_id": asset_id, "chunk_id": chunk_id}])
            print(f"Stored chunk with ID: {chunk_id}")
            chunk_ids.append(chunk_id)

        # Extract and store document metadata
        print("Storing document metadata in MongoDB...")
        metadata = self.extract_metadata(file_path)
        metadata.update({
            "asset_id": asset_id,
            "chunk_ids": chunk_ids,
            "summary": self.summarize_text(text)
        })
        documents_collection.insert_one(metadata)
        print(f"Document metadata stored with asset ID: {asset_id}")

        return asset_id

    def retrieve_document(self, asset_id: str) -> Tuple[str, List[str], dict]:
        print(f"Retrieving document with asset ID: {asset_id}...")
        document = documents_collection.find_one({"asset_id": asset_id})
        if not document:
            raise ValueError(f"Document with asset ID {asset_id} not found.")
        print("Document found!")

        chunk_ids = document.get("chunk_ids", [])
        print(f"Retrieving chunks with IDs: {chunk_ids}")
        chunks = collection.get(ids=chunk_ids)["documents"]
        print(f"Total chunks retrieved: {len(chunks)}")

        return document.get("file_name", ""), chunks, document

    def update_document(self, asset_id: str, new_file_path: str) -> str:
        print(f"Updating document with asset ID: {asset_id}...")
        
        # Parse the new document content
        file_type = os.path.splitext(new_file_path)[1][1:]
        if file_type == "pdf":
            text = self.parse_pdf(new_file_path)
        elif file_type in ["doc", "docx"]:
            text = self.parse_doc(new_file_path)
        elif file_type == "txt":
            text = self.parse_txt(new_file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Chunk the new text
        chunks = self.chunk_text(text)

        # Update the embeddings in ChromaDB
        print("Storing updated chunks in ChromaDB...")
        chunk_ids = []
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            collection.add(documents=[chunk], ids=[chunk_id], metadatas=[{"asset_id": asset_id, "chunk_id": chunk_id}])
            print(f"Stored updated chunk with ID: {chunk_id}")
            chunk_ids.append(chunk_id)

        # Update document metadata in MongoDB
        print("Updating document metadata in MongoDB...")
        metadata = self.extract_metadata(new_file_path)
        metadata.update({
            "chunk_ids": chunk_ids,
            "summary": self.summarize_text(text),
            "last_modified": os.stat(new_file_path).st_mtime
        })
        documents_collection.update_one({"asset_id": asset_id}, {"$set": metadata})
        print(f"Document updated successfully with asset ID: {asset_id}")

        return asset_id
