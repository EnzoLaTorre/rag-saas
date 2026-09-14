from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import auth, chat, documents
from .database import engine
from .models import SQLModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="RAG SaaS", lifespan=lifespan)
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "RAG SaaS API"}