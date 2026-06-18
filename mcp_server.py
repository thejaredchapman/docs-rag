"""FastMCP server exposing the docs RAG pipeline as MCP tools, so clients
like Claude Code or Cursor can query your docs directly.

Run: python mcp_server.py
"""
from fastmcp import FastMCP

import query

mcp = FastMCP("docs-rag")


@mcp.tool()
def ask_docs(question: str, top_k: int | None = None) -> dict:
    """Answer a question about the indexed documents, with source citations."""
    return query.ask(question, top_k=top_k)


@mcp.tool()
def list_sources() -> list[str]:
    """List every source file currently in the index."""
    return query.list_sources()


@mcp.tool()
def index_stats() -> dict:
    """Return stats about the current index: chunk/source counts, models, cache hit rate."""
    stats = query.index_stats()
    stats["cache"] = query.cache_stats()
    return stats


def main():
    mcp.run()


if __name__ == "__main__":
    main()
