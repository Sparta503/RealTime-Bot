from fastapi import APIRouter
from pydantic import BaseModel
from app.services.groq_service import ask_groq

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):

    response = ask_groq(req.message)

    return response