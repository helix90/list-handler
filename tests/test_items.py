import pytest
from fastapi import status


class TestGetListItems:
    """Tests for GET /users/{userId}/lists/{listId}/items"""
    
    def test_get_items_success(self, client, auth_headers, test_user, test_list, test_list_item):
        """Test getting all items in a list"""
        response = client.get(
            f"/users/me/lists/{test_list.id}/items",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(item["id"] == test_list_item.id for item in data)
    
    def test_get_items_empty_list(self, client, auth_headers, test_user, test_list):
        """Test getting items from an empty list"""
        response = client.get(
            f"/users/me/lists/{test_list.id}/items",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_items_unauthorized(self, client, test_user, test_list):
        """Test getting items without authentication"""
        response = client.get(
            f"/users/me/lists/{test_list.id}/items"
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_items_wrong_user(self, client, auth_headers, test_user, test_user2, db_session):
        """Test getting items from another user's list"""
        from app.models.list import List
        
        other_list = List(
            user_id=test_user2.id,
            name="Other User's List"
        )
        db_session.add(other_list)
        db_session.commit()
        db_session.refresh(other_list)
        
        response = client.get(
            f"/users/{test_user.id}/lists/{other_list.id}/items",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateListItem:
    """Tests for POST /users/{userId}/lists/{listId}/items"""
    
    def test_create_item_success(self, client, auth_headers, test_user, test_list):
        """Test adding an item to a list"""
        response = client.post(
            f"/users/me/lists/{test_list.id}/items",
            headers=auth_headers,
            json={
                "content": "New Item",
                "is_completed": 0
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "New Item"
        assert data["is_completed"] == 0
        assert data["list_id"] == test_list.id
    
    def test_create_item_default_completed(self, client, auth_headers, test_user, test_list):
        """Test creating item with default is_completed"""
        response = client.post(
            f"/users/me/lists/{test_list.id}/items",
            headers=auth_headers,
            json={"content": "Item without completion"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_completed"] == 0
    
    def test_create_item_unauthorized(self, client, test_user, test_list):
        """Test creating item without authentication"""
        response = client.post(
            f"/users/me/lists/{test_list.id}/items",
            json={"content": "New Item"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateListItem:
    """Tests for PUT /users/{userId}/lists/{listId}/items/{itemId}"""
    
    def test_update_item_success(self, client, auth_headers, test_user, test_list, test_list_item):
        """Test updating an item"""
        response = client.put(
            f"/users/me/lists/{test_list.id}/items/{test_list_item.id}",
            headers=auth_headers,
            json={
                "content": "Updated Item Content",
                "is_completed": 1
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Updated Item Content"
        assert data["is_completed"] == 1
    
    def test_update_item_partial(self, client, auth_headers, test_user, test_list, test_list_item):
        """Test updating only content"""
        response = client.put(
            f"/users/me/lists/{test_list.id}/items/{test_list_item.id}",
            headers=auth_headers,
            json={"content": "Only Content Updated"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Only Content Updated"
        # is_completed should remain unchanged
        assert data["is_completed"] == test_list_item.is_completed
    
    def test_update_item_not_found(self, client, auth_headers, test_user, test_list):
        """Test updating a nonexistent item"""
        response = client.put(
            f"/users/me/lists/{test_list.id}/items/99999",
            headers=auth_headers,
            json={"content": "Updated Content"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_item_wrong_list(self, client, auth_headers, test_user, db_session):
        """Test updating item from wrong list"""
        from app.models.list import List, ListItem
        
        list1 = List(user_id=test_user.id, name="List 1")
        list2 = List(user_id=test_user.id, name="List 2")
        db_session.add_all([list1, list2])
        db_session.commit()
        db_session.refresh(list1)
        db_session.refresh(list2)
        
        item = ListItem(list_id=list1.id, content="Item in List 1")
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        response = client.put(
            f"/users/me/lists/{list2.id}/items/{item.id}",
            headers=auth_headers,
            json={"content": "Updated"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteListItem:
    """Tests for DELETE /users/{userId}/lists/{listId}/items/{itemId}"""
    
    def test_delete_item_success(self, client, auth_headers, test_user, test_list, db_session):
        """Test deleting an item"""
        from app.models.list import ListItem
        
        item_to_delete = ListItem(
            list_id=test_list.id,
            content="Item to Delete"
        )
        db_session.add(item_to_delete)
        db_session.commit()
        db_session.refresh(item_to_delete)
        
        response = client.delete(
            f"/users/me/lists/{test_list.id}/items/{item_to_delete.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify item is deleted
        response = client.get(
            f"/users/me/lists/{test_list.id}/items",
            headers=auth_headers
        )
        items = response.json()
        assert not any(item["id"] == item_to_delete.id for item in items)
    
    def test_delete_item_not_found(self, client, auth_headers, test_user, test_list):
        """Test deleting a nonexistent item"""
        response = client.delete(
            f"/users/me/lists/{test_list.id}/items/99999",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestToggleItemCompletion:
    """Tests for PATCH /users/{userId}/lists/{listId}/items/{itemId}"""
    
    def test_toggle_completion_to_completed(self, client, auth_headers, test_user, test_list, test_list_item):
        """Test toggling item from incomplete to completed"""
        # Ensure item starts as incomplete
        assert test_list_item.is_completed == 0
        
        response = client.patch(
            f"/users/me/lists/{test_list.id}/items/{test_list_item.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_completed"] == 1
    
    def test_toggle_completion_to_incomplete(self, client, auth_headers, test_user, test_list, db_session):
        """Test toggling item from completed to incomplete"""
        from app.models.list import ListItem
        
        completed_item = ListItem(
            list_id=test_list.id,
            content="Completed Item",
            is_completed=1
        )
        db_session.add(completed_item)
        db_session.commit()
        db_session.refresh(completed_item)
        
        response = client.patch(
            f"/users/me/lists/{test_list.id}/items/{completed_item.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_completed"] == 0
    
    def test_toggle_completion_not_found(self, client, auth_headers, test_user, test_list):
        """Test toggling completion for nonexistent item"""
        response = client.patch(
            f"/users/me/lists/{test_list.id}/items/99999",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_toggle_completion_multiple_times(self, client, auth_headers, test_user, test_list, test_list_item):
        """Test toggling completion multiple times"""
        # Toggle to completed
        response1 = client.patch(
            f"/users/me/lists/{test_list.id}/items/{test_list_item.id}",
            headers=auth_headers
        )
        assert response1.json()["is_completed"] == 1
        
        # Toggle back to incomplete
        response2 = client.patch(
            f"/users/me/lists/{test_list.id}/items/{test_list_item.id}",
            headers=auth_headers
        )
        assert response2.json()["is_completed"] == 0
        
        # Toggle to completed again
        response3 = client.patch(
            f"/users/me/lists/{test_list.id}/items/{test_list_item.id}",
            headers=auth_headers
        )
        assert response3.json()["is_completed"] == 1

