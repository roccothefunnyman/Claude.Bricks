"""
Configure AI Search index wiring for the Foundry project.

Sets up the RAG index configuration with parameterized chunking strategy
and embedding model vectorization. Wires the index to the Foundry project
so that retrieval-augmented generation flows can use it.

Usage:
    python configure_index.py --chunk-size 1024 --overlap 128
    python configure_index.py --index-name building-specs --embedding-model text-embedding-ada-002

Environment variables:
    SUBSCRIPTION_ID     Azure subscription ID
    RESOURCE_GROUP      Azure resource group name
    FOUNDRY_PROJECT     Foundry project name (workspace)
    SEARCH_ENDPOINT     Azure AI Search endpoint URL
    OPENAI_ENDPOINT     Azure OpenAI endpoint (for embeddings)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from azure.ai.ml import MLClient
from azure.ai.ml.entities import Index
from azure.identity import DefaultAzureCredential


def get_project_client(project_name):
    """Create an MLClient scoped to the Foundry project."""
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
        workspace_name=project_name,
    )


def configure_rag_index(client, index_name, search_endpoint, openai_endpoint,
                         embedding_model, chunk_size, overlap, embedding_dimensions):
    """Configure the RAG index with chunking and embedding settings."""
    print(f"Configuring RAG index '{index_name}'...")

    # Build index configuration as a Foundry-managed index asset
    index_config = {
        "type": "acs",  # Azure Cognitive Search
        "connection": {
            "endpoint": search_endpoint,
            "type": "cognitive_search",
        },
        "index_name": index_name,
        "chunking": {
            "strategy": "fixed_size",
            "chunk_size": chunk_size,
            "overlap": overlap,
        },
        "embedding": {
            "model": embedding_model,
            "endpoint": openai_endpoint,
            "dimensions": embedding_dimensions,
            "type": "azure_open_ai",
        },
        "field_mapping": {
            "content_field": "content",
            "title_field": "title",
            "vector_field": "content_vector",
            "metadata_fields": ["style"],
        },
    }

    # Register the index configuration as a Foundry index asset
    index = Index(
        name=index_name,
        version="1",
        description=f"RAG index for Claude.Bricks building specifications "
                    f"(chunk_size={chunk_size}, overlap={overlap})",
        path=search_endpoint,
        properties=index_config,
    )

    result = client.indexes.create_or_update(index)
    print(f"Index asset '{index_name}' registered in Foundry project.")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Configure AI Search index wiring for Foundry project"
    )
    parser.add_argument("--project-name", type=str,
                        default=os.environ.get("FOUNDRY_PROJECT", "claudebricks-genai"),
                        help="Foundry project name")
    parser.add_argument("--index-name", type=str, default="building-specs",
                        help="Name of the AI Search index")
    parser.add_argument("--chunk-size", type=int, default=1024,
                        help="Chunk size in tokens for document splitting")
    parser.add_argument("--overlap", type=int, default=128,
                        help="Overlap in tokens between chunks")
    parser.add_argument("--embedding-model", type=str, default="text-embedding-ada-002",
                        help="Embedding model deployment name")
    parser.add_argument("--embedding-dimensions", type=int, default=1536,
                        help="Embedding vector dimensions")
    args = parser.parse_args()

    search_endpoint = os.environ["SEARCH_ENDPOINT"]
    openai_endpoint = os.environ.get("OPENAI_ENDPOINT", "")

    client = get_project_client(args.project_name)

    # Configure the index
    print("=" * 60)
    print("RAG Index Configuration")
    print("=" * 60)

    configure_rag_index(
        client=client,
        index_name=args.index_name,
        search_endpoint=search_endpoint,
        openai_endpoint=openai_endpoint,
        embedding_model=args.embedding_model,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        embedding_dimensions=args.embedding_dimensions,
    )

    # Print summary
    print()
    print("=" * 60)
    print("Index Configuration Summary")
    print("=" * 60)
    print(f"  Project:              {args.project_name}")
    print(f"  Index name:           {args.index_name}")
    print(f"  Search endpoint:      {search_endpoint}")
    print(f"  Chunking strategy:    fixed_size")
    print(f"  Chunk size:           {args.chunk_size} tokens")
    print(f"  Chunk overlap:        {args.overlap} tokens")
    print(f"  Embedding model:      {args.embedding_model}")
    print(f"  Embedding dimensions: {args.embedding_dimensions}")
    print()
    print("The index is now wired to the Foundry project for RAG flows.")
    print("Documents in the AI Search index will be chunked and vectorized")
    print("using the configured embedding model.")


if __name__ == "__main__":
    main()
