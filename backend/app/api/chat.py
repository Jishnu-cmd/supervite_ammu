from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Invoice, ExceptionRecord, PurchaseOrder, ChatSession, ChatMessage
from app.schemas.schemas import ChatMessageRequest, ChatMessageResponse
from app.services.explanation_service import ExplanationService

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/invoice/{invoice_id}", response_model=ChatMessageResponse)
def chat_with_assistant(
    invoice_id: str, 
    req: ChatMessageRequest, 
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == invoice.po_number).first()
    exceptions = db.query(ExceptionRecord).filter(ExceptionRecord.invoice_id == invoice_id).all()

    # Find or create Chat Session
    session = db.query(ChatSession).filter(ChatSession.invoice_id == invoice_id).first()
    if not session:
        session = ChatSession(invoice_id=invoice_id)
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save User Message
    user_msg = ChatMessage(
        session_id=session.id,
        sender="USER",
        message=req.message
    )
    db.add(user_msg)
    db.commit()

    # Generate Grounded Explanation Response
    answer, sources = ExplanationService.generate_explanation(
        invoice=invoice,
        exceptions=exceptions,
        po=po,
        user_message=req.message
    )

    # Save Assistant Response
    asst_msg = ChatMessage(
        session_id=session.id,
        sender="ASSISTANT",
        message=answer,
        sources=sources
    )
    db.add(asst_msg)
    db.commit()
    db.refresh(asst_msg)

    return asst_msg

@router.get("/invoice/{invoice_id}/history", response_model=List[ChatMessageResponse])
def get_chat_history(invoice_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.invoice_id == invoice_id).first()
    if not session:
        return []
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.timestamp.asc()).all()
    return messages
