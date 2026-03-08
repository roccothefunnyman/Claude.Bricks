"""
Set up Azure AI Search index for RAG.

Creates a search index with vector fields, generates placeholder embeddings,
and uploads building spec documents.

References:
  https://learn.microsoft.com/en-us/azure/search/search-get-started-vector
"""
import os
import json
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)

EMBEDDING_DIMENSIONS = 1536
INDEX_NAME = "building-specs"


def create_index(search_endpoint):
    """Create the search index with vector fields."""
    credential = DefaultAzureCredential()

    index = SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(name="style", type=SearchFieldDataType.String,
                          filterable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=EMBEDDING_DIMENSIONS,
                vector_search_profile_name="my-vector-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="my-hnsw")],
            profiles=[
                VectorSearchProfile(
                    name="my-vector-profile",
                    algorithm_configuration_name="my-hnsw",
                )
            ],
        ),
    )

    index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
    index_client.create_or_update_index(index)
    print(f"Index '{INDEX_NAME}' created/updated.")
    return index_client


def upload_documents(search_endpoint, docs_path):
    """Upload building spec documents to the search index."""
    credential = DefaultAzureCredential()

    if not os.path.exists(docs_path):
        # Create sample documents
        sample_docs = [
            {
                "id": "1",
                "title": "Historic European Townhouse",
                "content": (
                    "A 3-story historic European townhouse with masonry facade, "
                    "peaked roof, commercial ground floor, and residential upper "
                    "floors. Features dentil cornice, window sills, and awning. "
                    "Colors: dark tan primary, sand green secondary."
                ),
                "style": "historic",
                "content_vector": [0.0] * EMBEDDING_DIMENSIONS,
            },
            {
                "id": "2",
                "title": "Modern Office Building",
                "content": (
                    "A 2-story modern office building with smooth facade, flat "
                    "roof, and glass curtain wall. Features rooftop terrace. "
                    "Colors: light bluish gray primary, white secondary."
                ),
                "style": "modern",
                "content_vector": [0.0] * EMBEDDING_DIMENSIONS,
            },
            {
                "id": "3",
                "title": "Industrial Warehouse",
                "content": (
                    "A single-story industrial warehouse with corrugated facade, "
                    "peaked roof, and roller door. Features loading dock and "
                    "ventilation. Colors: dark bluish gray primary."
                ),
                "style": "industrial",
                "content_vector": [0.0] * EMBEDDING_DIMENSIONS,
            },
        ]
        os.makedirs(os.path.dirname(docs_path) or ".", exist_ok=True)
        with open(docs_path, "w") as f:
            json.dump(sample_docs, f, indent=2)
        print(f"Created sample documents at {docs_path}")
        docs = sample_docs
    else:
        with open(docs_path) as f:
            docs = json.load(f)

    search_client = SearchClient(
        endpoint=search_endpoint, index_name=INDEX_NAME, credential=credential
    )
    result = search_client.upload_documents(documents=docs)
    print(f"Uploaded {len(result)} documents to index '{INDEX_NAME}'.")


def main():
    search_endpoint = os.environ["SEARCH_ENDPOINT"]
    docs_path = "../../data/scenario4/building_specs.json"

    print("1. Creating search index...")
    create_index(search_endpoint)

    print("2. Uploading documents...")
    upload_documents(search_endpoint, docs_path)

    print("\nRAG index setup complete.")


if __name__ == "__main__":
    main()
