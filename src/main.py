from fastapi import FastAPI, APIRouter
from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory

from models.models import HumanResponse, AIResponse


# AI Prompt Template and Chain
llm = Ollama(model="llama2")
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a chatbot assistant. Keep your responses concise and relevant. Do not start responses with either "
     "'Assisstant:' or 'Bot:' or 'AI:'."),
    MessagesPlaceholder(variable_name="chat_history")
])
output_parser = StrOutputParser()
chat_history_memory = ChatMessageHistory()
chain = prompt | llm | output_parser

# Transcript
processed_chat_history = []
transcript_memory = []

# Fast API
app = FastAPI()
router = APIRouter()
prefix = "/api/v1"


def update_chat_history(text, human=True):
    if human:
        chat_history_memory.add_user_message(text)
    else:
        chat_history_memory.add_ai_message(text)


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


def update_transcript(text, human=True):
    if human:
        transcript_memory.append(f"Human: {text}")
    else:
        transcript_memory.append(f"AI Assisstant: {text}")


@router.get("/")
async def home():
    return {"message": "Voice Chatbot with LLM"}


@router.post("/chat", response_model=AIResponse)
async def chat(message: HumanResponse):
    # update chat history
    update_chat_history(message.response)
    response = chain.invoke({"chat_history": chat_history_memory.messages})
    if response[:3] == "AI:":  # AI seems to fail to respect the prompt template. Not sure why.
        response = response[3:]
    update_chat_history(response, human=False)
    process_chat_history(message.response, response)

    # update transcript
    update_transcript(message.response)
    update_transcript(response, human=False)

    print(type(chat_history_memory))

    return {"name": "ai_response",
            "response": response,
            "chat_history": processed_chat_history}


@router.get("/chathistory")
async def chat_history():
    return {"chat_history": chat_history_memory}


@router.post("/deltechathisory")
async def delete_chat_history():
    chat_history_memory.clear()
    return {"message": "Chat History Cleared"}


@router.get("/transcript")
async def transcript():
    return {"transcript": transcript_memory}


@router.post("/deltetranscript")
async def delete_transcript():
    transcript_memory.clear()
    return {"message": "Transcript Cleared"}


app.include_router(router, prefix=prefix)
