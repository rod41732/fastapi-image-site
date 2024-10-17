from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Simple message response"""

    message: str


class ErrorDetail(BaseModel):
    """pydantic error model (assume string)"""

    detail: str
