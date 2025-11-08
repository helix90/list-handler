from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List as TypingList
from app.database import get_db
from app.models.user import User
from app.models.list import List, ListItem
from app.schemas.list import ListItemCreate, ListItemUpdate, ListItemResponse
from app.auth import get_current_user

router = APIRouter(prefix="/users/{user_id}/lists/{list_id}/items", tags=["list-items"])


def verify_list_access(current_user: User, user_id: int, list_id: int, db: Session):
    """Verify that the current user can access the requested list"""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this resource"
        )
    
    db_list = db.query(List).filter(
        List.id == list_id,
        List.user_id == user_id
    ).first()
    
    if not db_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    return db_list


@router.get("", response_model=TypingList[ListItemResponse])
async def get_list_items(
    user_id: int,
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all items in a list"""
    verify_list_access(current_user, user_id, list_id, db)
    
    items = db.query(ListItem).filter(ListItem.list_id == list_id).all()
    return items


@router.post("", response_model=ListItemResponse, status_code=status.HTTP_201_CREATED)
async def create_list_item(
    user_id: int,
    list_id: int,
    item_data: ListItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to list"""
    verify_list_access(current_user, user_id, list_id, db)
    
    db_item = ListItem(
        list_id=list_id,
        content=item_data.content,
        is_completed=item_data.is_completed
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.put("/{item_id}", response_model=ListItemResponse)
async def update_list_item(
    user_id: int,
    list_id: int,
    item_id: int,
    item_data: ListItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an item"""
    verify_list_access(current_user, user_id, list_id, db)
    
    db_item = db.query(ListItem).filter(
        ListItem.id == item_id,
        ListItem.list_id == list_id
    ).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Update fields if provided
    if item_data.content is not None:
        db_item.content = item_data.content
    if item_data.is_completed is not None:
        db_item.is_completed = item_data.is_completed
    
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list_item(
    user_id: int,
    list_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove an item"""
    verify_list_access(current_user, user_id, list_id, db)
    
    db_item = db.query(ListItem).filter(
        ListItem.id == item_id,
        ListItem.list_id == list_id
    ).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    db.delete(db_item)
    db.commit()
    
    return None


@router.patch("/{item_id}", response_model=ListItemResponse)
async def toggle_item_completion(
    user_id: int,
    list_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle completion status of an item"""
    verify_list_access(current_user, user_id, list_id, db)
    
    db_item = db.query(ListItem).filter(
        ListItem.id == item_id,
        ListItem.list_id == list_id
    ).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Toggle completion status (0 -> 1, 1 -> 0)
    db_item.is_completed = 1 if db_item.is_completed == 0 else 0
    
    db.commit()
    db.refresh(db_item)
    
    return db_item

