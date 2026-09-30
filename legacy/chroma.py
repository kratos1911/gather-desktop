from main import vector_index, embed_model, llm
import chromadb
import os
from llama_index.llms.ollama import Ollama
import json

def init_db():
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="file_embeddings",embedding_function=None)
    return collection

collection = init_db()

llm = Ollama(model="mistral", request_timeout=300.0)

def create_document_embedding(vector_index):
    all_embeddings = []
    all_metadatas = []
    all_ids = []

    os.makedirs("./doc_store", exist_ok=True)  # directory to save document text

    existing_ids = set()
    if collection.count() > 0:
        existing_ids = set(collection.get()["ids"])

    for node in vector_index.docstore.docs.values():
        doc_id = node.id_
        metadata = node.metadata or {}
        file_name = metadata.get("filename", f"Unknown_File_{doc_id}")

        if doc_id in existing_ids:
            print("Legacy operation: private details omitted.")
            continue

        print("Legacy operation: private details omitted.")

        if node.embedding is None:
            node.embedding = embed_model.get_text_embedding(node.text)

        embedding = node.embedding
        print("Legacy operation: private details omitted.")

        # ✅ Save full document text to file
        doc_path = os.path.join("doc_store", f"{doc_id}.json")
        with open(doc_path, "w", encoding="utf-8") as f:
            json.dump({"file_name": file_name, "text": node.text}, f)

        all_embeddings.append(embedding)
        all_metadatas.append({"file_name": file_name, "doc_id": doc_id})
        all_ids.append(doc_id)

    if all_ids:
        # print("\n📦 Preparing to add to ChromaDB:")
        # for i in range(len(all_ids)):
        #     print(f"→ ID: {all_ids[i]}, File: {all_metadatas[i]['file_name']}")

        collection.add(
            embeddings=all_embeddings,
            metadatas=all_metadatas,
            ids=all_ids
        )
        print("✅ New embeddings stored successfully in ChromaDB")
    else:
        print("📁 No new documents to add.")

    print("\n🧾 Stored Entries in ChromaDB:")
    all_data = collection.get()
    for i in range(len(all_data["ids"])):
        print("Legacy operation: private details omitted.")
        print("Legacy operation: private details omitted.")

def search_document(query_text, top_k=1):
    query_embedding = embed_model.get_text_embedding(query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    if results and results.get("metadatas") and len(results["metadatas"][0]) > 0:
        matched_files = results["metadatas"][0]
        best_match = matched_files[0]

        print("Legacy operation: private details omitted.")

        file_name = best_match.get("file_name", "Unknown File")
        doc_id = best_match.get("doc_id")

        # 🔁 Load full document text from saved JSON
        doc_path = os.path.join("doc_store", f"{doc_id}.json")
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
                document_text = doc_data.get("text", "")

                print("Legacy operation: private details omitted.")
                print("Legacy operation: private details omitted.")
                return file_name, document_text
        else:
            print("⚠️ Document text file not found!")

    print("❌ No relevant documents found in ChromaDB.")
    return None, None

def ask_question_about_document(file_name, document_text):
    if document_text:
        user_question = input("\n🔹 Enter your question about the document: ")
        full_prompt = f"""
        Based on the document titled \"{file_name}\", answer this question within the document context:
        \"{user_question}\"

        Document Excerpt:
        {document_text[:2000]}
        """
        response = llm.complete(full_prompt)
        print("Legacy operation: private details omitted.")
        return response

# 🔁 RUN
create_document_embedding(vector_index)
file_name, document_text = search_document(input("🔹 Enter your search query: "))
ask_question_about_document(file_name, document_text)
