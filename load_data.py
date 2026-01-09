from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
import os
import argparse
import shutil

# Import modular loaders
from docx_loader import extract_content_from_docx

data_path = os.getenv("DATA_PATH", "/app/Knowledge-Base")
db_location = os.getenv("CHROMA_PATH", "./chroma_langchain_db")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

def clean_metadata(metadata):
    """Clean metadata to only include simple types"""
    allowed_types = (str, int, float, bool, type(None))
    cleaned = {}
    
    keep_keys = ['source', 'page', 'type', 'id', 'total_pages', 'has_table', 'used_ocr', 'file_type']
    
    for key in keep_keys:
        if key in metadata:
            value = metadata[key]
            if isinstance(value, allowed_types):
                cleaned[key] = value
            elif value is not None:
                cleaned[key] = str(value)
    
    return cleaned

def load_document():
    documents = []

    if not os.path.exists(data_path):
        print(f"❌ Error: Directory '{data_path}' does not exist!")
        return documents

    # Only DOCX files (ignore temp files)
    docx_files = [
        f for f in os.listdir(data_path)
        if f.lower().endswith(".docx") and not f.startswith("~$")
    ]

    if not docx_files:
        print(f"❌ No DOCX files found in '{data_path}'")
        return documents

    print(f"📚 Found {len(docx_files)} DOCX files\n")

    for filename in docx_files:
        file_path = os.path.join(data_path, filename)
        print(f"📄 Processing DOCX: {filename}")

        docs = extract_content_from_docx(file_path)

        if not docs:
            print(f"  ❌ Failed to extract content from {filename}\n")
            continue

        documents.extend(docs)

        total_chars = sum(len(doc.page_content) for doc in docs)
        sections_with_tables = sum(
            1 for doc in docs if doc.metadata.get("has_table")
        )

        print(f"  🧩 Sections: {len(docs)}")
        print(f"  📊 Sections with tables: {sections_with_tables}")
        print(f"  📝 Total characters: {total_chars:,}\n")

    print(f"\n{'=' * 60}")
    print(f"✅ Successfully loaded {len(documents)} sections")

    if documents:
        with_tables = sum(
            1 for doc in documents if doc.metadata.get("has_table")
        )
        print(f"📊 Sections with tables: {with_tables}/{len(documents)}")

    return documents


def split_text(documents: list[Document]):
    """Split documents with special handling for tables"""
    all_chunks = []
    
    docs_with_tables = [doc for doc in documents if doc.metadata.get('has_table')]
    regular_docs = [doc for doc in documents if not doc.metadata.get('has_table')]
    
    if regular_docs:
        regular_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        )
        regular_chunks = regular_splitter.split_documents(regular_docs)
        all_chunks.extend(regular_chunks)
        print(f"✂️ Split {len(regular_docs)} regular sections into {len(regular_chunks)} chunks")
    
    if docs_with_tables:
        table_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
            separators=["\n\n---\n", "\n\n", "\n", " ", ""]
        )
        table_chunks = table_splitter.split_documents(docs_with_tables)
        all_chunks.extend(table_chunks)
        print(f"✂️ Split {len(docs_with_tables)} sections with tables into {len(table_chunks)} chunks")
    
    print(f"\n📦 Total: {len(all_chunks)} chunks")
    
    if all_chunks:
        lengths = [len(c.page_content) for c in all_chunks]
        avg_length = sum(lengths) / len(lengths)
        print(f"  📊 Avg chunk size: {avg_length:.0f} characters")
        print(f"  📊 Min: {min(lengths)}, Max: {max(lengths)}")
    
    return all_chunks

def save_to_chroma(chunks: list[Document]):
    print(f"\n{'='*60}")
    print("💾 Saving to ChromaDB...")
    
    print("🔧 Filtering complex metadata...")
    chunks = filter_complex_metadata(chunks)
    
    for chunk in chunks:
        chunk.metadata = clean_metadata(chunk.metadata)
    
    print(f"📦 Total chunks to save: {len(chunks)}")
    
    embedding_model = OllamaEmbeddings(
        model="embeddinggemma:latest",
        base_url= OLLAMA_HOST
    )
    
    # Sort chunks deterministically before assigning IDs
    chunks_sorted = sorted(
        chunks,
        key=lambda c: (
            c.metadata.get('source'),
            int(c.metadata.get('page', 0)),
            bool(c.metadata.get('has_table', False)),
            int(c.metadata.get('start', 0)) if c.metadata.get('start') is not None else 0
        )
    )
    chunks_with_ids = calculate_chunk_ids(chunks_sorted)
    
    if os.path.exists(db_location):
        print("📂 Loading existing database...")
        db = Chroma(
            persist_directory=db_location,
            embedding_function=embedding_model
        )
        
        existing_items = db.get()
        existing_ids = set(existing_items.get("ids", []))
        print(f"  📊 Existing documents: {len(existing_ids)}")
        
        new_chunks = [
            chunk for chunk in chunks_with_ids 
            if chunk.metadata["id"] not in existing_ids
        ]
        
        if new_chunks:
            print(f"  ➕ Adding {len(new_chunks)} new documents...")
            new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
            
            for chunk in new_chunks:
                chunk.metadata = clean_metadata(chunk.metadata)
            
            db.add_documents(new_chunks, ids=new_chunk_ids)
            print("  ✅ New documents added")
        else:
            print("  ℹ️ No new documents to add")
    else:
        print("🆕 Creating new database...")
        new_chunk_ids = [chunk.metadata["id"] for chunk in chunks_with_ids]
        # Use embedding_function param for consistency with runtime usage
        try:
            db = Chroma.from_documents(
                documents=chunks_with_ids,
                embedding_function=embedding_model,
                persist_directory=db_location,
                ids=new_chunk_ids
            )
        except TypeError:
            # Fallback if older API expects `embedding`
            db = Chroma.from_documents(
                documents=chunks_with_ids,
                embedding=embedding_model,
                persist_directory=db_location,
                ids=new_chunk_ids
            )
        print(f"  ✅ Saved {len(chunks_with_ids)} chunks to {db_location}")
    
    print("\n✨ Database saved successfully!")

def calculate_chunk_ids(chunks):
    """Generate unique IDs for each chunk"""
    last_page_id = None
    current_chunk_index = 0
    
    for chunk in chunks:
        source = chunk.metadata.get("source", "UNKNOWN_SOURCE")
        page = chunk.metadata.get("page", 0)
        has_table = chunk.metadata.get("has_table", False)
        used_ocr = chunk.metadata.get("used_ocr", False)
        file_type = chunk.metadata.get("file_type", "unknown")
        
        table_suffix = "_table" if has_table else ""
        ocr_suffix = "_ocr" if used_ocr else ""
        current_page_id = f"{source}:{file_type}:page_{page}{table_suffix}{ocr_suffix}"
        
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0
        
        chunk_id = f"{current_page_id}:chunk_{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id
    
    return chunks

def clear_database():
    """Remove the ChromaDB directory"""
    if os.path.exists(db_location):
        shutil.rmtree(db_location)
        print(f"✅ Database cleared: {db_location}")
    else:
        print("ℹ️ No database to clear")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    parser.add_argument("--test", action="store_true", help="Test retrieval after loading.")
    args = parser.parse_args()
    
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    documents = load_document()
    if not documents:
        print("No documents found. Exiting.")
        return
    
    chunks = split_text(documents)
    
    print("\n🧹 Cleaning metadata...")
    for chunk in chunks:
        chunk.metadata = clean_metadata(chunk.metadata)
    
    save_to_chroma(chunks)


if __name__ == "__main__":
    main()
