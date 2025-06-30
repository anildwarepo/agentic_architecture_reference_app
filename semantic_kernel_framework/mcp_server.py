import asyncio
import os
this_dir = os.path.dirname(os.path.abspath(__file__))
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from typing import Annotated, List, Literal, Any
import argparse
from semantic_kernel.functions.kernel_function_decorator import kernel_function
import anyio
from semantic_kernel_framework import search_helper, cosmosdb_helper
from semantic_kernel_framework.user_defined_types import PaypalResult
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion



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
        

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the Semantic Kernel MCP server.")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["sse", "stdio"],
        default="stdio",
        help="Transport method to use (default: stdio).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to use for SSE transport (required if transport is 'sse').",
    )
    return parser.parse_args()


async def run(transport: Literal["sse", "stdio"] = "stdio", port: int | None = None) -> None:
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="Host",
        instructions=(
        """
        You are a Paypal Support Triage Agent. 
        You can answer questions about Paypal Account, Transaction and Support Related Queries and nothing else.

        For Account related queries, you will delegate to the get_account_info_agent.
        For Transaction related queries, you will delegate to the get_transaction_info_agent.
        For all other queries, you will delegate to the rag_agent.
        You need to handle user queries and delegate them to the appropriate agents.
        You will use the query_validator_agent to validate the user query and classify it into one of the following types:
        - Off-topic
        - Small talk
        - Search Generic
        - Search Personal
        If the query is valid and classified as Search Generic or Search Personal, you will delegate it to the rag_agent.
        If the query is classified as Off-topic or Small talk, you will respond with a message indicating that the query is not valid for support.
        If the query is not in English or Spanish, you will respond with a message indicating that the query is not supported.
        If the query is offensive or contains inappropriate content, you will respond with a message indicating that the query is not valid.
        Do not ask clarifying questions, always use the agents to answer the queries.
        """
    ),
        plugins=[AccountPlugins(), SearchPlugins()],  # add the sample plugin to the agent
    )

    server = agent.as_mcp_server()

    if transport == "sse" and port is not None:
        import nest_asyncio
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from starlette.responses import Response  

        sse = SseServerTransport("/sse")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as (
                read_stream,
                write_stream,
            ):
                await server.run(read_stream, write_stream, server.create_initialization_options())

            return Response(status_code=204)  


        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/", app=sse.handle_post_message),
            ],
        )
        nest_asyncio.apply()
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)  # nosec
    elif transport == "stdio":
        from mcp.server.stdio import stdio_server

        async def handle_stdin(stdin: Any | None = None, stdout: Any | None = None) -> None:
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, server.create_initialization_options())

        await handle_stdin()


if __name__ == "__main__":
    args = parse_arguments()
    print("Starting Semantic Kernel MCP server...")
    anyio.run(run, args.transport, args.port)