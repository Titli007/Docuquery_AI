import os
import requests
import uuid
from pymongo import MongoClient
from some_embedding_library import create_embedding  # Replace with your actual embedding library
from pdfminer.high_level import extract_text as extract_pdf_text
import docx
from typing import List

# MongoDB setup
client = MongoClient('your_mongo_uri')
db = client['your_database_name']
documents_collection = db['documents']
collection = db['embeddings']  # ChromaDB or your vector database collection

class DocumentProcessor:
    def __init__(self):
        self.temp_dir = "/tmp"

    def download_document(self, document_link: str) -> str:
        """
        Download the document from the provided link and save it to a temporary directory.
        """
        response = requests.get(document_link)
        file_name = document_link.split("/")[-1]
        file_path = os.path.join(self.temp_dir, file_name)
        
        with open(file_path, 'wb') as file:
            file.write(response.content)
        
        return file_path

    def parse_pdf(self, file_path: str) -> List[str]:
        """
        Parse a PDF document into chunks of text.
        """
        text = extract_pdf_text(file_path)
        chunks = self.chunk_text(text)
        return chunks

    def parse_doc(self, file_path: str) -> List[str]:
        """
        Parse a Word document into chunks of text.
        """
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        text = '\n'.join(full_text)
        chunks = self.chunk_text(text)
        return chunks

    def parse_txt(self, file_path: str) -> List[str]:
        """
        Parse a plain text file into chunks of text.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        chunks = self.chunk_text(text)
        return chunks

    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Divide the text into chunks of a specified size.
        """
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    async def create_embeddings_for_chunks(self, chunks: List[str], asset_id: str) -> List[str]:
        """
        Create embeddings for each chunk and store them in the vector database.
        """
        embedding_ids = []
        for chunk in chunks:
            embedding = await create_embedding(chunk)
            
            embedding_id = str(uuid.uuid4())
            collection.insert_one({
                "embedding": embedding,
                "asset_id": asset_id,
                "chunk_id": embedding_id,
                "metadata": {"asset_id": asset_id}
            })
            
            embedding_ids.append(embedding_id)
        return embedding_ids

    async def process_document(self, document_link: str = None, file = None) -> str:
        """
        Process a document from a link or a file upload, parse its content, 
        create embeddings in chunks, and store them.
        """
        if document_link:
            file_path = self.download_document(document_link)
        elif file:
            file_name = file.filename
            file_path = os.path.join(self.temp_dir, file_name)
            file.save(file_path)
        else:
            raise ValueError("Either a document link or a file must be provided.")

        # Get file type
        file_type = os.path.splitext(file_path)[1][1:]

        # Generate a unique asset ID
        asset_id = str(uuid.uuid4())

        # Create document entry in MongoDB
        document = {
            "file_path": file_path,
            "file_type": file_type,
            "asset_id": asset_id
        }
        result = documents_collection.insert_one(document)

        # Parse the document and divide it into chunks
        if file_type == "pdf":
            chunks = self.parse_pdf(file_path)
        elif file_type in ["doc", "docx"]:
            chunks = self.parse_doc(file_path)
        elif file_type == "txt":
            chunks = self.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Create embeddings for each chunk and store them
        embedding_ids = await self.create_embeddings_for_chunks(chunks, asset_id)

        # Update document with embedding IDs
        documents_collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"embedding_ids": embedding_ids}}
        )

        return asset_id