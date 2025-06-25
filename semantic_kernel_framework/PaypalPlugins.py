import os
from typing import Annotated, List

import search_helper
from user_defined_types import *

from semantic_kernel.functions.kernel_function_decorator import kernel_function

this_dir = os.path.dirname(os.path.abspath(__file__))

# Correct path to sample_data (which is a sibling of sk_streaming)
sample_data_path = os.path.join(this_dir, "..", "sample_data")
sample_data_path = os.path.abspath(sample_data_path)  # resolve full path


class PaypalPlugins:

    @kernel_function
    def get_account_info(self, account_id: str) -> str:
        """Get account information for the given account ID."""
        try:
            account_data_file = os.path.join(sample_data_path, f"{account_id}.json")
            with open(account_data_file, "r") as file:
                data = file.read()
            return data
        except FileNotFoundError:
            return "Account not found."

    @kernel_function
    def get_transaction_details(self, account_id: str) -> str:
        """Get transaction details for the given account ID."""
        try:
            txn_data_file = os.path.join(sample_data_path, f"Txn_{account_id}.json")
            with open(txn_data_file, "r") as file:
                data = file.read()
            return data
        except FileNotFoundError:
            return "Transaction details not found."


        
    @kernel_function(description="Searches the index with the user query and returns the results.")
    async def get_search_results(self, search_query: Annotated[str, "user query"]): 
        results = await search_helper.retrieve_search_results(search_query=search_query)

        paypalResults = PaypalResult(
            search_results=results,
            user_query=search_query
        )
        return paypalResults.model_dump(mode="json", exclude_none=True)
        

