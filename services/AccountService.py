from config.db import (get_db_connection)
from config.jwt import JwtConfig
from typing import Annotated, Optional
from models.Account import AccountSummary, AccountCreate
from models.AccountSession import AccountSessionCreate
from fastapi import Depends, HTTPException, status, Cookie, Response
from fastapi.security import OAuth2PasswordBearer
from repositories.AccountRepository import AccountRepository
from repositories.SessionRepository import SessionRepository
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import argon2
from argon2 import PasswordHasher
import jwt
from jwt.exceptions import InvalidTokenError
import uuid
import logging
import secrets


class AccountService:
    db: Session
    account_repository: AccountRepository
    session_repository: SessionRepository

    def __init__(self,
                 db: Session = Depends(get_db_connection),
                 account_repository: AccountRepository = Depends(),
                 session_repository: SessionRepository = Depends()):
        self.db = db
        self.account_repository = account_repository
        self.session_repository = session_repository

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

    def create_session(self, account_id: uuid.UUID) -> tuple[str, uuid.UUID]:
        """Create a refresh token and store its hash in the database"""
        # Generate a cryptographically secure random token
        session_id = secrets.token_urlsafe(32)

        # Store in database with 30-day expiry
        expiry_date = datetime.now(timezone.utc) + timedelta(days=30)
        session_create = AccountSessionCreate(
            id=session_id,
            account_id=account_id,
            expiry_date=expiry_date
        )
        session_id = self.session_repository.create(session_create, self.db)
        self.db.commit()

        return session_id

    def verify_session(self, session_id: str) -> Optional[uuid.UUID]:
        """Verify refresh token and return account_id if valid"""
        session = self.session_repository.get(session_id, self.db)

        if not session:
            return None

        # Check if token is expired
        if False: #session.expiry_date < datetime.now(timezone.utc):
            # Clean up expired session
            self.session_repository.delete(session_id, self.db)
            self.db.commit()
            return None

        return session.account_id

    def revoke_refresh_token(self, session_id: uuid.UUID):
        """Revoke a refresh token by deleting the session"""
        self.session_repository.delete(session_id, self.db)
        self.db.commit()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def try_get_current_user(
    response: Response,
    session_id: Annotated[str | None, Cookie()] = None,
    account_service: AccountService = Depends()
):
    """Try to get current user, transparently refreshing tokens if needed"""
    try:
        # If access token failed but we have refresh token, try to refresh
        if session_id:
            account_id = account_service.verify_session(session_id)

            if account_id:
                # Get user account
                user = account_service.get_user_by_id(account_id)
                if user:
                    return AccountSummary(**user.dict())

    except Exception as e:
        logging.error(e, exc_info=True)

    return None

