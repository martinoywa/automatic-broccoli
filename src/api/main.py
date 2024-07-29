from fastapi import FastAPI, APIRouter
from langchain_community.llms.ollama import Ollama
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from src.api.models.models import AIResponse

# AI Prompt Template and Chain
print("Loading LLM")
llm = Ollama(model="llama2")

qa_system_prompt = """You are an assistant for question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise."""

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])
output_parser = StrOutputParser()

chain = qa_prompt | llm | output_parser

# Transcript
processed_chat_history = []  # TODO fetch from session store
transcript_memory = {}
session_store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]


chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# Fast API
app = FastAPI()
router = APIRouter()
prefix = "/api/v1"


def process_chat_history(human, ai):
    """
    Function to process chat history for payload.
    Addedd as cannot have Langchain type in pydantic v2.
    May not be necessary as /chathistory endpoint returns data well.
    :param human:
    :param ai:
    :return:
    """
    processed_chat_history.append((human, ai))


def update_transcript(session_id, text, role="Human:"):
    if transcript_memory.get(session_id):
        transcript_memory[session_id].append(f"{role} {text}")
    else:
        transcript_memory[session_id] = [f"{role} {text}"]


@router.get("/")
async def home():
    return {"message": "Voice Chatbot with LLM"}


@router.post("/chat", response_model=AIResponse)
async def chat(message: str, session_id: str):
    response = chain_with_history.invoke(
        {"input": message},
        config={"configurable": {"session_id": session_id}}
    )
    if response[:3] == "AI:":  # LLM sometimes adds this.
        response = response[3:]

    # update transcript
    update_transcript(session_id, message)
    update_transcript(session_id, response, role="AI Assisstant:")

    return {
            "response": response
    }


@router.get("/chathistory")
async def chat_history(session_id: str):
    return {"chat_history": session_store.get(session_id)}


@router.post("/deltechathisory")
async def delete_chat_history(session_id: str):
    del session_store[session_id]
    return {"message": "Chat History Cleared"}


@router.get("/transcript")
async def transcript(session_id: str):
    return {"transcript": transcript_memory.get(session_id)}


@router.post("/deltetranscript")
async def delete_transcript():
    transcript_memory.clear()
    return {"message": "Transcript Cleared"}


app.include_router(router, prefix=prefix)
