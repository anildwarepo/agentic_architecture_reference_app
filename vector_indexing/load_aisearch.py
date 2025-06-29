import json
import os
import time
import uuid

import requests
from azure.identity import AzureCliCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from openai import AzureOpenAI, RateLimitError

load_dotenv()

azcli_credential = AzureCliCredential()
json_vector_file_name = "search_docs_with_vectors.json"

def create_simple_index(index_name: str, analyzer_name: str = "en.microsoft", language_suffix: str = "en"):
    index_schema = {
        "name": index_name,
        "fields": [
            {
                "name": "id",
                "type": "Edm.String",
                "key": True,
                "sortable": True,
                "filterable": True,
                "facetable": True
            },
            {
                "name": "content",
                "type": "Edm.String",
                "searchable": True
            },
            {
                "name": "fileName",
                "type": "Edm.String",
                "searchable": True
            },
            {
                "name": "contentVector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "dimensions": 1536,
                "vectorSearchProfile": "amlHnswProfile"
            }
        ],
        "scoringProfiles": [],
        "suggesters": [],
        "vectorSearch": {
            "algorithms": [
                {
                    "name": "amlHnsw",
                    "kind": "hnsw",
                    "hnswParameters": {
                        "m": 4,
                        "metric": "cosine"
                    }
                }
            ],
            "profiles": [
                {
                    "name": "amlHnswProfile",
                    "algorithm": "amlHnsw"
                }
            ],
            "vectorizers": []
        },
        "semantic": {
            "configurations": [
                {
                    "name": "aml-semantic-config",
                    "prioritizedFields": {
                        "titleField": {"fieldName": "content"},
                        "prioritizedKeywordsFields": [{"fieldName": "content"}],
                        "prioritizedContentFields": [{"fieldName": "content"}]
                    }
                }
            ]
        }
    }

    # get bearer token for Azure Search

    token = azcli_credential.get_token("https://search.azure.com/.default")
    if not token:
        print("❌ Failed to get token for Azure Search.")
        return
    

    headers = {'Content-Type': 'application/json',
                'Authorization': f"Bearer {token.token}"}
    

    

    url = f"{os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")}/indexes/{index_name}?api-version=2024-07-01"

    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        create_response = requests.put(url, headers=headers, json=index_schema)
        if create_response.status_code in [200, 201]:
            print("✅ Index created successfully.")
        else:
            print("❌ Failed to create index:", create_response.text)
    elif response.status_code == 200:
        print("ℹ️ Index already exists.")
    else:
        print("❌ Unexpected error while checking index:", response.text)


def upload_to_search_simple(index_name):
    with open(json_vector_file_name, "r", encoding="utf-8") as f:
        index_data_with_vectors = json.load(f)

    search_client = SearchClient(endpoint=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"), index_name=index_name, credential=azcli_credential)

    for idx, doc in enumerate(index_data_with_vectors):
        search_doc = {
            "id": doc["id"],
            "fileName": doc.get("fileName", ""),
            "content": doc.get("content", ""),
            "contentVector": doc.get("contentVector") or [],
        }

        result = search_client.upload_documents(documents=[search_doc])
        print(f"Uploaded document: {doc['id']} - {idx + 1}")

    print(f"{len(index_data_with_vectors)} Documents uploaded to Azure Search")




if __name__ == "__main__":
    
    print("Starting processing...")
    print("Creating or checking index...")
    create_simple_index("search_docs_index")
    print("Uploading documents to Azure Search...")
    upload_to_search_simple("search_docs_index")
    print("Processing completed.")

