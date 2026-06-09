from pydantic import BaseModel

class RegisterRequest(BaseModel):
    email_address: str
    account_name: str
    password: str
