import getpass
import os
from langchain_google_genai import ChatGoogleGenerativeAI

from config import GEMINI_API_KEY

os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
class GeminiProcessor:
    def __init__(self):
        pass
        
    def generate_response(self, documents: list, user_query: str) -> str:
        print("Inside generate response")
        # Combine documents and query into a single prompt
        print(documents[0])
        context = " ".join([doc[0] for doc in documents])
        print(f"Context is {context}")
        prompt = f"Given the following context:\n{context}\nAnswer the following query: {user_query}"
        print(prompt)
        # Make a GPT call using LangChain
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        result = llm.invoke(prompt)
        return result.content