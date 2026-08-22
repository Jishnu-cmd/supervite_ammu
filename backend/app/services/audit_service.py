from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import AuditLog, ReviewAction

class AuditService:
    @classmethod
    def log_event(
        cls, 
        db: Session, 
        entity_type: str, 
        entity_id: str, 
        action: str, 
        user_id: str = "SYSTEM", 
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            details=details or {}
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @classmethod
    def log_review_action(
        cls,
        db: Session,
        invoice_id: str,
        action_type: str,
        user_name: str,
        reason: str,
        user_id: str = "USER_1",
        exception_id: Optional[str] = None
    ) -> ReviewAction:
        action = ReviewAction(
            invoice_id=invoice_id,
            exception_id=exception_id,
            action_type=action_type,
            user_id=user_id,
            user_name=user_name,
            reason=reason
        )
        db.add(action)
        
        # Also log to main audit log
        cls.log_event(
            db=db,
            entity_type="INVOICE",
            entity_id=invoice_id,
            action=action_type,
            user_id=user_id,
            details={"user_name": user_name, "reason": reason, "exception_id": exception_id}
        )

        db.commit()
        db.refresh(action)
        return action
