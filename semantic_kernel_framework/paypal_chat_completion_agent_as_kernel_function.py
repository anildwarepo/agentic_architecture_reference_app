# Copyright (c) Microsoft. All rights reserved.

import asyncio

from PaypalPlugins import PaypalPlugins

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.filters import FunctionInvocationContext
from semantic_kernel.prompt_template.prompt_template_config import \
    PromptTemplateConfig

"""
The following sample demonstrates how to create Chat Completion Agents
and use them as tools available for a Triage Agent to delegate requests
to the appropriate agent. A Function Invocation Filter is used to show
the function call content and the function result content so the caller
can see which agent was called and what the response was.
"""


# Define the auto function invocation filter that will be used by the kernel
async def function_invocation_filter(context: FunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    if "messages" not in context.arguments:
        await next(context)
        return
    print(f"    Agent [{context.function.name}] called with messages: {context.arguments['messages']}")
    await next(context)
    print(f"    Response from agent [{context.function.name}]: {context.result.value}")


# Create and configure the kernel.
kernel = Kernel()

# The filter is used for demonstration purposes to show the function invocation.
#kernel.add_filter("function_invocation", function_invocation_filter)


prompt_template = PromptTemplateConfig()

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
    service=AzureChatCompletion(),
)
rag_agent = ChatCompletionAgent(
    name="rag_agent",
    instructions=(
        """
            You are a paypal support agent. You need to answer users questions about paypal in English or Spanish language.
            These are the domains you can answer: Disputes, Refunds, Support.
            You will search only if the query is validated by query_validator_agent.
            You will provide the answer if you can answer based on the results of the search from the start_rag_process tool.
            If you cannot answer the question, you will respond with a message indicating that you cannot answer the question.
            Just provide the answer to the user question and nothing else. Always use the same language as the user query. 
            Default to English if the language is not supported. 
            """
    ),
    service=AzureChatCompletion(),
    plugins=[PaypalPlugins()]
)

triage_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    kernel=kernel,
    name="SupportTriageAgent",
    instructions=(
        """
        You are a Paypal Support Triage Agent. You need to handle user queries and delegate them to the appropriate agents.
        You will use the query_validator_agent to validate the user query and classify it into one of the following types:
        - Off-topic
        - Small talk
        - Search Generic
        - Search Personal
        If the query is valid and classified as Search Generic or Search Personal, you will delegate it to the rag_agent.
        If the query is classified as Off-topic or Small talk, you will respond with a message indicating that the query is not valid for support.
        If the query is not in English or Spanish, you will respond with a message indicating that the query is not supported.
        If the query is offensive or contains inappropriate content, you will respond with a message indicating that the query is not valid.
        
        """
    ),
    plugins=[query_validator_agent, rag_agent],
)

thread: ChatHistoryAgentThread = None


async def chat() -> bool:
    """
    Continuously prompt the user for input and show the assistant's response.
    Type 'exit' to exit.
    """
    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input.lower().strip() == "exit":
        print("\n\nExiting chat...")
        return False

    #response = await triage_agent.get_response(
    #    messages=user_input,
    #    thread=thread,
    #)
    
    response = triage_agent.invoke_stream(messages=user_input, thread=thread)

    async for message in response:
        print(message)




    #if response:
    #    print(f"Agent :> {response}")

    return True





async def main() -> None:
    print("Welcome to the chat bot!\n  Type 'exit' to exit.\n .")
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
