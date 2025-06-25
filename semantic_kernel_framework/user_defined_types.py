from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatHistory
import json

class SearchResult(BaseModel):
    id: Optional[str]
    part_title: Optional[str]
    chapter_title: Optional[str]
    section_title: Optional[str]
    para: Optional[str]
    summary: Optional[str]
    part_id: Optional[str]
    chapter_id: Optional[str]
    section_id: Optional[str]


class PaypalSearchResult(BaseModel):
    id: Optional[str]
    fileName: Optional[str]
    content: Optional[str]
  
class PaypalResult(BaseModel):
    search_results: list[PaypalSearchResult] = []
    user_query: str = ""
    
class RagStepInput(BaseModel):
    search_results: list[PaypalSearchResult] = []
    user_query: str = ""

class QueryType(str, Enum):
    OFF_TOPIC = "Off-topic"
    SMALL_TALK = "Small talk"
    SEARCH_GENERIC = "Search Generic"
    SEARCH_PERSONAL = "Search Personal"

class QueryFilteringResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_query_offensive: bool
    is_language_supported: bool

class CondensedQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    condensed_query: str
    language: str
    is_condensed: bool

class QueryTypeClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_type: QueryType

class Validation_Response(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_filtering_result: QueryFilteringResult
    condensed_query: CondensedQuery
    query_type_classification: QueryTypeClassification


def build_chat_history(history: list[any], system_message: str) -> ChatHistory:
    """
    Builds a chat history string from a list of messages.
    """
    chat_history = ChatHistory(system_message=system_message)
    for msg in history:
        if msg["role"] == "user":
            chat_history.add_user_message(msg["message"])
        elif msg["role"] == "assistant":
            chat_history.add_assistant_message(json.dumps(msg["message"]))
    
    return chat_history