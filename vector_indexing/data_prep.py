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

token_provider = get_bearer_token_provider(
    azcli_credential,
    "https://cognitiveservices.azure.com/.default"
)

aoai_client = AzureOpenAI(
   api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
   azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
   azure_ad_token_provider=token_provider,   
)

json_vector_file_name = "search_docs_with_vectors.json"

def generate_embeddings_sync(text_list, model="text-embedding-ada-002"):
    try:
        # Send a batch of texts to the embedding API
        if text_list is None or len(text_list) == 0:
            return []
        #print("embedding model:", model)
        embeddings = aoai_client.embeddings.create(input=text_list, model=model).data
        return embeddings
    
    except RateLimitError as e:
        print("Rate limit reached (429 error).")
        raise
    
    except Exception as e:
        print("Error calling OpenAI:" + str(aoai_client.base_url))
        print(e)
        raise

def generate_embeddings(doc, fieldName, max_retries=5, base_delay=15):
    # Extract fields
    try:
        
        content = doc.get(fieldName, "")
        

        # Function to attempt embedding generation with retry logic
        def generate_with_retries(data, model):
            retries = 0
            while retries < max_retries:
                try:
                    if type(data) == list:
                        cleaned_data = [item for item in data if item is not None]
                        cleaned_data_string = ", ".join(cleaned_data)
                        return generate_embeddings_sync(cleaned_data_string, model=model)
                    else:
                        return generate_embeddings_sync(data, model=model)

                except Exception as e:
                    retries += 1
                    delay = base_delay * (2 ** (retries - 1))  # Exponential backoff
                    print(f"Retry {retries}. Waiting {delay} seconds before retrying...")
                    time.sleep(delay)
            print(f"Failed to generate embeddings after {max_retries} attempts.")
            return None

        # Generate embeddings for each part, chapter, section, keywords, para, topics, summary, category
        content_embeddings = generate_with_retries(content, os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"))
        
        # Update document with embeddings
        doc[f"{fieldName}Vector"] = content_embeddings[0].embedding if content_embeddings else None
        
        print(f"Embedded document: {doc.get('id', 'unknown')}")
        return doc
    except Exception as e:
        with open("embedding_error.log", "a") as f:
            f.write(str(doc) + "\n")
        print(f"generate_embeddings_for_doc Error processing document: {e}")
        doc[f"{fieldName}Vector"] = None
        doc["embedding_error"] = str(e)
    return doc


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




def process_search_docs():
    search_docs_folder_path = "search_docs"
    search_docs_json = []
    if not os.path.exists("search_docs.json") or os.path.getsize("search_docs.json") == 0:
        for file in os.listdir(search_docs_folder_path):
            if file.endswith(".txt"):
                print(f"Processing file: {file}")
                with open(os.path.join(search_docs_folder_path, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    json_doc = {
                        "id": str(uuid.uuid4()),
                        "filename": file,
                        "content": content
                    }
                    search_docs_json.append(json_doc)

        with open("search_docs.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(search_docs_json, indent=2, ensure_ascii=False))
    else:
        print("search_docs.json already exists and is not empty. Skipping initial processing.")

    if not os.path.exists(json_vector_file_name):
        with open("search_docs.json", "r", encoding="utf-8") as f:
            search_docs_json = json.loads(f.read())

        vectorized_docs = []
        for doc in search_docs_json:
            doc = generate_embeddings(doc, "content")
            
            if doc:
                vectorized_docs.append(doc)
            else:
                print(f"Failed to process document: {doc.get('id', 'unknown')}")

            with open(json_vector_file_name, "w", encoding="utf-8") as f:
                    json.dump(vectorized_docs, f, indent=2, ensure_ascii=False)
            
    else:
        print(f"{json_vector_file_name} already exists. Skipping embedding generation.")


if __name__ == "__main__":
    
    print("Starting processing...")
    print("Processing search documents...")
    process_search_docs()
    print("Data Prep completed.")

