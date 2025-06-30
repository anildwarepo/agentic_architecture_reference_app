import asyncio
import os
from pathlib import Path
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from azure.identity.aio import (AzureDeveloperCliCredential,
                                DefaultAzureCredential,
                                AzureCliCredential,
                                get_bearer_token_provider)



aoai_credential =  AzureCliCredential() # login with azd login # DefaultAzureCredential()
token_provider = get_bearer_token_provider(aoai_credential, "https://cognitiveservices.azure.com/.default")

def get_azure_chat_completion(service_id) -> AzureChatCompletion:
    """
    Creates an instance of AzureChatCompletion with the necessary credentials.
    """
    return AzureChatCompletion(
        ad_token_provider=token_provider,
        service_id=service_id

    )

async def main():
    async with MCPStdioPlugin(name="SupportPlugins",
                            description="Paypal Support plugins",
                            command="uv",
                            args=[
                                f"--directory={str(Path(os.path.dirname(__file__)).joinpath('.'))}",
                                "run",
                                "mcp_server.py",
                            ],
                            ) as plugin:
        support_agent = ChatCompletionAgent(
            service=get_azure_chat_completion("support-agent"),
            name="SupportAgent",
            instructions="You are a support agent. Answer questions about PayPal.",
            plugins=[plugin],
        )

        thread: ChatHistoryAgentThread | None = None
        while True:
            user_input = input("User: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            response = await support_agent.get_response(messages=user_input, thread=thread)
            print(f"# {response.name}: {response} ")
            thread = response.thread

if __name__ == "__main__":
    asyncio.run(main())