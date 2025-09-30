from sqlalchemy.orm import Session
from models.AccountSession import AccountSession, AccountSessionCreate
import uuid


class SessionRepository:
    def create(self, session: AccountSessionCreate, db: Session) -> uuid.UUID:
        db_session = AccountSession(**session.dict())
        db.add(db_session)
        db.flush()
        return db_session.id

    def get(self, session_id: uuid.UUID, db: Session) -> AccountSession:
        return db.query(AccountSession).filter(AccountSession.id == session_id).first()

    def delete(self, session_id: uuid.UUID, db: Session):
        db.query(AccountSession).filter(AccountSession.id == session_id).delete()
        db.flush()

    def delete_by_account(self, account_id: uuid.UUID, db: Session):
        """Delete all sessions for an account (useful for logout all devices)"""
        db.query(AccountSession).filter(AccountSession.account_id == account_id).delete()
        db.flush()

    def cleanup_expired(self, db: Session):
        """Clean up expired sessions"""
        from datetime import datetime, timezone
        db.query(AccountSession).filter(AccountSession.expiry_date < datetime.now(timezone.utc)).delete()
        db.flush()
