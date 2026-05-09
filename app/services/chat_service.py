from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.config.database import db
from app.models.chat import Message, ChatSession, User, APIUsage
from app.services.groq_service import ask_groq
import uuid

class ChatService:
    @staticmethod
    async def create_session(user_id: Optional[str] = None) -> ChatSession:
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "message_count": 0,
            "is_active": True
        }
        result = await db.sessions.insert_one(session_data)
        session_data["id"] = str(result.inserted_id)
        return ChatSession(**session_data)

    @staticmethod
    async def save_message(session_id: str, content: str, role: str, model_used: Optional[str] = None, tokens_used: Optional[int] = None) -> Message:
        session = await db.sessions.find_one({"session_id": session_id})
        if not session:
            raise ValueError("Session not found")

        message_data = {
            "session_id": str(session["_id"]),
            "content": content,
            "role": role,
            "timestamp": datetime.utcnow(),
            "model_used": model_used,
            "tokens_used": tokens_used
        }
        
        result = await db.messages.insert_one(message_data)
        message_data["id"] = str(result.inserted_id)
        
        # Update session activity
        await db.sessions.update_one(
            {"_id": session["_id"]},
            {
                "$set": {"last_activity": datetime.utcnow()},
                "$inc": {"message_count": 1}
            }
        )
        
        return Message(**message_data)

    @staticmethod
    async def get_session_messages(session_id: str) -> List[Message]:
        session = await db.sessions.find_one({"session_id": session_id})
        if not session:
            raise ValueError("Session not found")

        messages_cursor = db.messages.find({"session_id": str(session["_id"])}).sort("timestamp", 1)
        messages = []
        async for message in messages_cursor:
            # Convert ObjectId to string for id field
            if "_id" in message:
                message["id"] = str(message["_id"])
            messages.append(Message(**message))
        return messages

    @staticmethod
    async def chat_with_ai(session_id: Optional[str] = None, user_message: str = "", user_id: Optional[str] = None) -> dict:
        # Create or get session
        if not session_id:
            # Generate anonymous user ID if not provided
            if not user_id:
                user_id = f"anonymous_{str(uuid.uuid4())[:8]}"
            session = await ChatService.create_session(user_id)
            session_id = session.session_id
        else:
            session = await db.sessions.find_one({"session_id": session_id})
            if not session:
                raise ValueError("Session not found")

        # Save user message
        await ChatService.save_message(session_id, user_message, "user")

        # Check if it's a greeting - handle locally to save tokens
        greetings = ["hi", "hello", "hey", "hey there", "hi", "good morning", "good afternoon", "good evening", "yo"]
        lower_message = user_message.lower().strip()
        
        if lower_message in greetings or lower_message.startswith(tuple(greetings)):
            # Handle greeting locally without API call
            response_content = "Hello! How can I help you today?"
            model_used = "local_greeting"
            tokens_used = 0
        else:
            # Get AI response with conversational prompt
            conversational_prompt = f"""You are a helpful AI assistant. Analyze the user's question and respond appropriately:

User message: {user_message}

If the topic is simple and specific (like "What is gravity?", "Who is Einstein?", "What is 2+2?"), provide a direct, concise explanation without asking questions.

If the topic is broad or complex (like "What is physics?", "Tell me about history", "Explain economics"), provide:
1. Two-line summary explaining what the topic is
2. Then ask specific questions about what aspect interests them

Examples:
Simple topic "What is gravity?":
"Gravity is a fundamental force that attracts objects toward each other. It's what keeps you on Earth and planets in orbit."

Broad topic "What is physics?":
"Physics is the scientific study of matter, energy, and their interactions. It explains how the universe works from tiny particles to vast galaxies.

What specific area interests you - mechanics, thermodynamics, quantum physics, or something else?"""
            
            ai_response = ask_groq(conversational_prompt)
        
        # Extract response content and metadata
        # For greetings, response_content and tokens_used are already set above
        if lower_message in greetings or lower_message.startswith(tuple(greetings)):
            # Already set for greetings
            pass
        else:
            # For AI responses
            response_content = ""
            tokens_used = 0
            model_used = "llama-3.3-70b-versatile"
            
            if "choices" in ai_response and len(ai_response["choices"]) > 0:
                response_content = ai_response["choices"][0]["message"]["content"]
                if "usage" in ai_response:
                    tokens_used = ai_response["usage"]["total_tokens"]
            else:
                response_content = str(ai_response)

        # Save AI response
        await ChatService.save_message(session_id, response_content, "assistant", model_used, tokens_used)

        # Log API usage
        usage_data = {
            "user_id": user_id,
            "session_id": session_id,
            "api_provider": "groq",
            "model": model_used,
            "tokens_used": tokens_used,
            "timestamp": datetime.utcnow()
        }
        await db.usage.insert_one(usage_data)

        return {
            "session_id": session_id,
            "user_message": user_message,
            "ai_response": response_content,
            "model_used": model_used,
            "tokens_used": tokens_used
        }

    @staticmethod
    async def get_chat_history(session_id: str) -> List[dict]:
        messages = await ChatService.get_session_messages(session_id)
        return [
            {
                "content": msg.content,
                "role": msg.role,
                "timestamp": msg.timestamp,
                "model_used": msg.model_used,
                "tokens_used": msg.tokens_used
            }
            for msg in messages
        ]
