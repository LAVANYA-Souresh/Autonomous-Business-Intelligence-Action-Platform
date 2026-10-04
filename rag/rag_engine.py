
from pathlib import Path

from sentence_transformers import SentenceTransformer
import faiss


KNOWLEDGE_DIR = Path("knowledge")

MODEL_NAME = "all-MiniLM-L6-v2"


def load_documents():

    documents = []

    for file_path in KNOWLEDGE_DIR.glob("*.md"):

        content = file_path.read_text(
            encoding="utf-8"
        )

        documents.append({
            "source": file_path.name,
            "content": content
        })

    return documents


def chunk_text(text):

    sections = text.split("\n## ")

    chunks = []

    for section in sections:

        section = section.strip()

        if not section:
            continue

        if not section.startswith("#"):
            section = "## " + section

        paragraphs = section.split("\n\n")

        current_chunk = ""

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            if len(current_chunk) + len(paragraph) <= 800:

                if current_chunk:
                    current_chunk += "\n\n"

                current_chunk += paragraph

            else:

                if current_chunk:
                    chunks.append(
                        current_chunk.strip()
                    )

                current_chunk = paragraph

        if current_chunk:
            chunks.append(
                current_chunk.strip()
            )

    return chunks


def create_chunks(documents):

    chunks = []

    for document in documents:

        document_chunks = chunk_text(
            document["content"]
        )

        for chunk in document_chunks:

            chunks.append({
                "source": document["source"],
                "content": chunk
            })

    return chunks


def create_embeddings(chunks, model):

    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True
    )

    return embeddings


def create_vector_index(embeddings):

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings)

    return index


class RAGRetriever:

    def __init__(self):

        print("Initializing RAG retriever...")

        self.documents = load_documents()

        print(
            f"Loaded {len(self.documents)} knowledge documents."
        )

        self.chunks = create_chunks(
            self.documents
        )

        print(
            f"Created {len(self.chunks)} chunks."
        )

        print("Loading embedding model...")

        self.model = SentenceTransformer(
            MODEL_NAME
        )

        print("Creating embeddings...")

        embeddings = create_embeddings(
            self.chunks,
            self.model
        )

        print(
            f"Embedding dimension: "
            f"{embeddings.shape[1]}"
        )

        print("Creating FAISS vector index...")

        self.index = create_vector_index(
            embeddings
        )

        print(
            f"Vector index contains "
            f"{self.index.ntotal} vectors."
        )

    def retrieve(
        self,
        query,
        top_k=3
    ):

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True
        )

        distances, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for distance, index_position in zip(
            distances[0],
            indices[0]
        ):

            results.append({

                "source": self.chunks[
                    index_position
                ]["source"],

                "content": self.chunks[
                    index_position
                ]["content"],

                "distance": float(distance)
            })

        return results


if __name__ == "__main__":

    print(
        "\n========== RAG RETRIEVER TEST ==========\n"
    )

    retriever = RAGRetriever()

    query = (
        "What does an increase in return "
        "rate mean?"
    )

    results = retriever.retrieve(
        query,
        top_k=3
    )

    print(
        f"\nQuery: {query}"
    )

    for result in results:

        print("\n--------------------")

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Distance: "
            f"{result['distance']:.4f}"
        )

        print(
            result["content"]
        )

