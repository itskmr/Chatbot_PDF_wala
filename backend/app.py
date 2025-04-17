import os
from flask import Flask, request, jsonify
import pdfplumber
import openai
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Global variable to store extracted PDF text (for demo purposes)
knowledge_base = ""

def extract_text_from_pdf(pdf_path):
    """Extracts text from the given PDF file using pdfplumber."""
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"
    return all_text

def get_chatbot_response(question, context):
    """Calls OpenAI's API to get an answer based on the provided context."""
    try:
        prompt = f"Based on the following information:\n\n{context}\n\nAnswer the question: {question}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a knowledgeable assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error with OpenAI API: {str(e)}"

@app.route("/upload", methods=["POST"])
def upload_pdf():
    global knowledge_base
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
        knowledge_base = extract_text_from_pdf(temp_filename)
        os.remove(temp_filename)
        return jsonify({"message": "PDF uploaded and processed successfully"})
    except Exception as e:
        os.remove(temp_filename)
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    global knowledge_base
    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "Please provide a question"}), 400
    if not knowledge_base:
        return jsonify({"error": "Please upload a PDF first"}), 400
    answer = get_chatbot_response(question, knowledge_base)
    return jsonify({"answer": answer})

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the PDF Chatbot API"})

if __name__ == "__main__":
    app.run(debug=True)