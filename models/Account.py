from pydantic import EmailStr
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class AccountBase(SQLModel):
    id: uuid.UUID
    account_name: str
    email_address: EmailStr
    is_active: bool
    date_created: datetime
    date_updated: Optional[datetime]


class Account(AccountBase, table=True):
    __tablename__ = "account"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    account_name: str = Field(index=True, nullable=False)
    email_address: EmailStr = Field(index=True, nullable=False)
    hashed_password: str
    is_active: bool = Field(default=True)
    date_created: datetime = Field(default_factory=datetime.utcnow)
    date_updated: Optional[datetime]


class AccountSummary(AccountBase):
    pass


class AccountCreate(SQLModel):
    account_name: str
    email_address: EmailStr
    hashed_password: str
    is_active: bool = True
    date_created: datetime = datetime.utcnow()
    date_updated: Optional[datetime] = None
