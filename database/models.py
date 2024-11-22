from pydantic import BaseModel, Field
from datetime import datetime

class RB(BaseModel):
    panid: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    dob: str = Field(..., min_length=1)
    is_completed: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    creation: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

    class Config:
        schema_extra = {
            "example": {
                "panid": "Sample ID",
                "name": "name",
                "dob": "dob",
                "is_completed": False,
            }
        }