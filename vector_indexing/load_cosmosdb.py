# %%
import asyncio
import json
import os
import uuid

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()

print(f"Using Cosmos DB endpoint: {os.getenv('AZURE_COSMOSDB_ENDPOINT')}")

# Initialize the Cosmos client
client = CosmosClient(os.getenv("AZURE_COSMOSDB_ENDPOINT"), credential=AzureCliCredential())
database_name = os.getenv("AZURE_COSMOSDB_DBNAME")
container_name = os.getenv("AZURE_COSMOSDB_CONTAINERNAME")

client.create_database_if_not_exists(id=database_name)
# Connect to the database and container
database = client.get_database_client(database_name)

vector_embedding_policy = {
    "vectorEmbeddings": [
        {
            "path":"/contentVector",
            "dataType":"float32",
            "distanceFunction":"cosine",
            "dimensions":1536
        }
    ]
}


vector_indexing_policy = {
    
    "indexingMode": "consistent",
    "automatic": True,
    "includedPaths": [
        {
            "path": "/*"
        }
    ],
    "excludedPaths": [
        {
            "path": "/_etag/?"
        },
        {
            "path": "/contentVector/*"
        }
        
    ],
    "fullTextIndexes": [
        {
            "path": "/content"
        }
    ],
    "vectorIndexes": [
        {
            "path": "/contentVector",
            "type": "quantizedFlat"
        }
    ]
}

full_text_paths_policy = {
   "defaultLanguage": "en-US",
   "fullTextPaths": [
       {
           "path": "/fileName",
           "language": "en-US"
       },
       {
           "path": "/content",
           "language": "en-US"
       }
   ]
}



for db in client.list_databases():
    print(db)



container = None
try:
    container = database.create_container(id=container_name, partition_key=PartitionKey(path="/id"), 
                          vector_embedding_policy=vector_embedding_policy,
                          indexing_policy=vector_embedding_policy,
                          full_text_policy=full_text_paths_policy,
                          offer_throughput=400) 
except exceptions.CosmosResourceExistsError:
    print(f"Container {container_name} already exists. Using existing container.")
    container = database.get_container_client(container_name)




json_vector_file_name = "search_docs_with_vectors.json"
async def start_processing():
    with open(json_vector_file_name, "r", encoding="utf-8") as f:
        index_data_with_vectors = json.load(f)

    for idx, doc in enumerate(index_data_with_vectors):
        search_doc = {
            "id": doc["id"],
            "fileName": doc.get("fileName", ""),
            "content": doc.get("content", ""),
            "contentVector": doc.get("contentVector") or [],
        }
        res = container.upsert_item(search_doc)


if __name__ == "__main__":
    print("Starting processing...")
    
    print("Creating or checking container...")
    if not container:
        print(f"Container {container_name} created successfully.")
    else:
        print(f"Using existing container: {container_name}")
    
    print("Processing documents and uploading to Cosmos DB...")
    asyncio.run(start_processing())
    print("Processing completed.")



