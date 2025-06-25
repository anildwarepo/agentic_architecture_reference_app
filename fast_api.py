import asyncio
import typing
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from semantic_kernel.contents import (StreamingChatMessageContent,
                                      StreamingTextContent)

from semantic_kernel_framework.AgentSessionManager import \
    MultiAgentSessionManager
from semantic_kernel_framework.paypal_agent_implementation import MultiAgent

app = FastAPI()

class ChatRequest(BaseModel):
    user_message: str
    conversation_id: str


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/status/items/{item_id}")
def read_item(item_id: int):
    return {"status": f"healthy: item {item_id} is healthy"}



multi_agent_session_manager: MultiAgentSessionManager[MultiAgent] = (
    MultiAgentSessionManager(MultiAgent)        # ← factory goes here
)



@app.post("/multi_agent_chat/")
async def multi_agent_chat_with_user(request: ChatRequest):
    sk_multiagent_instance = multi_agent_session_manager.get_or_create_session(conversation_id=request.conversation_id) 


    token_stream = await sk_multiagent_instance.start_multi_agent_chat_stream(user_input=request.user_message)
    async def stream_tokens():
        async for chunk in token_stream:
            if not isinstance(chunk, StreamingChatMessageContent):
                yield str(chunk)
                continue
            if chunk.content:                      
                yield chunk.content
            else:                                  
                for item in chunk.items:
                    if isinstance(item, StreamingTextContent) and item.text:
                        yield item.text

    return StreamingResponse(stream_tokens(), media_type="text/plain")

