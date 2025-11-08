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


@router.get(
    "",
    response_model=TypingList[ListResponse],
    summary="Get all lists for a user",
    responses={
        200: {"description": "List of user's lists"},
        401: {"description": "Missing or invalid authentication token"},
        403: {"description": "User cannot access another user's lists"}
    }
)
async def get_user_lists(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all lists belonging to the specified user.
    
    - **user_id**: ID of the user whose lists to retrieve
    - Returns an array of lists (without items)
    """
    verify_user_access(current_user, user_id)
    
    lists = db.query(List).filter(List.user_id == user_id).all()
    return lists


@router.post(
    "",
    response_model=ListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new list",
    responses={
        201: {"description": "List successfully created"},
        401: {"description": "Missing or invalid authentication token"},
        403: {"description": "User cannot create lists for another user"}
    }
)
async def create_list(
    user_id: int,
    list_data: ListCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new list for the specified user.
    
    - **user_id**: ID of the user who will own the list
    - **name**: Name of the list (required)
    - **description**: Optional description of the list
    """
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


@router.get(
    "/{list_id}",
    response_model=ListWithItemsResponse,
    summary="Get a specific list with items",
    responses={
        200: {"description": "List with all its items"},
        401: {"description": "Missing or invalid authentication token"},
        403: {"description": "User cannot access another user's lists"},
        404: {"description": "List not found or doesn't belong to user"}
    }
)
async def get_list(
    user_id: int,
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific list with all its items.
    
    - **user_id**: ID of the user who owns the list
    - **list_id**: ID of the list to retrieve
    - Returns the list object with an array of all items
    """
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


@router.put(
    "/{list_id}",
    response_model=ListResponse,
    summary="Update a list",
    responses={
        200: {"description": "List successfully updated"},
        401: {"description": "Missing or invalid authentication token"},
        403: {"description": "User cannot update another user's lists"},
        404: {"description": "List not found"}
    }
)
async def update_list(
    user_id: int,
    list_id: int,
    list_data: ListUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a list's name and/or description.
    
    - **user_id**: ID of the user who owns the list
    - **list_id**: ID of the list to update
    - **name**: New name for the list (optional)
    - **description**: New description for the list (optional)
    - Only provided fields will be updated
    """
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


@router.delete(
    "/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a list",
    responses={
        204: {"description": "List successfully deleted"},
        401: {"description": "Missing or invalid authentication token"},
        403: {"description": "User cannot delete another user's lists"},
        404: {"description": "List not found"}
    }
)
async def delete_list(
    user_id: int,
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a list and all its items.
    
    - **user_id**: ID of the user who owns the list
    - **list_id**: ID of the list to delete
    - **Warning**: This will also delete all items in the list (cascade delete)
    """
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

