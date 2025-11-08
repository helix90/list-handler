from datetime import datetime
from typing import Optional, List as TypingList
from pydantic import BaseModel


class ListItemBase(BaseModel):
    content: str
    is_completed: int = 0


class ListItemCreate(ListItemBase):
    pass


class ListItemUpdate(BaseModel):
    content: Optional[str] = None
    is_completed: Optional[int] = None


class ListItemResponse(ListItemBase):
    id: int
    list_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ListBase(BaseModel):
    name: str
    description: Optional[str] = None


class ListCreate(ListBase):
    pass


class ListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ListResponse(ListBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ListWithItemsResponse(ListResponse):
    items: TypingList[ListItemResponse] = []

    class Config:
        from_attributes = True

