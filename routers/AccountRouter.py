from typing import Annotated
from config.jwt import JwtConfig
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, UploadFile, status, Response, HTTPException, Cookie, Request
from fastapi.responses import RedirectResponse
from models.Token import Token
from services.AccountService import AccountService
from datetime import timedelta
from models.requests.RegisterRequest import RegisterRequest
from pydantic import ValidationError
from starlette.status import HTTP_303_SEE_OTHER

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

AccountRouter = APIRouter(prefix="/v1/account", tags=["auth"])


@AccountRouter.post("/login", status_code=status.HTTP_200_OK)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    account_service: AccountService = Depends(),
) -> Token:
    user = account_service.login(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=JwtConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = account_service.create_access_token(
        data={"sub": user.email_address}, expires_delta=access_token_expires
    )
    redirect = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=JwtConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return redirect


@AccountRouter.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@AccountRouter.post("/token", status_code=status.HTTP_200_OK)
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    account_service: AccountService = Depends(),
) -> Token:
    user = account_service.login(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=JwtConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = account_service.create_access_token(
        data={"sub": user.email_address}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@AccountRouter.post("/register", status_code=status.HTTP_201_CREATED)
async def register_account(request: RegisterRequest,
                           account_service: AccountService = Depends()):
    try:
        account_service.create_account(
            request.account_name, request.email_address, request.password)
    except ValidationError as ex:
        raise HTTPException(
            status_code=422,
            detail=ex.errors(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
