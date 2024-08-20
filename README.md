
# Chat with Document AI

This project allows you to upload a document and then interact with an AI chatbot that uses the content of the document to answer your questions. You can also view the chat history.

## How to Run

1. **Install dependencies:**

   First, install the required dependencies by running:
   ```bash
   pip install -r requirements.txt
   ```

   **Create a config.py File**
   ```bash
   # config.py
   MONGO_URI = 'mongodb://localhost:27017/hahga'
   DATABASE_NAME = 'momentum'
   SECRET_KEY = 'your_secret_key'
   VECTOR_DB_PATH = './vectors'
   GEMINI_API_KEY = 'dsa12weqe123asd123d213'
   ```

2. **Run the application:**

   Start the Flask app by running:
   ```bash
   python app.py
   ```

3. **Access the application:**

   Open your browser and go to:
   ```
   http://localhost:5000
   ```

## APIs

### 1. **Upload Document API**

- **URL:** `/api/documents/process`
- **Method:** `POST`
- **Description:** Upload a document (PDF, DOCX, TXT), and the app will process it and store its content. Returns a unique `asset_id`.

- **Request Example:**
   ```bash
   curl -X POST http://localhost:5000/api/documents/process -F "file=@/path/to/document.pdf"
   ```

- **Response Example:**
   ```json
   {
     "asset_id": "123e4567-e89b-12d3-a456-426614174000"
   }
   ```

### 2. **Start Chat API**

- **URL:** `/api/chat/start`
- **Method:** `POST`
- **Description:** Start a new chat using an existing document by providing its `asset_id`. Returns a `chat_thread_id`.

- **Request Example:**
   ```bash
   curl -X POST http://localhost:5000/api/chat/start -H "Content-Type: application/json" -d '{"asset_id": "123e4567-e89b-12d3-a456-426614174000"}'
   ```

- **Response Example:**
   ```json
   {
     "chat_thread_id": "789e1234-e56b-78d9-c012-3456789abcd"
   }
   ```

### 3. **Send Message to Chat API**

- **URL:** `/api/chat/message`
- **Method:** `POST`
- **Description:** Send a message to the chatbot. The AI will respond using the document content related to the query.

- **Request Example:**
   ```bash
   curl -X POST http://localhost:5000/api/chat/message -H "Content-Type: application/json" -d '{"chat_thread_id": "789e1234-e56b-78d9-c012-3456789abcd", "message": "What is in document?"}'
   ```

- **Response Example:**
   ```json
   {
     "response": "Document says a lot about sales and engagement."
   }
   ```






