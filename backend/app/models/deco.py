from pydantic import BaseModel
from typing import Optional


class DecoConfig(BaseModel):
    host: str
    password: Optional[str] = None
    enabled: bool = True
    interval: int = 15  # minutes


class DecoVerifyRequest(BaseModel):
    host: str
    password: Optional[str] = None
