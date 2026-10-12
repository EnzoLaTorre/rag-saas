import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.ratelimit import RateLimiter
from ..database import engine, get_session
from ..models import ChatMessage, User
from ..services import rag

router = APIRouter(prefix="/chat", tags=["chat"])
query_limiter = RateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)


class QueryRequest(BaseModel):
    question: str
    document_id: int | None = None


@router.post("/query")
def chat_query(
    req: QueryRequest,
    user: User = Depends(get_current_user),
):
    if not query_limiter.allow(f"chat:{user.id}"):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Demasiadas consultas, espera un momento"
        )

    tenant_id = user.tenant_id
    user_id = user.id

    def event_stream():
        full = ""
        sources = []
        failed = False
        with Session(engine) as session:
            try:
                for event in rag.answer_stream(session, tenant_id, req.question, req.document_id):
                    data = json.loads(event)
                    if data["type"] == "sources":
                        sources = data["sources"]
                    elif data["type"] == "token":
                        full += data["content"]
                    yield f"data: {event}\n\n"
            except Exception as exc:
                failed = True
                error = json.dumps({"type": "error", "message": str(exc)}, ensure_ascii=False)
                yield f"data: {error}\n\n"

            if not failed:
                session.add(
                    ChatMessage(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        question=req.question,
                        answer=full,
                        sources_json=json.dumps(sources, ensure_ascii=False),
                    )
                )
                session.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history")
def history(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    msgs = session.exec(
        select(ChatMessage)
        .where(ChatMessage.tenant_id == user.tenant_id)
        .order_by(ChatMessage.id.desc())
        .limit(20)
    ).all()
    return msgs
