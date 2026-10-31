
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


# ------------------------------------
# Project Configuration
# ------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
FAISS_INDEX_DIR = BASE_DIR / "data" / "faiss_index"

EMBEDDING_MODEL = "text-embedding-3-small"

load_dotenv(BASE_DIR / ".env")


# ------------------------------------
# Step 1: Load Company Documents
# ------------------------------------

def load_documents():

    documents = []

    if not KNOWLEDGE_BASE_DIR.exists():
        raise FileNotFoundError(
            f"Knowledge base not found: {KNOWLEDGE_BASE_DIR}"
        )

    for file_path in sorted(
        KNOWLEDGE_BASE_DIR.glob("*.md")
    ):

        content = file_path.read_text(
            encoding="utf-8"
        )

        if not content.strip():
            print(f"Skipping empty file: {file_path.name}")
            continue

        document = Document(
            page_content=content,
            metadata={
                "source": file_path.name,
                "file_path": str(file_path)
            }
        )

        documents.append(document)

        print(f"Loaded: {file_path.name}")

    return documents


# ------------------------------------
# Step 2: Split Documents into Chunks
# ------------------------------------

def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index + 1

    return chunks


# ------------------------------------
# Step 3: Generate Embeddings
# Step 4: Store Vectors in FAISS
# ------------------------------------

def create_faiss_index(chunks):

    print("\nGenerating OpenAI embeddings...")

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL
    )

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    FAISS_INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    vector_store.save_local(
        str(FAISS_INDEX_DIR)
    )

    print("\nFAISS index created successfully!")

    print(f"Index location: {FAISS_INDEX_DIR}")

    print(
        f"Total vectors stored: "
        f"{vector_store.index.ntotal}"
    )


# ------------------------------------
# Main Execution
# ------------------------------------

def main():

    print("=" * 55)
    print("SupportIQ AI - FAISS Knowledge Base Ingestion")
    print("=" * 55)

    documents = load_documents()

    print(f"\nTotal documents loaded: {len(documents)}")

    if not documents:
        raise RuntimeError(
            "No valid knowledge base documents found."
        )

    chunks = split_documents(documents)

    print(f"Total chunks created: {len(chunks)}")

    if not chunks:
        raise RuntimeError(
            "No text chunks generated."
        )

    create_faiss_index(chunks)

    print("\nKnowledge Base Indexing Completed!")


if __name__ == "__main__":
    main()
