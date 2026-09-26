from llama_index.llms.ollama import Ollama
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, PromptTemplate
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from pydantic import BaseModel
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.query_pipeline import QueryPipeline
from prompts import context, code_parser_template
from code_reader import code_reader
from dotenv import load_dotenv
from llama_index.core.extractors import KeywordExtractor, SummaryExtractor
import os
import fitz  # PyMuPDF for PDFs
import docx  # python-docx for DOCX files
from pptx import Presentation  # python-pptx for PPTX files
from llama_index.core import Settings
from llama_index.core.schema import Document
import shutil

load_dotenv()

llm = Ollama(model="mistral", request_timeout=300.0)
embed_model = resolve_embed_model("local:BAAI/bge-m3")
Settings.llm = Ollama(model="mistral", request_timeout=300.0)

def process_file(file_path):
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    text = ""

    try:
        if ext == ".pdf":
            with fitz.open(file_path) as pdf_doc:
                text = "\n".join([page.get_text() for page in pdf_doc])
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        elif ext in [".doc", ".docx"]:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif ext == ".pptx":
            ppt = Presentation(file_path)
            text = "\n".join([
                shape.text for slide in ppt.slides for shape in slide.shapes if hasattr(shape, "text") and shape.text
            ])
        else:
            print("Legacy operation: private details omitted.")
            return None

    except Exception as e:
        print("Legacy operation: private details omitted.")
        return None

    return Document(text=text, metadata={"filename": filename})

def move_file(file_path, destination_dir):
    os.makedirs(destination_dir, exist_ok=True)
    dest_path = os.path.join(destination_dir, os.path.basename(file_path))
    shutil.move(file_path, dest_path)
    print("Legacy operation: private details omitted.")

def process_documents(temp_dir="./temp", final_dir="./data"):
    all_documents = []
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        print("Legacy operation: private details omitted.")

        document = process_file(file_path)
        if document:
            all_documents.append(document)
            move_file(file_path, final_dir)
            print("Legacy operation: private details omitted.")
            print("Legacy operation: private details omitted.")

    print("\n✅ All files processed and moved successfully.")
    return all_documents

def create_index(documents):
    vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
    for node in vector_index.docstore.docs.values():
        print("Legacy operation: private details omitted.")
        print("Legacy operation: private details omitted.")
        print("Legacy operation: private details omitted.")
    return vector_index

docs = process_documents()
vector_index = create_index(docs)




