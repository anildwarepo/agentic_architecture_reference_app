import asyncio
import os
from typing import Annotated, List

from semantic_kernel.functions.kernel_function_decorator import kernel_function

from semantic_kernel_framework import search_helper, cosmosdb_helper
from semantic_kernel_framework.user_defined_types import PaypalResult

this_dir = os.path.dirname(os.path.abspath(__file__))

# Correct path to sample_data (which is a sibling of sk_streaming)
sample_data_path = os.path.join(this_dir, "..", "sample_data")
sample_data_path = os.path.abspath(sample_data_path)  # resolve full path


class AccountPlugins:

    @kernel_function
    def get_account_info(self, account_id: Annotated[str, "Customer’s 10 alphanumeric account ID or account number"]) -> str:
        """Get account information for the given account ID."""
        try:
            account_data_file = os.path.join(sample_data_path, f"{account_id}.json")
            with open(account_data_file, "r") as file:
                data = file.read()
            return data
        except FileNotFoundError:
            return "Account not found."

    @kernel_function
    def get_transaction_details(self, account_id: Annotated[str, "Customer’s 10 alphanumeric account ID or account number"]) -> str:
        """Get transaction details for the given account ID."""
        try:
            txn_data_file = os.path.join(sample_data_path, f"Txn_{account_id}.json")
            with open(txn_data_file, "r") as file:
                data = file.read()
            return data
        except FileNotFoundError:
            return "Transaction details not found."


class SearchPlugins:
        
    @kernel_function(
        name="get_search_results",
        description="Search PayPal KB and return results."
                            # ← tell SK it's an async tool
    )
    async def get_search_results(
        self,
        search_query: Annotated[str, "user query"],
    ) -> str:
        print(f"Search query: {search_query}")
        
        try:
            search_engine = os.getenv("SEARCH_DB_TO_USE").lower()
            if search_engine not in ["cosmosdb", "azureaisearch"]:
                return f"Invalid search engine specified: {search_engine}. Supported engines are 'cosmosdb' and 'azureaisearch'."
            if search_engine == "cosmosdb":
                print("Using CosmosDB for search")
                
                results = await cosmosdb_helper.search_with_rrf(
                    search_query=search_query
                )
            elif search_engine == "azureaisearch":
                print("Using Azure AI Search for search")
                results = await search_helper.retrieve_search_results(
                    search_query=search_query
                )
            return (
                PaypalResult(
                    search_results=results,
                    user_query=search_query,
                )
                .model_dump_json(exclude_none=True)      # string, not dict
            )
        except Exception as e:
            print(f"Error during search: {e}")
            return f"An error occurred while searching"
        

