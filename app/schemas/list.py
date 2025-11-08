from datetime import datetime
from typing import Optional, List as TypingList
from pydantic import BaseModel, Field, ConfigDict


class ListItemBase(BaseModel):
    content: str = Field(..., description="Content/text of the list item")
    is_completed: int = Field(default=0, description="Completion status: 0 = not completed, 1 = completed")


class ListItemCreate(ListItemBase):
    pass


class ListItemUpdate(BaseModel):
    content: Optional[str] = Field(None, description="Content/text of the list item")
    is_completed: Optional[int] = Field(None, description="Completion status: 0 = not completed, 1 = completed")


class ListItemResponse(ListItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Item ID")
    list_id: int = Field(..., description="ID of the list this item belongs to")
    created_at: datetime = Field(..., description="Timestamp when the item was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the item was last updated")


class ListBase(BaseModel):
    name: str = Field(..., description="Name of the list")
    description: Optional[str] = Field(None, description="Optional description of the list")


class ListCreate(ListBase):
    pass


class ListUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the list")
    description: Optional[str] = Field(None, description="Description of the list")


class ListResponse(ListBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="List ID")
    user_id: int = Field(..., description="ID of the user who owns this list")
    created_at: datetime = Field(..., description="Timestamp when the list was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the list was last updated")


class ListWithItemsResponse(ListResponse):
    model_config = ConfigDict(from_attributes=True)
    
    items: TypingList[ListItemResponse] = Field(default_factory=list, description="Array of items in the list")

