from crypt import methods

from fastapi import FastAPI, APIRouter
from langchain_community.llms.ollama import Ollama
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from src.api.database.db import save_message, load_session_history, delete_session_history
from src.api.models.models import AIResponse, MessageRequest

# AI Prompt Template and Chain
print("Loading LLM")
llm = Ollama(model="llama3.1")

qa_system_prompt = """Your name is Convo. This is how you'll be referred to by the user.
You are an assistant and/or companion for turn-based conversations or question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.""" # TODO update the system prompt to fit the usecase.

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])
output_parser = StrOutputParser()

chain = qa_prompt | llm | output_parser
session_store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = load_session_history(session_id)
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


def generate_transcript(session_id):  # TODO unable to load last messages, format different db values
    transcript_memory = []
    history = chain_with_history.get_session_history(session_id).messages
    if len(history) > 0:
        for message in history:
            try:
                transcript_memory.append(f"{message['role']}: {message['content']}")
            except TypeError:
                pass
    return transcript_memory


# def update_transcript(session_id, text, role="Human:"):
#     if transcript_memory.get(session_id):
#         transcript_memory[session_id].append(f"{role} {text}")
#     else:
#         transcript_memory[session_id] = [f"{role} {text}"]

@router.get("/")
async def home():
    return {"message": "Conversation.ai LLM-based Backend"}


@router.post("/test/chat", response_model=AIResponse)
async def chat(message: MessageRequest):
    print(message.text, message.session_id)
    return {"response": "Hello there! Hope you're doing well. This is a test response"}


@router.post("/chat", response_model=AIResponse)
async def chat(message: MessageRequest):
    # TODO Update method. Application content type is JSON.
    message, session_id = message.message, message.session_id
    save_message(session_id, "human", message)
    response = chain_with_history.invoke(
        {"input": message},
        config={"configurable": {"session_id": session_id}}
    )
    if response[:3] == "AI:":  # LLM sometimes adds this.
        response = response[3:]
    save_message(session_id, "ai", response)

    # update transcript
    # update_transcript(session_id, message)
    # update_transcript(session_id, response, role="AI Assisstant:")

    return {
        "response": response
    }


@router.get("/chathistory")
async def chat_history(session_id: str):
    return {"chat_history": chain_with_history.get_session_history(session_id)}


@router.delete("/deltechathisory/{session_id}")
async def delete_chat_history(session_id: str):
    message = delete_session_history(session_id)
    return {"message": message}


@router.get("/transcript")
async def transcript(session_id: str):
    return {"transcript": generate_transcript(session_id)}


@router.delete("/deltetranscript")
async def delete_transcript():
    # transcript_memory.clear()
    return {"message": "WIP! Nothing cleared"}

app.include_router(router, prefix=prefix)
