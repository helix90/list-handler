from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List as TypingList
from app.database import get_db
from app.models.user import User
from app.models.list import List, ListItem
from app.schemas.list import (
    ListCreate,
    ListUpdate,
    ListResponse,
    ListWithItemsResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/users/{user_id}/lists", tags=["lists"])


def verify_user_access(current_user: User, user_id: int):
    """Verify that the current user can access the requested user's resources"""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this resource"
        )


@router.get("", response_model=TypingList[ListResponse])
async def get_user_lists(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all lists for a user"""
    verify_user_access(current_user, user_id)
    
    lists = db.query(List).filter(List.user_id == user_id).all()
    return lists


@router.post("", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    user_id: int,
    list_data: ListCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new list for a user"""
    verify_user_access(current_user, user_id)
    
    db_list = List(
        user_id=user_id,
        name=list_data.name,
        description=list_data.description
    )
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    
    return db_list


@router.get("/{list_id}", response_model=ListWithItemsResponse)
async def get_list(
    user_id: int,
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific list with items"""
    verify_user_access(current_user, user_id)
    
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


@router.put("/{list_id}", response_model=ListResponse)
async def update_list(
    user_id: int,
    list_id: int,
    list_data: ListUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a list (rename, description, etc)"""
    verify_user_access(current_user, user_id)
    
    db_list = db.query(List).filter(
        List.id == list_id,
        List.user_id == user_id
    ).first()
    
    if not db_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Update fields if provided
    if list_data.name is not None:
        db_list.name = list_data.name
    if list_data.description is not None:
        db_list.description = list_data.description
    
    db.commit()
    db.refresh(db_list)
    
    return db_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    user_id: int,
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a list"""
    verify_user_access(current_user, user_id)
    
    db_list = db.query(List).filter(
        List.id == list_id,
        List.user_id == user_id
    ).first()
    
    if not db_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    db.delete(db_list)
    db.commit()
    
    return None

