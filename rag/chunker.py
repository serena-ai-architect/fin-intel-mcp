"""Semantic text chunking using LangChain's RecursiveCharacterTextSplitter."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    return _splitter.split_text(text)
