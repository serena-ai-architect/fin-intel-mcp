"""Langfuse observability — trace every MCP tool call from day one."""

import functools
import time
from typing import Any, Callable

from langfuse import Langfuse

from config import settings

_langfuse: Langfuse | None = None


def get_langfuse() -> Langfuse | None:
    """Lazy-init Langfuse client. Returns None if credentials not configured."""
    global _langfuse
    if _langfuse is not None:
        return _langfuse

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    _langfuse = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    return _langfuse


def trace_tool(tool_name: str) -> Callable:
    """Decorator to trace MCP tool calls in Langfuse.

    Usage:
        @trace_tool("search_sec_filings")
        async def search_sec_filings(input: SearchFilingsInput) -> RAGResult:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            langfuse = get_langfuse()
            if not langfuse:
                return await func(*args, **kwargs)

            trace = langfuse.trace(
                name=f"mcp.{tool_name}",
                metadata={"tool": tool_name},
            )
            span = trace.span(name=tool_name, input=kwargs or (args[0] if args else None))

            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                span.end(
                    output=result if isinstance(result, (dict, str)) else str(result),
                    metadata={"duration_ms": round(elapsed * 1000)},
                )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                span.end(
                    level="ERROR",
                    status_message=str(e),
                    metadata={"duration_ms": round(elapsed * 1000)},
                )
                raise

        return wrapper

    return decorator
