
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


# ==========================================
# Project Configuration
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

FAISS_INDEX_DIR = BASE_DIR / "data" / "faiss_index"

EMBEDDING_MODEL = "text-embedding-3-small"

load_dotenv(BASE_DIR / ".env")


# ==========================================
# Category to Knowledge Base Mapping
# ==========================================

CATEGORY_SOURCES = {
    "shipping": ["shipping_policy.md"],
    "refund": ["refund_policy.md"],
    "account": ["account_and_login.md"],
    "product": [
        "product_faq.md",
        "refund_policy.md"
    ],
    "billing": ["refund_policy.md"]
}


# ==========================================
# Load FAISS Vector Store
# ==========================================

def load_vector_store():
    """Load the locally generated FAISS index."""

    index_file = FAISS_INDEX_DIR / "index.faiss"
    metadata_file = FAISS_INDEX_DIR / "index.pkl"

    if not index_file.exists() or not metadata_file.exists():
        raise FileNotFoundError(
            "FAISS index files not found. "
            "Run vector_rag/ingest.py first."
        )

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL
    )

    vector_store = FAISS.load_local(
        str(FAISS_INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_store


# ==========================================
# Category-Aware Semantic Search
# ==========================================

def search_kb(
    query: str,
    category: str = None,
    top_k: int = 3
):
    """
    Search FAISS using semantic similarity.

    When a valid category is provided, results
    are restricted to matching policy files.
    """

    if not query or not query.strip():
        return []

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    vector_store = load_vector_store()

    normalized_category = (
        category.strip().lower()
        if category else None
    )

    allowed_sources = CATEGORY_SOURCES.get(
        normalized_category
    )

    # If a category was supplied but is unknown,
    # return no results rather than guessing.
    if normalized_category and allowed_sources is None:
        return []

    search_kwargs = {
        "k": top_k
    }

    if allowed_sources:
        search_kwargs["filter"] = {
            "source": {
                "$in": allowed_sources
            }
        }

        # Search all indexed chunks before filtering.
        search_kwargs["fetch_k"] = (
            vector_store.index.ntotal
        )

    results = vector_store.similarity_search_with_score(
        query,
        **search_kwargs
    )

    passages = []

    for document, score in results:

        passages.append({
            "source": document.metadata.get(
                "source", "unknown"
            ),
            "chunk_id": document.metadata.get(
                "chunk_id"
            ),
            "content": document.page_content,
            "distance": float(score)
        })

    return passages


# ==========================================
# Command Line Testing
# ==========================================

def main():

    print("=" * 60)
    print("SupportIQ AI - Category-Aware FAISS Search")
    print("=" * 60)

    print("\nAvailable categories:")
    print("shipping | refund | account | product | billing")

    question = input(
        "\nEnter customer complaint: "
    ).strip()

    category = input(
        "Enter category: "
    ).strip().lower()

    try:
        results = search_kb(
            query=question,
            category=category or None,
            top_k=3
        )

        if not results:
            print(
                "\nNo matching policy passages found."
            )
            print(
                "This case may require human escalation."
            )
            return

        print(
            f"\nRetrieved {len(results)} passages:"
        )

        for index, result in enumerate(
            results, start=1
        ):

            print(f"\n{'-' * 55}")
            print(f"Result {index}")
            print(f"{'-' * 55}")

            print(
                f"Source: {result['source']}"
            )

            print(
                f"Chunk ID: {result['chunk_id']}"
            )

            print(
                f"FAISS distance: "
                f"{result['distance']:.4f}"
            )

            print(
                f"\nContent:\n{result['content']}"
            )

    except Exception as error:
        print(
            f"\nFAISS search failed: {error}"
        )


if __name__ == "__main__":
    main()
