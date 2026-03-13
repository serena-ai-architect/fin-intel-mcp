"""OpenAI embedding client for text-embedding-3-small."""

from openai import AsyncOpenAI

from config import settings

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns list of embedding vectors."""
    client = _get_client()
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    result = await embed_texts([query])
    return result[0]
