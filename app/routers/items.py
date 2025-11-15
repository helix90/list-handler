from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List as TypingList
from app.database import get_db
from app.models.user import User
from app.models.list import List, ListItem
from app.schemas.list import ListItemCreate, ListItemUpdate, ListItemResponse
from app.auth import get_current_user

router = APIRouter(prefix="/users/me/lists/{list_id}/items", tags=["list-items"])


def verify_list_access(current_user: User, list_id: int, db: Session):
    """Verify that the current user owns the requested list"""
    db_list = db.query(List).filter(
        List.id == list_id,
        List.user_id == current_user.id
    ).first()
    
    if not db_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    return db_list


@router.get(
    "",
    response_model=TypingList[ListItemResponse],
    summary="Get all items in a list",
    responses={
        200: {"description": "Array of list items"},
        401: {"description": "Missing or invalid authentication token"},
        404: {"description": "List not found"}
    }
)
async def get_list_items(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all items in a specific list.
    
    - **list_id**: ID of the list
    - Returns an array of all items in the list owned by current user
    """
    verify_list_access(current_user, list_id, db)
    
    items = db.query(ListItem).filter(ListItem.list_id == list_id).all()
    return items


@router.post(
    "",
    response_model=ListItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to list",
    responses={
        201: {"description": "Item successfully created"},
        401: {"description": "Missing or invalid authentication token"},
        404: {"description": "List not found"}
    }
)
async def create_list_item(
    list_id: int,
    item_data: ListItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new item to a list owned by current user.
    
    - **list_id**: ID of the list to add the item to
    - **content**: Text content of the item (required)
    - **is_completed**: Completion status, defaults to 0 (not completed)
    """
    verify_list_access(current_user, list_id, db)
    
    db_item = ListItem(
        list_id=list_id,
        content=item_data.content,
        is_completed=item_data.is_completed
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.put(
    "/{item_id}",
    response_model=ListItemResponse,
    summary="Update an item",
    responses={
        200: {"description": "Item successfully updated"},
        401: {"description": "Missing or invalid authentication token"},
        404: {"description": "Item not found"}
    }
)
async def update_list_item(
    list_id: int,
    item_id: int,
    item_data: ListItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an item's content and/or completion status.
    
    - **list_id**: ID of the list containing the item
    - **item_id**: ID of the item to update
    - **content**: New content for the item (optional)
    - **is_completed**: New completion status (optional: 0 = not completed, 1 = completed)
    - Only provided fields will be updated
    - Only updates items in lists owned by current user
    """
    verify_list_access(current_user, list_id, db)
    
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


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item",
    responses={
        204: {"description": "Item successfully deleted"},
        401: {"description": "Missing or invalid authentication token"},
        404: {"description": "Item not found"}
    }
)
async def delete_list_item(
    list_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an item from a list.
    
    - **list_id**: ID of the list containing the item
    - **item_id**: ID of the item to delete
    - Only deletes items from lists owned by current user
    """
    verify_list_access(current_user, list_id, db)
    
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


@router.patch(
    "/{item_id}",
    response_model=ListItemResponse,
    summary="Toggle item completion status",
    responses={
        200: {"description": "Item completion status toggled"},
        401: {"description": "Missing or invalid authentication token"},
        404: {"description": "Item not found"}
    }
)
async def toggle_item_completion(
    list_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle the completion status of an item.
    
    - **list_id**: ID of the list containing the item
    - **item_id**: ID of the item to toggle
    - Toggles `is_completed` between 0 (incomplete) and 1 (completed)
    - No request body required
    - Only toggles items in lists owned by current user
    """
    verify_list_access(current_user, list_id, db)
    
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

