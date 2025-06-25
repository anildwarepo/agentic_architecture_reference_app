import asyncio
from typing import Any, AsyncGenerator

from semantic_kernel_framework.AgentPlugins import AccountPlugins, SearchPlugins
from azure.identity.aio import (AzureDeveloperCliCredential,
                                DefaultAzureCredential,
                                get_bearer_token_provider)
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion, AzureChatPromptExecutionSettings)
from semantic_kernel.connectors.ai.prompt_execution_settings import \
    PromptExecutionSettings
from semantic_kernel.contents import (ChatMessageContent, FunctionCallContent,
                                      FunctionResultContent)
from semantic_kernel.filters import FunctionInvocationContext
from semantic_kernel.prompt_template.prompt_template_config import \
    PromptTemplateConfig

from semantic_kernel_framework.observability_helper import set_up_observability

set_up_observability()

aoai_credential =  AzureDeveloperCliCredential() # login with azd login # DefaultAzureCredential()
token_provider = get_bearer_token_provider(aoai_credential, "https://cognitiveservices.azure.com/.default")

"""
The following sample demonstrates how to create Chat Completion Agents
and use them as tools available for a Triage Agent to delegate requests
to the appropriate agent. A Function Invocation Filter is used to show
the function call content and the function result content so the caller
can see which agent was called and what the response was.
"""


# Create and configure the kernel.
kernel = Kernel()

RAG_AGENT_SERVICE_ID = "rag_agent"
QUERY_VALIDATOR_AGENT_SERVICE_ID = "query_validator_agent"
TRIAGE_AGENT_SERVICE_ID = "triage_agent"
ACCOUNT_AGENT_SERVICE_ID = "get_account_info_agent"
TRANSACTION_AGENT_SERVICE_ID = "get_transaction_info_agent"



def get_azure_chat_completion(service_id) -> AzureChatCompletion:
    """
    Creates an instance of AzureChatCompletion with the necessary credentials.
    """
    return AzureChatCompletion(
        ad_token_provider=token_provider,
        service_id=service_id

    )




# Define the auto function invocation filter that will be used by the kernel
async def function_invocation_filter(context: FunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    if "messages" not in context.arguments:
        await next(context)
        return
    print(f"    Agent [{context.function.name}] called with messages: {context.arguments['messages']}")
    await next(context)
    print(f"    Response from agent [{context.function.name}]: {context.result.value}")




# The filter is used for demonstration purposes to show the function invocation.
kernel.add_filter("function_invocation", function_invocation_filter)


prompt_template_config = PromptTemplateConfig(
    execution_settings=AzureChatPromptExecutionSettings(max_tokens=4000, 
                                                        temperature=0, 
                                                        store=True, 
                                                        metadata={"service_id": RAG_AGENT_SERVICE_ID},
                                                        tool_choice="auto",
                                                        function_choice_behavior=FunctionChoiceBehavior.Auto())  # <-- let the model pick tools,
)

get_account_info_agent = ChatCompletionAgent(
    name="get_account_info_agent",
    instructions="""You are PayPal Support Agent. PayPal is an online payment platform.
        
        You can provide information about the account details such as credit card balance. 
        You will provide the information only if the query has been validated by query_validator_agent.
        You need to know the 'account number' to provide the account details.

        If the 'account number' is provided use the get_account_info tool to get the account details.
        Format the response with 'Account Details:'.
        If the 'account number' is not provided, ask the user to provide the 'account number'.
        Just provide the answer to the user question and nothing else
    """,
    service=get_azure_chat_completion(service_id=ACCOUNT_AGENT_SERVICE_ID),
    plugins=[AccountPlugins()],
    function_choice_behavior=FunctionChoiceBehavior.Auto(
        auto_invoke=True)
)

get_transaction_info_agent = ChatCompletionAgent(
    name="get_transaction_info_agent",
    instructions="""You are PayPal Support Agent. PayPal is an online payment platform.
        You can provide information about the transaction details for the account.
        You will provide the information only if the query has been validated by query_validator_agent.
        You need to know the 'account number' to provide the transaction details.
        If the 'account number' is provided use the get_transaction_details tool to get the transaction details.
        Format the response with 'Transaction Details:'.
        If the 'account number' is not provided, ask the user to provide the 'account number'.
        Just provide the answer to the user question and nothing else
    """,
    service=get_azure_chat_completion(service_id=TRANSACTION_AGENT_SERVICE_ID),
    plugins=[AccountPlugins()],
    function_choice_behavior=FunctionChoiceBehavior.Auto(
        auto_invoke=True)
)

query_validator_agent = ChatCompletionAgent(
    name="query_validator_agent",
    instructions=(
        """You are user input validator agent.
        Your task is to validate the user query based on the following criteria:
        1. Check if the query is offensive or contains inappropriate content. Not valid if it does.
        2. Check if the query is in a supported language.Only English & Spanish is supported. Not valid for other languages.
        3. Condense the query to a more concise form if possible based on the previous user question from chat history.
        4. Classify the query into one of the following types: Off-topic, Small talk, Search Generic, Search Personal.
        """
    ),
    service=get_azure_chat_completion(service_id=QUERY_VALIDATOR_AGENT_SERVICE_ID),
)

rag_agent = ChatCompletionAgent(
    name="rag_agent",
    prompt_template_config=prompt_template_config,
    instructions=(
        """
            You are a paypal support agent.
            You will use the get_search_results tool to search the knowledge base for the user query. 
            You will search only if the query is validated by query_validator_agent.
            You need to answer users questions about paypal in English or Spanish language.
            These are the domains you can answer: Disputes, Refunds, Support.
            If you cannot answer the question based on the search results, you will respond with a message indicating that you cannot answer the question.
            Just provide the answer to the user question and nothing else. Always use the same language as the user query. 
            Default to English if the language is not supported. 
            Do not ask clarifying questions.
            """
    ),
    service=get_azure_chat_completion(service_id=RAG_AGENT_SERVICE_ID),
    plugins=[SearchPlugins()],
    function_choice_behavior=FunctionChoiceBehavior.Auto(
        auto_invoke=True)
)



triage_agent = ChatCompletionAgent(
    service=get_azure_chat_completion(service_id=TRIAGE_AGENT_SERVICE_ID),
    kernel=kernel,
    name="SupportTriageAgent",
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
    plugins=[query_validator_agent, rag_agent, get_account_info_agent, get_transaction_info_agent],
)

async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        else:
            print(f"{message.role}: {message.content}")

class MultiAgent:
    def __init__(self):
        self.thread = ChatHistoryAgentThread()


    async def start_multi_agent_chat_stream(self, user_input: str) -> AsyncGenerator[str, Any]:
        try:
            stream_response = triage_agent.invoke_stream(messages=user_input, 
                                          thread=self.thread,
                                          on_intermediate_message=handle_streaming_intermediate_steps)
            return stream_response

        except Exception as e:
            print("Error in multi agent chat: ", e)

