from typing import List, Union, Dict, Tuple

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from pydantic import BaseModel


class HumanResponse(BaseModel):
    name: str
    response: str


class AIResponse(BaseModel):
    # name: str
    response: str
    # chat_history: List[Tuple[str, str]]
