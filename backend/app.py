import os
from flask import Flask, request, jsonify
import pdfplumber
import openai
from dotenv import load_dotenv
from flask_cors import CORS
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Define index name
index_name = "pdf-chat-bot-land2lavish"

# Check if the index exists, create it if it doesn't
if index_name not in pc.list_indexes().names():
    print(f"Creating index {index_name}...")
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    print(f"Index {index_name} created successfully.")

# Connect to the index
try:
    pinecone_index = pc.Index(index_name)
    stats = pinecone_index.describe_index_stats()
    print(f"Connected to Pinecone index: {index_name}, stats: {stats}")
except Exception as e:
    print(f"Failed to connect to Pinecone index: {str(e)}")
    raise

app = Flask(__name__)
CORS(app)

def ensure_default_namespace():
    """Ensure the default namespace exists by upserting a dummy vector if needed."""
    try:
        # Check if the default namespace has any vectors
        stats = pinecone_index.describe_index_stats()
        namespaces = stats.get('namespaces', {})
        if "" not in namespaces:
            print("Default namespace not found. Creating by upserting a dummy vector...")
            # Create a dummy vector with at least one non-zero value
            dummy_values = [0.0] * 1536
            dummy_values[0] = 1.0  # Set the first value to 1.0 to satisfy Pinecone's requirement
            dummy_vector = {
                "id": "dummy",
                "values": dummy_values,
                "metadata": {"text": "dummy"}
            }
            pinecone_index.upsert(vectors=[dummy_vector], namespace="")
            print("Default namespace created successfully.")
        else:
            print(f"Default namespace exists with {namespaces['']['vector_count']} vectors.")
    except Exception as e:
        print(f"Error ensuring default namespace: {str(e)}")
        raise

def extract_text_from_pdf(pdf_path):
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"
    chunk_size = 500
    words = all_text.split()
    chunks = []
    current_chunk = ""
    for word in words:
        if len(current_chunk) + len(word) < chunk_size:
            current_chunk += word + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = word + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    print(f"Extracted {len(chunks)} chunks from PDF.")
    return chunks

def get_embedding(text):
    try:
        response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
        return response["data"][0]["embedding"]
    except Exception as e:
        raise Exception(f"Error generating embedding: {str(e)}")

def search_knowledge_base(query):
    try:
        query_embedding = get_embedding(query)
        results = pinecone_index.query(vector=query_embedding, top_k=5, include_metadata=True, namespace="")
        print(f"Queried Pinecone with query: {query}, found {len(results['matches'])} matches in default namespace.")
        return [result["metadata"]["text"] for result in results["matches"]]
    except Exception as e:
        raise Exception(f"Error searching knowledge base: {str(e)}")

def get_chatbot_response(question, context_chunks):
    try:
        context = "\n".join(context_chunks)
        prompt = f"Based on the following information:\n\n{context}\n\nAnswer the question: {question}\nIf no relevant info is found, say: 'Sorry, I don’t have that information.'"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a knowledgeable assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error with OpenAI API: {str(e)}"

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['pdf_file']
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    temp_filename = "temp_uploaded.pdf"
    file.save(temp_filename)
    try:
        # Ensure the default namespace exists
        ensure_default_namespace()

        chunks = extract_text_from_pdf(temp_filename)
        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            vectors.append({
                "id": f"chunk_{i}",
                "values": embedding,
                "metadata": {"text": chunk}
            })
        
        # Check index stats
        stats = pinecone_index.describe_index_stats()
        print(f"Index stats before operation: {stats}")
        
        # Clear existing vectors in the default namespace
        pinecone_index.delete(delete_all=True, namespace="")
        print("Cleared existing vectors in default namespace.")

        # Upsert vectors in the default namespace
        pinecone_index.upsert(vectors=vectors, namespace="")
        print(f"Upserted {len(vectors)} vectors to Pinecone in default namespace.")

        os.remove(temp_filename)
        return jsonify({"message": f"PDF processed and {len(chunks)} chunks stored in Pinecone"})
    except Exception as e:
        os.remove(temp_filename)
        print(f"Upload failed with error: {str(e)}")
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "Please provide a question"}), 400
    
    stats = pinecone_index.describe_index_stats()
    if stats["total_vector_count"] == 0:
        return jsonify({"error": "Please upload a PDF first"}), 400
    
    try:
        relevant_chunks = search_knowledge_base(question)
        answer = get_chatbot_response(question, relevant_chunks)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": f"Failed to process question: {str(e)}"}), 500

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the PDF Chatbot API"})

if __name__ == "__main__":
    app.run(debug=True)