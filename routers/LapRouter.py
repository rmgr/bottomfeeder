from typing import List, Annotated
from fastapi import APIRouter, Depends
from services.LapService import LapService
from services.AccountService import (get_current_user)
from models.Account import AccountSummary


LapRouter = APIRouter(prefix="/v1/laps", tags = ["lap"])

@LapRouter.get("/{id}")
def index(id: int, 
          current_user: Annotated[AccountSummary, Depends(get_current_user)],
          lapService: LapService = Depends()):
    return lapService.list_laps_for_activity(id, current_user.id)

