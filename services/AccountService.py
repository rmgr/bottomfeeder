from config.db import (get_db_connection)
from config.jwt import JwtConfig
from typing import Annotated
from models.Account import AccountSummary, AccountCreate
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from repositories.AccountRepository import AccountRepository
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import argon2
from argon2 import PasswordHasher
import jwt
from jwt.exceptions import InvalidTokenError
import uuid


class AccountService:
    db: Session
    account_repository: AccountRepository

    def __init__(self,
                 db: Session = Depends(get_db_connection),
                 account_repository: AccountRepository = Depends()):
        self.db = db
        self.account_repository = account_repository

    def hash_password(self, password: str):
        ph = PasswordHasher()
        hash = ph.hash(password)
        return hash

    def check_password(self, hashed_password: str, cleartext_password: str):
        ph = PasswordHasher()
        try:
            match = ph.verify(hashed_password, cleartext_password)
        except argon2.exceptions.VerifyMismatchError:
            return False
        return match

    def create_account(self, account_name: str, email_address: str, password: str) -> uuid.UUID:
        account_create = AccountCreate(account_name=account_name,
                                       email_address=email_address,
                                       hashed_password=self.hash_password(password))
        id = self.account_repository.create(account_create, self.db)
        self.db.commit()
        return id

    def login(self, email_address: str, password: str) -> AccountSummary:
        account = self.account_repository.get_by_email_address(
            email_address, self.db)

        if not account:
            return None

        if not self.check_password(account.hashed_password, password):
            return None

        return AccountSummary(**account.dict())

    def get_user_by_id(self, id: uuid):
        account = self.account_repository.get(id, self.db)
        return account

    def get_user_by_email_address(self, email_address: str):
        account = self.account_repository.get_by_email_address(
            email_address, self.db)
        return account

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, JwtConfig.SECRET_KEY, JwtConfig.ALGORITHM)
        return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def validate_token(token: str, account_service: AccountService = Depends()):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JwtConfig.SECRET_KEY,
                             algorithms=[JwtConfig.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = username
    except InvalidTokenError:
        raise credentials_exception
    user = account_service.get_user_by_email_address(token_data)

    if user is None:
        raise credentials_exception
    return AccountSummary(**user.dict())


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    access_token: Annotated[str | None, Cookie()] = None,
    account_service: AccountService = Depends()
):
    # Try bearer token first
    if token:
        return await validate_token(token, account_service)
    # Then try cookie
    if access_token:
        return await validate_token(access_token, account_service)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
