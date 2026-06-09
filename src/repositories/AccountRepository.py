from typing import Optional
from models.Account import Account, AccountCreate
from sqlalchemy.orm import Session
import uuid


class AccountRepository:

    def get(self, id: int, db: Session) -> Optional[Account]:
        query = db.query(Account)
        account = query.where(Account.id == id).first()
        return account

    def get_by_email_address(self, email_address: str, db: Session) -> Optional[Account]:
        query = db.query(Account)
        account = query.where(Account.email_address == email_address).first()
        return account

    def create(self, account_create: AccountCreate, db: Session) -> uuid.UUID:
        account_data = Account(
            **{k: v for k, v in account_create.dict().items()})
        db.add(account_data)
        db.flush()
        db.refresh(account_data)
        return account_data.id
