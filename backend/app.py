import os
import glob
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

# Define namespaces
PRELOADED_NAMESPACE = "preloaded_pdfs"
USER_NAMESPACE = ""  # Default namespace for user uploads

def ensure_namespace(namespace):
    """Ensure a namespace exists by upserting a dummy vector if needed."""
    try:
        stats = pinecone_index.describe_index_stats()
        namespaces = stats.get('namespaces', {})
        if namespace not in namespaces:
            print(f"Namespace {namespace} not found. Creating by upserting a dummy vector...")
            dummy_values = [0.0] * 1536
            dummy_values[0] = 1.0
            dummy_vector = {
                "id": "dummy",
                "values": dummy_values,
                "metadata": {"text": "dummy"}
            }
            pinecone_index.upsert(vectors=[dummy_vector], namespace=namespace)
            print(f"Namespace {namespace} created successfully.")
        else:
            print(f"Namespace {namespace} exists with {namespaces[namespace]['vector_count']} vectors.")
    except Exception as e:
        print(f"Error ensuring namespace {namespace}: {str(e)}")
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
    print(f"Extracted {len(chunks)} chunks from PDF: {pdf_path}")
    return chunks

def get_embedding(text):
    try:
        response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
        return response["data"][0]["embedding"]
    except Exception as e:
        raise Exception(f"Error generating embedding: {str(e)}")

def search_knowledge_base(query, namespace=PRELOADED_NAMESPACE):
    try:
        query_embedding = get_embedding(query)
        results = pinecone_index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            namespace=namespace
        )
        print(f"Queried Pinecone in namespace {namespace} with query: {query}, found {len(results['matches'])} matches.")
        return [result["metadata"]["text"] for result in results["matches"]]
    except Exception as e:
        raise Exception(f"Error searching knowledge base in namespace {namespace}: {str(e)}")

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

# Function to pre-process and upload PDFs to Pinecone
def preload_pdfs():
    pdf_folder = "pdfs"
    if not os.path.exists(pdf_folder):
        print(f"PDF folder {pdf_folder} does not exist. Creating it...")
        os.makedirs(pdf_folder)
        return

    pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {pdf_folder}.")
        return

    ensure_namespace(PRELOADED_NAMESPACE)
    pinecone_index.delete(delete_all=True, namespace=PRELOADED_NAMESPACE)
    print(f"Cleared existing vectors in namespace {PRELOADED_NAMESPACE}.")

    for pdf_path in pdf_files:
        try:
            chunks = extract_text_from_pdf(pdf_path)
            vectors = []
            for i, chunk in enumerate(chunks):
                embedding = get_embedding(chunk)
                vectors.append({
                    "id": f"{os.path.basename(pdf_path).replace('.pdf', '')}_chunk_{i}",
                    "values": embedding,
                    "metadata": {"text": chunk, "source": os.path.basename(pdf_path)}
                })

            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                pinecone_index.upsert(vectors=batch, namespace=PRELOADED_NAMESPACE)
                print(f"Upserted batch for {pdf_path}: {len(batch)} vectors.")
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")

    stats = pinecone_index.describe_index_stats()
    print(f"Preloaded PDFs. Index stats: {stats}")

# New endpoint to get list of preloaded PDFs
@app.route("/pdfs", methods=["GET"])
def get_pdfs():
    pdf_folder = "pdfs"
    if not os.path.exists(pdf_folder):
        return jsonify({"pdfs": []})
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    return jsonify({"pdfs": pdf_files})

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
        ensure_namespace(USER_NAMESPACE)
        chunks = extract_text_from_pdf(temp_filename)
        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            vectors.append({
                "id": f"chunk_{i}",
                "values": embedding,
                "metadata": {"text": chunk}
            })

        pinecone_index.delete(delete_all=True, namespace=USER_NAMESPACE)
        print(f"Cleared existing vectors in namespace {USER_NAMESPACE}.")

        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            pinecone_index.upsert(vectors=batch, namespace=USER_NAMESPACE)
            print(f"Upserted batch: {len(batch)} vectors.")

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

    try:
        # Query preloaded PDFs first
        relevant_chunks = search_knowledge_base(question, namespace=PRELOADED_NAMESPACE)
        if not relevant_chunks:
            # Optionally query user-uploaded PDFs
            relevant_chunks = search_knowledge_base(question, namespace=USER_NAMESPACE)
        answer = get_chatbot_response(question, relevant_chunks)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": f"Failed to process question: {str(e)}"}), 500

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the PDF Chatbot API"})

if __name__ == "__main__":
    # Preload PDFs when the application starts
    preload_pdfs()
    app.run(debug=True)