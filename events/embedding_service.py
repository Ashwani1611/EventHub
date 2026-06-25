import logging
from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

logger = logging.getLogger(__name__)

# Model runs locally — no API key needed
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_COLLECTION = "events"


def get_embedding_function():
    """Returns the HuggingFace embedding model."""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def get_vector_store():
    """Returns the ChromaDB vector store."""
    return Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=get_embedding_function(),
        persist_directory=str(settings.CHROMA_DB_PATH),
    )


def index_event(event):
    """
    Generate embedding for an event and store it in ChromaDB.
    Called when an event is created or updated.
    """
    try:
        vector_store = get_vector_store()

        # Combine title + description into one searchable text
        text = f"{event.title} {event.description} {event.venue}"

        # ChromaDB needs string IDs
        event_id = str(event.id)

        # Delete existing entry if updating
        try:
            vector_store.delete(ids=[event_id])
        except Exception:
            pass  # No existing entry — that's fine

        vector_store.add_texts(
            texts=[text],
            metadatas=[{
                "event_id": event.id,
                "title": event.title,
                "venue": event.venue,
                "price": float(event.price),
                "status": event.status,
            }],
            ids=[event_id]
        )

        logger.info(f"Event indexed in ChromaDB | event_id={event.id} | title={event.title}")

    except Exception as e:
        logger.error(f"Failed to index event | event_id={event.id} | error={e}")


def search_events(query: str, n_results: int = 10):
    """
    Search for events semantically similar to the query.
    Returns a list of event_ids ranked by similarity.
    """
    try:
        vector_store = get_vector_store()

        results = vector_store.similarity_search(
            query=query,
            k=n_results,
            filter={"status": "published"}
        )

        event_ids = [int(doc.metadata["event_id"]) for doc in results]
        logger.info(f"Semantic search | query='{query}' | results={event_ids}")
        return event_ids

    except Exception as e:
        logger.error(f"Semantic search failed | query='{query}' | error={e}")
        return []