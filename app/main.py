from fastapi import FastAPI
from app.routes.chat import router as chat_router
from app.config.database import check_database_connection

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    db_status = await check_database_connection()
    print(f"Database Status: {db_status['message']}")

app.include_router(chat_router)