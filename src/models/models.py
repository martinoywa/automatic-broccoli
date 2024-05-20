from typing import List, Union

from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel


class HumanResponse(BaseModel):
    name: str
    response: str


class AIResponse(BaseModel):
    name: str
    response: str
    chat_history: List[Union[AIMessage, HumanMessage]]
