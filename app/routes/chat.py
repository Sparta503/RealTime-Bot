from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.chat_service import ChatService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    ai_response: str
    model_used: str
    tokens_used: int

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        # Auto-generate session and user if not provided
        response = await ChatService.chat_with_ai(
            session_id=None,  # Will create new session
            user_message=req.message,
            user_id=None  # Will create anonymous user
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        history = await ChatService.get_chat_history(session_id)
        return {"session_id": session_id, "messages": history}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/session")
async def create_session(user_id: str = None):
    try:
        session = await ChatService.create_session(user_id)
        return {"session_id": session.session_id, "created_at": session.created_at}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))