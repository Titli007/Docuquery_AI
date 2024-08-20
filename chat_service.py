from flask import Blueprint, request, jsonify
import uuid
from pymongo import MongoClient
from config import DATABASE_NAME, MONGO_URI
import chromadb

from llm_provider import GeminiProcessor

# MongoDB setup
print("Connecting to MongoDB...")
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
chat_collection = db['chat_threads']
print("Connected to MongoDB!")

# ChromaDB setup
print("Connecting to ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./vectors")
collection = chroma_client.get_collection(name="document_embeddings")
print("Connected to ChromaDB!")

# Gemini Processor setup
print("Setting up Gemini Processor...")
gemini_processor = GeminiProcessor()
print("Gemini Processor is ready!")

# Create a Blueprint for chat service
print("Creating chat service blueprint...")
chat_blueprint = Blueprint('chat', __name__)
print("Chat service blueprint created!")

@chat_blueprint.route('/api/chat/start', methods=['POST'])
def start_chat():
    print("Received request to start chat...")
    data = request.json
    asset_id = data.get('asset_id')
    print(f"Asset ID received: {asset_id}")

    if not asset_id:
        print("Error: Asset ID is required.")
        return jsonify({"error": "Asset ID is required"}), 400

    chat_thread_id = str(uuid.uuid4())
    print(f"Generated new chat thread ID: {chat_thread_id}")

    # Insert chat thread into MongoDB
    chat_collection.insert_one({"chat_thread_id": chat_thread_id, "asset_id": asset_id, "history": []})
    print(f"Chat thread {chat_thread_id} started and stored in MongoDB.")

    return jsonify({"chat_thread_id": chat_thread_id}), 201

@chat_blueprint.route('/api/chat/message', methods=['POST'])
def chat_message():
    print("Received new chat message...")
    data = request.json
    chat_thread_id = data.get('chat_thread_id')
    user_message = data.get('message')
    print(f"Chat thread ID: {chat_thread_id}, User message: {user_message}")

    # Retrieve chat thread from MongoDB
    chat_thread = chat_collection.find_one({"chat_thread_id": chat_thread_id})
    if not chat_thread:
        print("Error: Chat thread not found.")
        return jsonify({"error": "Chat thread not found"}), 404
    print(f"Chat thread {chat_thread_id} found.")

    asset_id = chat_thread['asset_id']
    print(f"Using asset ID: {asset_id} to query ChromaDB...")

    # Query top 5 documents from ChromaDB
    result = collection.query(query_texts=[user_message], n_results=5)
    documents = result['documents']
    print(f"Top 5 documents retrieved from ChromaDB. Total documents found: {len(documents)}")

    # Use Gemini LLM for RAG using the retrieved documents
    print("Generating response using Gemini LLM...")
    response = gemini_processor.generate_response(documents, user_message)
    print(f"Response generated: {response}")

    # Save message to chat history in MongoDB
    chat_collection.update_one({"chat_thread_id": chat_thread_id}, {
        "$push": {"history": {"user": user_message, "agent": response}}
    })
    print(f"Chat history updated for thread {chat_thread_id}")

    return jsonify({"response": response})

@chat_blueprint.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    print("Received request to get chat history...")
    data = request.json
    chat_thread_id = data.get('chat_thread_id')
    print(f"Chat thread ID: {chat_thread_id}")

    # Retrieve chat thread from MongoDB
    chat_thread = chat_collection.find_one({"chat_thread_id": chat_thread_id})
    if not chat_thread:
        print("Error: Chat thread not found.")
        return jsonify({"error": "Chat thread not found"}), 404
    print(f"Chat thread {chat_thread_id} found.")

    # Return chat history
    print("Returning chat history...")
    return jsonify(chat_thread['history'])
