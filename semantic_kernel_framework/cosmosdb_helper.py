import asyncio
import os

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.identity import AzureCliCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import AzureOpenAI, RateLimitError
from semantic_kernel_framework.user_defined_types import *
from typing import List

load_dotenv()

print(f"Using Cosmos DB endpoint: {os.getenv('AZURE_COSMOSDB_ENDPOINT')}")

# Initialize the Cosmos client
client = CosmosClient(os.getenv("AZURE_COSMOSDB_ENDPOINT"), credential=AzureCliCredential())
database_name = os.getenv("AZURE_COSMOSDB_DBNAME")
container_name = os.getenv("AZURE_COSMOSDB_CONTAINER_NAME")

client.create_database_if_not_exists(id=database_name)
# Connect to the database and container
database = client.get_database_client(database_name)
embedding_model = "text-embedding-ada-002" 

container = database.get_container_client(container_name)
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

if not container:
    print(f"Container '{container_name}' does not exist.")
    exit(1)


async def generate_embeddings_sync(text_list, model="text-embedding-ada-002"):
    try:
        # Send a batch of texts to the embedding API
        if text_list is None or len(text_list) == 0:
            return []
        #print("embedding model:", model)
        embeddings = aoai_client.embeddings.create(input=text_list, model=model)
        return embeddings.data[0].embedding
    
    except RateLimitError as e:
        print("Rate limit reached (429 error).")
        raise
    
    except Exception as e:
        print("Error calling OpenAI:" + str(aoai_client.base_url))
        print(e)
        raise

async def get_vector_search_results(search_query, top_k=5, threshold=0.7):
    embedding_result = await generate_embeddings_sync([search_query], model=embedding_model)
    search_query_embedded = embedding_result # embedding_result[0].embedding
    items = container.query_items( 
        query="""
        SELECT top @top_k c.fileName, c.content, VectorDistance(c.contentVector, @embedding) AS textSimilarityScore 
        FROM c
        WHERE VectorDistance(c.contentVector, @embedding) > @threshold
        ORDER BY VectorDistance(c.contentVector, @embedding) 
        """, 
        parameters=[
            {"name": "@embedding", "value": search_query_embedded},
            {"name": "@top_k", "value": top_k},
            {"name": "@threshold", "value": threshold}
        ], 
        enable_cross_partition_query=True)
    results = [item for item in items]
    return results

    


async def get_fulltext_search_results(search_query, top_k=5):
    #print(search_query_arr)
    query_string = f"""
    SELECT TOP {top_k} c.content
    FROM c
    ORDER BY RANK FullTextScore(c.content, '{search_query}')
    """

    items = container.query_items(
        query=query_string,
        parameters=[],
        enable_cross_partition_query=True
    )

    try:
        item_files = [item for item in items]
    except Exception as e:
        print(f"Error in query: {e}")
        item_files = []

    return item_files




async def search_with_rrf(search_query, top_k=5, threshold=0.7):
    embedding_result = await generate_embeddings_sync([search_query], model=embedding_model)
    search_query_embedded = embedding_result  # already a list of floats
    try:
        items = container.query_items(
            query=f"""
            SELECT TOP {top_k} c.fileName, c.content
            FROM c
            ORDER BY RANK RRF(
                FullTextScore(c.content, '{search_query}'),
                VectorDistance(c.contentVector, {search_query_embedded})
            )
            """,
            parameters=[],
            enable_cross_partition_query=True
        )
        search_results: List[PaypalSearchResult] = []
        for item in items:
            single_result = {}
            single_result['id'] = item.get('id', '')
            single_result['fileName'] = item.get('fileName', '')
            single_result['content'] = item.get('content', '')
            search_results.append(PaypalSearchResult(**single_result))
        return search_results
        
    except Exception as e:
        print(f"Error in query: {e}")
        return []


if __name__ == "__main__":
    question = "dispute"
    print(f"Searching for: {question}")
    
    #items = asyncio.run(search_with_rrf(question, top_k=5, threshold=0.7))
    #items = asyncio.run(get_vector_search_results(question, top_k=5, threshold=0.7))
    items = asyncio.run(get_fulltext_search_results(question, top_k=5))

    for item in items:
        print(item)