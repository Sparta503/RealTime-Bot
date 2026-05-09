from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, Field
from bson import ObjectId

PyObjectId = Annotated[str, Field(alias="_id")]

class Message(BaseModel):
    id: Optional[PyObjectId] = None
    session_id: str
    content: str
    role: str  # "user" or "assistant"
    timestamp: datetime
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None

class ChatSession(BaseModel):
    id: Optional[PyObjectId] = None
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    message_count: int = 0
    is_active: bool = True

class User(BaseModel):
    id: Optional[PyObjectId] = None
    username: str
    email: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    total_messages: int = 0
    is_active: bool = True

class APIUsage(BaseModel):
    id: Optional[PyObjectId] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    api_provider: str  # "groq", "openai", etc.
    model: str
    tokens_used: int
    cost: Optional[float] = None
    timestamp: datetime
