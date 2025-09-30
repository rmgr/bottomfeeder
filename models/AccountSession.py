from pydantic import EmailStr,field_validator
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class AccountSessionBase(SQLModel):
    account_id: str
    expiry_date: datetime


class AccountSession(AccountSessionBase, table=True):
    __tablename__ = "session"
    id: str = Field(primary_key=True)
    account_id: uuid.UUID = Field(nullable=False, foreign_key="account.id")
    expiry_date: datetime = Field(nullable=False)


class AccountSessionCreate(SQLModel):
    id: str
    account_id: uuid.UUID
    expiry_date: datetime
