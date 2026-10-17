import asyncio
import os

from openai import AsyncOpenAI

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
REQUEST_TIMEOUT_SECONDS = 120
BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", "32"))
CONCURRENCY = int(os.environ.get("EMBEDDING_CONCURRENCY", "1"))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "1024"))
QUERY_INSTRUCTION = "Instruct: Given a question, retrieve passages from the document that answer it\nQuery: "


class EmbeddingError(Exception):
    pass


def _batches(texts):
    result = []
    for idx in range(0, len(texts), BATCH_SIZE):
        result.append(texts[idx : idx + BATCH_SIZE])
    return result


def _validate(texts, vectors):
    if len(vectors) != len(texts):
        raise EmbeddingError(f"Expected {len(texts)} vectors, got {len(vectors)}")
    for idx, vector in enumerate(vectors):
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise EmbeddingError(
                f"Vector {idx} has {len(vector)} dimensions, expected {EMBEDDING_DIMENSIONS} "
                f"(check EMBEDDING_MODEL / EMBEDDING_DIMENSIONS)"
            )


async def _embed_all(texts):
    semaphore = asyncio.Semaphore(CONCURRENCY)
    async with AsyncOpenAI(
        base_url=f"{OLLAMA_BASE_URL}/v1",
        api_key="ollama",
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=2,
    ) as client:

        async def embed_batch(batch):
            async with semaphore:

                response = await client.embeddings.create(
                    model=EMBEDDING_MODEL, input=batch
                )
                ordered = sorted(response.data, key=lambda item: item.index)
                return [item.embedding for item in ordered]

        results = await asyncio.gather(*(embed_batch(b) for b in _batches(texts)))
    return [vector for batch in results for vector in batch]


def embed_texts(texts):
    if not texts:
        return []
    if any(not t.strip() for t in texts):
        raise EmbeddingError("Cannot embed empty text")

    vectors = asyncio.run(_embed_all(texts))
    _validate(texts, vectors)

    return vectors


def embed_query(question: str) -> list[float]:
    """Embed a user question for retrieval (sync). Adds the query instruction."""
    return embed_texts([QUERY_INSTRUCTION + question])[0]


async def embed_query(question: str) -> list[float]:
    """Same as embed_query, for async code (FastAPI endpoints)."""
    text = QUERY_INSTRUCTION + question
    vectors = await _embed_all([text])
    _validate([text], vectors)
    return vectors[0]
