"""Retrieval node: query Azure AI Search for relevant building specs."""
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient


def retrieve(query: str, search_endpoint: str, index_name: str, top_k: int = 3) -> str:
    """Search for relevant building specs using text search."""
    credential = DefaultAzureCredential()
    client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=credential,
    )

    results = client.search(
        search_text=query,
        top=top_k,
        select=["title", "content", "style"],
    )

    context_parts = []
    for result in results:
        context_parts.append(
            f"Title: {result['title']}\n"
            f"Style: {result['style']}\n"
            f"Content: {result['content']}"
        )

    return "\n---\n".join(context_parts) if context_parts else "No relevant specs found."
