from langchain_core.chat_history import BaseChatMessageHistory
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, Text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from langchain.memory import ChatMessageHistory

# Define the SQLite database
DATABASE_URL = "sqlite:///chat_history.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Define the Session model
class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, nullable=False)
    messages = relationship("Message", back_populates="session")


# Define the Message model
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    session = relationship("Session", back_populates="messages")


# Create the database and the tables
Base.metadata.create_all(engine)


def save_message(session_id: str, role: str, content: str):
    db = next(get_db())
    try:
        # Check if the session already exists
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            # Create a new session if it doesn't exist
            session = Session(session_id=session_id)
            db.add(session)
            db.commit()
            db.refresh(session)

        # Add the message to the session
        db.add(Message(session_id=session.id, role=role, content=content))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()


def load_session_history(session_id: str) -> BaseChatMessageHistory:
    db = next(get_db())
    chat_history = ChatMessageHistory()
    try:
        # Retrieve the session
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            # Add each message to the chat history
            for message in session.messages:
                chat_history.add_message({"role": message.role, "content": message.content})
    except SQLAlchemyError:
        pass
    finally:
        db.close()

    return chat_history


def delete_session_history(session_id: str):
    db = next(get_db())
    try:
        # check if session exists
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            messages = db.query(Message).filter(Message.session_id == session.id).all()
            for message in messages:
                db.delete(message)
            db.delete(session)
            db.commit()
            return "Session deleted"
        else:
            return "Session not found"
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
